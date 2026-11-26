import json, pytest
from aidmesh import tools_core as c


def test_detect_language():
    assert c.detect_language("سيول في حي المنشية") == "ar"
    assert c.detect_language("Flash flood at the bridge") == "en"
    assert c.detect_language("Flood في المنشية water") == "mixed"
    assert c.detect_language("12345") == "unknown"


def test_haversine_known_distance():
    # Alexandria to Cairo is about 180 km
    assert 175 < c.haversine_km(31.2001, 29.9187, 30.0444, 31.2357) < 185
    assert c.haversine_km(31.2, 29.9, 31.2, 29.9) == 0


def test_rumour_scores_low_and_specific_report_scores_high():
    rumour = c.credibility_score("BREAKING!!! dam collapsed in Alexandria, thousands dead, share now!!!", "social")
    real = c.credibility_score("Clinic in Sidi Gaber lost power, 6 dialysis patients waiting, generator fuel ends in 3 hours.", "call")
    assert rumour["label"] == "likely rumour" and rumour["score"] < 25
    assert real["label"] == "likely credible" and real["score"] >= 65
    assert real["score"] > rumour["score"]


def test_credibility_bounds():
    for t in ["", "!!!!!! SHARE NOW", "x" * 500]:
        s = c.credibility_score(t)["score"]
        assert 0 <= s <= 100


def test_arabic_report_gets_place_and_number_credit():
    r = c.credibility_score("سيول في حي المنشية، المياه وصلت لمتر ونص", "call")
    assert "names a concrete place" in r["reasons"]


def test_nearest_resources_sorted_and_filtered():
    res = c.nearest_resources(31.2238, 29.9372, "dialysis", k=3)
    assert res and all(r["kind"] == "dialysis" for r in res)
    allr = c.nearest_resources(31.2238, 29.9372, "", k=5)
    kms = [r["km"] for r in allr]
    assert kms == sorted(kms) and len(allr) == 5


def test_nearest_unknown_kind_is_empty():
    assert c.nearest_resources(31.2, 29.9, "spaceport") == []


def test_geocode_parses_response(monkeypatch):
    monkeypatch.setattr(c, "_get_json", lambda url, timeout=8: [{"lat": "31.2", "lon": "29.9", "display_name": "X"}])
    assert c.geocode("anything") == {"lat": 31.2, "lon": 29.9, "display_name": "X"}


def test_geocode_not_found_and_error(monkeypatch):
    monkeypatch.setattr(c, "_get_json", lambda url, timeout=8: [])
    assert c.geocode("zzz")["error"] == "not_found"
    def boom(url, timeout=8): raise TimeoutError()
    monkeypatch.setattr(c, "_get_json", boom)
    assert c.geocode("zzz")["error"] == "TimeoutError"


def test_weather_flood_sums_rain_and_trend(monkeypatch):
    def fake(url, timeout=8):
        if "flood-api" in url:
            return {"daily": {"river_discharge": [1.0, 2.0, 3.5]}}
        return {"hourly": {"precipitation": [0.5] * 24 + [9] * 24}}
    monkeypatch.setattr(c, "_get_json", fake)
    r = c.weather_flood(31.2, 29.9)
    assert r["rain_next_24h_mm"] == 12.0 and r["discharge_rising"] is True


def test_weather_degrades_gracefully(monkeypatch):
    def boom(url, timeout=8): raise OSError()
    monkeypatch.setattr(c, "_get_json", boom)
    r = c.weather_flood(31.2, 29.9)
    assert "rain_error" in r and "flood_error" in r


def test_crewai_tool_wrappers_return_json():
    from aidmesh.tools import credibility_tool, language_tool
    out = json.loads(credibility_tool.run(text="Bridge blocked on Corniche, 2 hours", source="call"))
    assert "score" in out
    assert language_tool.run(text="مرحبا") == "ar"
