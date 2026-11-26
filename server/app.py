"""Small FastAPI server: runs the real crew for the website and serves the static site.

The Groq key lives only in the host's GROQ_API_KEY secret. Never in the repo or the browser.
"""
import os
import re
import threading
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from aidmesh.pipeline import run_pipeline

from .jobs import JobStore
from .limits import RateLimiter

ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://alouakhalid.github.io").split(",")
PER_IP_PER_HOUR = int(os.getenv("PER_IP_PER_HOUR", "4"))
GLOBAL_PER_DAY = int(os.getenv("GLOBAL_PER_DAY", "150"))
MAX_REPORTS, MAX_CHARS = 6, 400
SITE_DIR = Path(__file__).resolve().parent.parent / "docs"

app = FastAPI(title="AidMesh API")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["POST", "GET"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1024)



@app.middleware("http")
async def harden_and_cache(request: Request, call_next):
    """Security headers on every response; short caching for static files; never cache the API."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    elif response.status_code == 200:
        response.headers.setdefault("Cache-Control", "public, max-age=300")
    return response


limiter = RateLimiter(PER_IP_PER_HOUR, GLOBAL_PER_DAY)
jobs = JobStore(max_active=3)
_crew_slot = threading.Semaphore(1)  # one crew run at a time (small hosting plan)


_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SOURCES = {"web", "call", "sms", "social", "radio", "field"}


def clean_text(value: str) -> str:
    """Drop control characters and trim. Report text is untrusted input that reaches an LLM prompt."""
    return _CONTROL.sub("", value).strip()


class Report(BaseModel):
    id: str = Field(max_length=8, pattern=r"^[\w-]+$")
    text: str = Field(min_length=1, max_length=MAX_CHARS)
    source: str = Field(default="web", max_length=12)

    @field_validator("text")
    @classmethod
    def _text(cls, v: str) -> str:
        v = clean_text(v)
        if not v:
            raise ValueError("text is empty")
        return v

    @field_validator("source")
    @classmethod
    def _source(cls, v: str) -> str:
        return v if v in _SOURCES else "web"


class RunRequest(BaseModel):
    reports: List[Report] = Field(min_length=1, max_length=MAX_REPORTS)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return (forwarded or request.client.host).split(",")[0].strip()


def _worker(job_id: str, reports: list) -> None:
    """Runs in a thread and records the outcome in the job store."""
    try:
        with _crew_slot:
            jobs.update(job_id, status="running")
            result = run_pipeline(reports)
        jobs.update(job_id, status="done", result=result)
    except SystemExit as exc:
        jobs.update(job_id, status="error", error=str(exc))
    except Exception as exc:  # noqa: BLE001 - report the type only, never internals
        jobs.update(job_id, status="error", error="Crew run failed: " + type(exc).__name__)


@app.get("/api/health")
def health():
    return {"ok": True, "key_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/api/run")
def run(req: RunRequest, request: Request):
    if not limiter.allow(_client_ip(request)):
        raise HTTPException(429, "Rate limit reached. Showing the recorded run instead.",
                            headers={"Retry-After": "3600"})
    job_id = jobs.create()
    if job_id is None:
        raise HTTPException(503, "Crew is busy, try again in a minute.", headers={"Retry-After": "60"})
    reports = [r.model_dump() for r in req.reports]
    threading.Thread(target=_worker, args=(job_id, reports), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/job/{job_id}")
def job(job_id: str):
    state = jobs.public(job_id)
    if state is None:
        raise HTTPException(404, "Unknown job")
    return state


# Serve the static site (docs/) from the same origin. Mounted last so /api/* routes win.
if SITE_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(SITE_DIR), html=True), name="site")
