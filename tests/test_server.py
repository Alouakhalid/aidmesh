from fastapi.testclient import TestClient

import server.app as srv

client = TestClient(srv.app)


def test_health():
    assert client.get("/api/health").json()["ok"] is True


def test_rejects_empty_and_oversized():
    assert client.post("/api/run", json={"reports": []}).status_code == 422
    big = [{"id": "R", "text": "x" * 401}]
    assert client.post("/api/run", json={"reports": big}).status_code == 422
    many = [{"id": f"R{i}", "text": "a"} for i in range(7)]
    assert client.post("/api/run", json={"reports": many}).status_code == 422


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(srv, "run_pipeline", lambda r: {"ok": True})
    srv.limiter.reset(); srv.jobs.clear()
    body = {"reports": [{"id": "R1", "text": "Flood at Manshiya"}]}
    codes = [client.post("/api/run", json=body).status_code for _ in range(srv.PER_IP_PER_HOUR + 1)]
    assert codes[:-1] == [200] * srv.PER_IP_PER_HOUR and codes[-1] == 429


def test_cors_header():
    r = client.options("/api/run", headers={"Origin": "https://alouakhalid.github.io",
                                        "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "https://alouakhalid.github.io"


def test_job_flow(monkeypatch):
    import time
    monkeypatch.setattr(srv, "run_pipeline", lambda r: {"stages": {"x": "y"}})
    srv.limiter.reset(); srv.jobs.clear()
    r = client.post("/api/run", json={"reports": [{"id": "R1", "text": "Flood at Manshiya"}]})
    jid = r.json()["job_id"]
    for _ in range(50):
        j = client.get(f"/api/job/{jid}").json()
        if j["status"] == "done":
            break
        time.sleep(0.05)
    assert j["status"] == "done" and j["result"]["stages"]["x"] == "y"
    assert client.get("/api/job/nope").status_code == 404
