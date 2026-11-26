import argparse, json, pathlib
from .intake import run_intake
from .crew import build_crew


def main():
    p = argparse.ArgumentParser(prog="aidmesh", description="Run the AidMesh crew on a reports file.")
    p.add_argument("reports", nargs="?", default="data/reports.json")
    p.add_argument("--out", default="docs/data/run.json")
    a = p.parse_args()
    reports = json.loads(pathlib.Path(a.reports).read_text())
    incidents = run_intake(reports)
    inc_json = incidents.model_dump_json(indent=2)
    crew = build_crew(inc_json)
    result = crew.kickoff()
    stages = {}
    names = ["verification", "triage", "dispatch", "communication"]
    for n, t in zip(names, crew.tasks):
        stages[n] = t.output.raw if t.output else ""
    out = {"reports": reports, "incidents": json.loads(inc_json)["incidents"], "stages": stages}
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(result)


if __name__ == "__main__":
    main()
