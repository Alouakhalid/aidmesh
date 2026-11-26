"""Plain-Python helpers behind the crew tools. No LLM, no framework: easy to test."""
import functools
import json
import math
import pathlib
import re
import time
import urllib.parse
import urllib.request

UA = "aidmesh/1.0 (hackathon project; github.com/Alouakhalid/aidmesh)"
RESOURCES = pathlib.Path(__file__).resolve().parent.parent / "data" / "resources.json"
CACHE_SECONDS = 600  # identical geocode / weather lookups within 10 minutes reuse one answer

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_LATIN = re.compile(r"[A-Za-z]")


@functools.lru_cache(maxsize=256)
def _fetch_json(url: str, timeout: float, _bucket: int):
    """Network call. Failed calls raise, so lru_cache never stores an error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_json(url: str, timeout: float = 8.0):
    """GET a JSON document, cached for CACHE_SECONDS (the bucket changes the cache key over time)."""
    return _fetch_json(url, timeout, int(time.time() // CACHE_SECONDS))


def detect_language(text: str) -> str:
    """'ar' if most letters are Arabic script, 'en' if Latin, 'mixed' otherwise."""
    ar = len(_ARABIC.findall(text))
    la = len(_LATIN.findall(text))
    if ar == 0 and la == 0:
        return "unknown"
    if ar > 0 and la > 0 and min(ar, la) / max(ar, la) > 0.3:
        return "mixed"
    return "ar" if ar > la else "en"


_FLAGS = re.I
# (penalty or bonus, reason, pattern). Order is the order reasons are reported in.
_SHOUT_BANGS = re.compile(r"!{2,}")
_SHOUT_CAPS = re.compile(r"\b[A-Z]{5,}\b")
_RULES = [
    (-15, "asks to share", re.compile(r"share now|forward|urgent share|انشر|شير", _FLAGS)),
    (-15, "extreme casualty claim", re.compile(
        r"\b\d{2,}[,.]?\d*\s*(dead|deaths|killed|victims)|thousands? (dead|of deaths)|آلاف", _FLAGS)),
    (15, "contains checkable numbers", re.compile(
        r"\d+(\.\d+)?\s*(m|meter|metre|متر)|\b\d{2,4}\s*(people|persons|patients|عيلة)|\b\d+\s*hours?", _FLAGS)),
    (15, "names a concrete place", re.compile(
        r"(district|street|bridge|school|clinic|hospital|corniche|road|حي|شارع|كوبري|مدرسة|عيادة|مستشفى)", _FLAGS)),
]
_SOURCE_ADJUST = {"call": (5, "direct channel"), "sms": (5, "direct channel"),
                  "social": (-5, "unverified social post")}


def credibility_score(text: str, source: str = "") -> dict:
    """Transparent rule-based score from 0 (rumour-like) to 100 (specific, calm, checkable)."""
    score, reasons = 50, []
    if _SHOUT_BANGS.search(text) or _SHOUT_CAPS.search(text):
        score -= 20
        reasons.append("shouting (caps or repeated !)")
    for delta, reason, pattern in _RULES:
        if pattern.search(text):
            score += delta
            reasons.append(reason)
    if source in _SOURCE_ADJUST:
        delta, reason = _SOURCE_ADJUST[source]
        score += delta
        reasons.append(reason)
    score = max(0, min(100, score))
    label = "likely credible" if score >= 65 else "needs confirmation" if score >= 40 else "likely rumour"
    return {"score": score, "label": label, "reasons": reasons}


def geocode(place: str, country: str = "eg") -> dict:
    """Look up coordinates with OpenStreetMap Nominatim. Returns {} on failure."""
    q = urllib.parse.urlencode({"q": place, "format": "json", "limit": 1, "countrycodes": country})
    try:
        data = _get_json("https://nominatim.openstreetmap.org/search?" + q)
    except Exception as e:
        return {"error": type(e).__name__}
    if not data:
        return {"error": "not_found"}
    d = data[0]
    return {"lat": float(d["lat"]), "lon": float(d["lon"]), "display_name": d.get("display_name", "")[:120]}


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@functools.lru_cache(maxsize=4)
def _load_registry(path: str) -> tuple:
    """Read the registry once per path; the file never changes while the server runs."""
    return tuple(json.loads(pathlib.Path(path).read_text()))


def nearest_resources(lat: float, lon: float, kind: str = "", k: int = 3, path=RESOURCES) -> list:
    """Nearest entries of the (sample) resource registry, by great-circle distance."""
    items = list(_load_registry(str(path)))
    if kind:
        items = [i for i in items if i["kind"] == kind]
    out = [{**i, "km": round(haversine_km(lat, lon, i["lat"], i["lon"]), 2)} for i in items]
    return sorted(out, key=lambda x: x["km"])[:k]


def weather_flood(lat: float, lon: float) -> dict:
    """Next-24h rain from Open-Meteo plus river-discharge trend from its flood API."""
    out = {}
    try:
        w = _get_json(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                      "&hourly=precipitation&forecast_days=2&timezone=auto")
        pr = w["hourly"]["precipitation"][:24]
        out["rain_next_24h_mm"] = round(sum(x or 0 for x in pr), 1)
    except Exception as e:
        out["rain_error"] = type(e).__name__
    try:
        f = _get_json(f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}"
                      "&daily=river_discharge&forecast_days=3")
        dis = [x for x in f["daily"]["river_discharge"] if x is not None]
        if dis:
            out["river_discharge_m3s"] = dis
            out["discharge_rising"] = dis[-1] > dis[0]
    except Exception as e:
        out["flood_error"] = type(e).__name__
    return out
