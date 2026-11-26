# AidMesh 🛟

**An AI crew that turns crisis chaos into action.** Raw, multilingual disaster reports go in. A verified, ranked, dispatched response plan comes out — in seconds, not hours.

🌐 **Live site:** https://alouakhalid.github.io/aidmesh/ · 🏆 Built for **PromptWars × AI Vibeathon 2026**

---

## The problem

In the first hours of a disaster, coordination rooms drown in noise:

- the same incident reported five times in two languages,
- panicked posts mixed with real calls for help,
- viral rumours ("the dam collapsed, thousands dead") that send rescuers to the wrong place.

Every minute spent sorting noise is a minute nobody gets rescued.

## The crew

LangChain structures the chaos. CrewAI runs four specialist agents in sequence. Groq makes it fast enough to matter.

```
raw reports (calls, SMS, social — Arabic + English)
        │
        ▼
┌─────────────┐   ┌───────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
│  LangChain  │ → │  🛡️ Verify │ → │ 🎯 Triage │ → │ 🚁 Dispatch│ → │ 📣 Alert │
│   intake    │   │  dedupe + │   │ P1 / P2  │   │ resource + │   │ bilingual │
│  (Pydantic) │   │  rumour   │   │   / P3   │   │ safe first │   │ alerts +  │
│             │   │  check    │   │          │   │  action    │   │ corrections│
└─────────────┘   └───────────┘   └──────────┘   └───────────┘   └──────────┘
```

| Agent | Job | Real output (recorded run) |
|---|---|---|
| 🛡️ Verification Analyst | Merges duplicate reports across Arabic and English; labels every incident VERIFIED, UNVERIFIED or RUMOUR | Two reports of the same trapped family merged into one VERIFIED incident; a viral dam-collapse post flagged RUMOUR |
| 🎯 Triage Lead | Ranks incidents P1/P2/P3 by threat to life, with reasoning | Trapped family and live wire P1; dialysis clinic on a 3-hour fuel clock P2; rumour P3 |
| 🚁 Resource Dispatcher | Matches a resource, a first safe action and a hazard check to every incident | Swift-water rescue + paramedic; electrical-hazard team with insulated gear; mobile generator crew |
| 📣 Community Communicator | Bilingual public alerts and rumour corrections | Arabic + English responder instructions and a public correction defusing the fake dam collapse |

## Quick start

```bash
git clone https://github.com/Alouakhalid/aidmesh && cd aidmesh
pip install -r requirements.txt
export GROQ_API_KEY=your_key        # https://console.groq.com
python -m aidmesh.cli data/reports.json --out docs/data/run.json
```

Tests: `pip install pytest && pytest`

## Repo layout

```
aidmesh/
  intake.py    # LangChain stage: ChatGroq + prompt + Pydantic structured output
  crew.py      # CrewAI stage: 4 agents, 4 tasks, sequential process
  llm.py       # Groq wiring for both frameworks (reads GROQ_API_KEY)
  schemas.py   # Pydantic incident schema
  cli.py       # entry point: intake, then crew
  pipeline.py  # shared pipeline helpers
data/reports.json      # six sample crisis reports (Arabic + English)
docs/                  # the 3D multi-page site (GitHub Pages)
  data/run.json        # recorded real run shown on the site
server/                # FastAPI backend (rate-limited, key from env)
tests/                 # schema tests
```

## The site

The `docs/` folder is a multi-page animated 3D site served by GitHub Pages:

- **Home** — the problem, the pipeline, why it is different
- **Use cases** — floods, earthquakes, wildfires, blackouts, mass-casualty, rumour control, plus a minute-by-minute walkthrough of the recorded run
- **One page per agent** — Verify, Triage, Dispatch, Alert, each with its own 3D scene and its real output
- **Live replay** — step-by-step replay of the recorded run on six Alexandria reports

## Honest limits

AidMesh assists human coordinators; it does not replace dispatchers. Verification labels (VERIFIED / UNVERIFIED / RUMOUR), not blind trust, are the safety feature. In the recorded run the crew ranked the rumour low but still proposed a recon flight — a human keeps the veto. Site numbers come from the recorded run in `docs/data/run.json`; nothing is mocked.

## License

MIT — see [LICENSE](LICENSE).
