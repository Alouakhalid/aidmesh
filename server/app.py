"""Tiny FastAPI server so the static site can run the real crew live.
The Groq key lives only in the host's GROQ_API_KEY secret. Never in the repo or the browser."""
import os, time, threading, collections
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List

from aidmesh.pipeline import run_pipeline

ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://alouakhalid.github.io").split(",")
PER_IP_PER_HOUR = int(os.getenv("PER_IP_PER_HOUR", "4"))
GLOBAL_PER_DAY = int(os.getenv("GLOBAL_PER_DAY", "150"))
MAX_REPORTS, MAX_CHARS = 8, 400

app = FastAPI(title="AidMesh API")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["POST", "GET"], allow_headers=["*"])
_hits = collections.defaultdict(list)
_day = []
_lock = threading.Semaphore(1)  # one crew run at a time (free tier memory)


class Report(BaseModel):
    id: str = Field(max_length=8)
    text: str = Field(max_length=MAX_CHARS)
    source: str = Field(default="web", max_length=12)


class RunRequest(BaseModel):
    reports: List[Report] = Field(min_length=1, max_length=MAX_REPORTS)


def _limit(ip: str):
    now = time.time()
    _hits[ip] = [t for t in _hits[ip] if now - t < 3600]
    global _day
    _day = [t for t in _day if now - t < 86400]
    if len(_hits[ip]) >= PER_IP_PER_HOUR or len(_day) >= GLOBAL_PER_DAY:
        raise HTTPException(429, "Rate limit reached. Showing the recorded run instead.")
    _hits[ip].append(now)
    _day.append(now)


@app.get("/api/health")
def health():
    return {"ok": True, "key_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/api/run")
def run(req: RunRequest, request: Request):
    ip = (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0].strip()
    _limit(ip)
    if not _lock.acquire(timeout=60):
        raise HTTPException(503, "Crew is busy, try again in a minute.")
    try:
        return run_pipeline([r.model_dump() for r in req.reports])
    except SystemExit as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(502, "Crew run failed: " + type(e).__name__)
    finally:
        _lock.release()
