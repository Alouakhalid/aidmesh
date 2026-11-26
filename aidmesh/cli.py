import argparse, json, pathlib
from .pipeline import run_pipeline


def main():
    p = argparse.ArgumentParser(prog="aidmesh", description="Run the AidMesh crew on a reports file.")
    p.add_argument("reports", nargs="?", default="data/reports.json")
    p.add_argument("--out", default="docs/data/run.json")
    a = p.parse_args()
    reports = json.loads(pathlib.Path(a.reports).read_text())
    out = run_pipeline(reports)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(out["stages"]["communication"])


if __name__ == "__main__":
    main()
