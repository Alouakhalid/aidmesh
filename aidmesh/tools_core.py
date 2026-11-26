"""Plain-Python helpers behind the crew tools. No LLM, no framework: easy to test."""
import json, math, pathlib, re
import urllib.parse, urllib.request

UA = "aidmesh/1.0 (hackathon project; github.com/Alouakhalid/aidmesh)"
RESOURCES = pathlib.Path(__file__).resolve().parent.parent / "data" / "resources.json"


def _get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def detect_language(text: str) -> str:
    """'ar' if most letters are Arabic script, 'en' if Latin, 'mixed' otherwise."""
    ar = len(re.findall(r"[\u0600-\u06FF]", text))
    la = len(re.findall(r"[A-Za-z]", text))
    if ar == 0 and la == 0:
        return "unknown"
    if ar > 0 and la > 0 and min(ar, la) / max(ar, la) > 0.3:
        return "mixed"
    return "ar" if ar > la else "en"


def credibility_score(text: str, source: str = "") -> dict:
    """Transparent rule-based score from 0 (rumour-like) to 100 (specific, calm, checkable)."""
    score, reasons = 50, []
    shout = len(re.findall(r"!{2,}", text)) + len(re.findall(r"\b[A-Z]{5,}\b", text))
    if shout:
        score -= 20; reasons.append("shouting (caps or repeated !)")
    if re.search(r"share now|forward|urgent share|انشر|شير", text, re.I):
        score -= 15; reasons.append("asks to share")
    if re.search(r"\b\d{2,}[,.]?\d*\s*(dead|deaths|killed|victims)|thousands? (dead|of deaths)|آلاف", text, re.I):
        score -= 15; reasons.append("extreme casualty claim")
    if re.search(r"\d+(\.\d+)?\s*(m|meter|metre|متر)|\b\d{2,4}\s*(people|persons|patients|عيلة)|\b\d+\s*hours?", text, re.I):
        score += 15; reasons.append("contains checkable numbers")
    if re.search(r"(district|street|bridge|school|clinic|hospital|corniche|road|حي|شارع|كوبري|مدرسة|عيادة|مستشفى)", text, re.I):
        score += 15; reasons.append("names a concrete place")
    if source in ("call", "sms"):
        score += 5; reasons.append("direct channel")
    if source == "social":
        score -= 5; reasons.append("unverified social post")
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


def nearest_resources(lat: float, lon: float, kind: str = "", k: int = 3, path=RESOURCES) -> list:
    """Nearest entries of the (sample) resource registry, by great-circle distance."""
    items = json.loads(pathlib.Path(path).read_text())
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
