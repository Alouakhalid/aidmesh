from fastapi.testclient import TestClient
import server.app as srv

client = TestClient(srv.app)


def test_health():
    assert client.get("/api/health").json()["ok"] is True


def test_rejects_empty_and_oversized():
    assert client.post("/api/run", json={"reports": []}).status_code == 422
    big = [{"id": "R", "text": "x" * 401}]
    assert client.post("/api/run", json={"reports": big}).status_code == 422
    many = [{"id": f"R{i}", "text": "a"} for i in range(9)]
    assert client.post("/api/run", json={"reports": many}).status_code == 422


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(srv, "run_pipeline", lambda r: {"ok": True})
    srv._hits.clear(); srv._day.clear()
    body = {"reports": [{"id": "R1", "text": "Flood at Manshiya"}]}
    codes = [client.post("/api/run", json=body).status_code for _ in range(srv.PER_IP_PER_HOUR + 1)]
    assert codes[:-1] == [200] * srv.PER_IP_PER_HOUR and codes[-1] == 429


def test_cors_header():
    r = client.options("/api/run", headers={"Origin": "https://alouakhalid.github.io", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "https://alouakhalid.github.io"
