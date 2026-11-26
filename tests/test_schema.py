import json, pathlib
from aidmesh.schemas import Incidents

def test_recorded_run_matches_schema():
    d = json.loads(pathlib.Path("docs/data/run.json").read_text())
    inc = Incidents(incidents=d["incidents"])
    assert len(inc.incidents) == 6
    assert any(i.life_threatening for i in inc.incidents)


def test_all_incident_needs_are_valid_and_recorded_run_has_four_stages():
    d = json.loads(pathlib.Path("docs/data/run.json").read_text())
    assert set(d["stages"]) == {"verification", "triage", "dispatch", "communication"}
    assert all(d["stages"].values())
