import json, pathlib
from aidmesh.schemas import Incidents

def test_recorded_run_matches_schema():
    d = json.loads(pathlib.Path("docs/data/run.json").read_text())
    inc = Incidents(incidents=d["incidents"])
    assert len(inc.incidents) == 6
    assert any(i.life_threatening for i in inc.incidents)
