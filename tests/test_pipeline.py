import json
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import server.app as srv
from aidmesh import cli, llm, pipeline

BODY = {"reports": [{"id": "R1", "text": "Flood at Manshiya"}]}


def test_require_key_message(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="GROQ_API_KEY"):
        llm.require_key()
    monkeypatch.setenv("GROQ_API_KEY", "k")
    assert llm.require_key() == "k"


def test_pipeline_collects_stage_outputs(monkeypatch):
    incidents = SimpleNamespace(model_dump_json=lambda indent=2: "{}", incidents=[])
    tasks = [SimpleNamespace(output=SimpleNamespace(raw=f"out-{n}")) for n in pipeline.STAGE_NAMES]
    crew = SimpleNamespace(kickoff=lambda: None, tasks=tasks)
    monkeypatch.setattr(pipeline, "run_intake", lambda reports: incidents)
    monkeypatch.setattr(pipeline, "build_crew", lambda inc, rep: crew)
    out = pipeline.run_pipeline([{"id": "R1", "text": "x"}])
    assert out["stages"]["verification"] == "out-verification"
    assert list(out["stages"]) == pipeline.STAGE_NAMES and out["incidents"] == []


def test_cli_writes_output(monkeypatch, tmp_path, capsys):
    src, dst = tmp_path / "in.json", tmp_path / "sub" / "out.json"
    src.write_text(json.dumps([{"id": "R1", "text": "x"}]))
    monkeypatch.setattr(cli, "run_pipeline", lambda r: {"stages": {"communication": "ALERT"}})
    monkeypatch.setattr("sys.argv", ["aidmesh", str(src), "--out", str(dst)])
    cli.main()
    assert json.loads(dst.read_text())["stages"]["communication"] == "ALERT"
    assert "ALERT" in capsys.readouterr().out


def _wait_for(client, job_id):
    for _ in range(60):
        state = client.get(f"/api/job/{job_id}").json()
        if state["status"] in ("done", "error"):
            return state
        time.sleep(0.05)
    return state


def test_failed_run_reports_type_only(monkeypatch):
    def boom(reports):
        raise ValueError("secret detail")

    monkeypatch.setattr(srv, "run_pipeline", boom)
    srv.limiter.reset(); srv.jobs.clear()
    client = TestClient(srv.app)
    state = _wait_for(client, client.post("/api/run", json=BODY).json()["job_id"])
    assert state["status"] == "error" and state["error"] == "Crew run failed: ValueError"
    assert "secret" not in json.dumps(state)


def test_missing_key_is_a_clean_error(monkeypatch):
    def no_key(reports):
        raise SystemExit("Set GROQ_API_KEY")

    monkeypatch.setattr(srv, "run_pipeline", no_key)
    srv.limiter.reset(); srv.jobs.clear()
    client = TestClient(srv.app)
    state = _wait_for(client, client.post("/api/run", json=BODY).json()["job_id"])
    assert state["status"] == "error" and "GROQ_API_KEY" in state["error"]


def test_busy_crew_returns_503(monkeypatch):
    srv.limiter.reset(); srv.jobs.clear()
    monkeypatch.setattr(srv.jobs, "max_active", 0)
    r = TestClient(srv.app).post("/api/run", json=BODY)
    assert r.status_code == 503
    srv.jobs.max_active = 3


def test_site_is_served_same_origin():
    client = TestClient(srv.app)
    assert client.get("/").status_code == 200
    assert client.get("/demo.html").status_code == 200
    assert client.get("/api/health").json()["ok"] is True


def test_security_headers_and_cache_policy():
    client = TestClient(srv.app)
    api = client.get("/api/health")
    assert api.headers["x-content-type-options"] == "nosniff"
    assert api.headers["x-frame-options"] == "DENY"
    assert api.headers["cache-control"] == "no-store"
    assert "max-age" in client.get("/demo.html").headers["cache-control"]


def test_report_text_is_cleaned_and_validated():
    assert srv.clean_text("  a\x00b\x07 c \n") == "ab c"
    client = TestClient(srv.app)
    for bad in ({"id": "R 1!", "text": "ok"}, {"id": "R1", "text": " \x00 "}):
        assert client.post("/api/run", json={"reports": [bad]}).status_code == 422
    assert srv.Report(id="R1", text="x", source="weird").source == "web"


def test_rate_limit_sets_retry_after(monkeypatch):
    monkeypatch.setattr(srv, "run_pipeline", lambda r: {})
    srv.limiter.reset(); srv.jobs.clear()
    client = TestClient(srv.app)
    last = [client.post("/api/run", json=BODY) for _ in range(srv.PER_IP_PER_HOUR + 1)][-1]
    assert last.status_code == 429 and last.headers["retry-after"] == "3600"


def test_server_starts_without_loading_the_crew_framework():
    import subprocess
    import sys

    code = "import sys, server.app; sys.exit(1 if 'crewai' in sys.modules else 0)"
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0


def test_crew_builds_with_four_agents_and_four_tasks(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    from aidmesh.crew import build_crew

    crew = build_crew("{}", "[]")
    assert len(crew.agents) == 4 and len(crew.tasks) == 4
