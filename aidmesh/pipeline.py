"""Shared pipeline used by the CLI and the web server."""
import json

from .crew import build_crew
from .intake import run_intake

STAGE_NAMES = ["verification", "triage", "dispatch", "communication"]


def run_pipeline(reports: list[dict]) -> dict:
    incidents = run_intake(reports)
    inc_json = incidents.model_dump_json(indent=2)
    crew = build_crew(inc_json, json.dumps(reports, ensure_ascii=False))
    crew.kickoff()
    stages = {n: (t.output.raw if t.output else "") for n, t in zip(STAGE_NAMES, crew.tasks, strict=True)}
    return {"reports": reports, "incidents": [i.model_dump() for i in incidents.incidents], "stages": stages}
