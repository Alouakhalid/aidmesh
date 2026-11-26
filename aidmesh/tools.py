"""CrewAI tool wrappers around aidmesh.tools_core. Each returns a compact JSON string."""
import json

from crewai.tools import tool

from . import tools_core as core


@tool("credibility_score")
def credibility_tool(text: str, source: str = "") -> str:
    """Score how credible a raw crisis report is (0-100) with reasons. Use before labelling VERIFIED/RUMOUR."""
    return json.dumps(core.credibility_score(text, source), ensure_ascii=False)


@tool("detect_language")
def language_tool(text: str) -> str:
    """Detect whether a report is Arabic (ar), English (en) or mixed."""
    return core.detect_language(text)


@tool("geocode_place")
def geocode_tool(place: str) -> str:
    """Get latitude/longitude for a place name in Egypt using OpenStreetMap. Include the city, e.g. 'Sidi Gaber, Alexandria'."""  # noqa: E501
    return json.dumps(core.geocode(place), ensure_ascii=False)


@tool("nearest_resources")
def nearest_tool(lat: float, lon: float, kind: str = "") -> str:
    """Find the nearest response resources (kind: hospital, dialysis, rescue, shelter, electric, water; empty for all). Sample registry."""  # noqa: E501
    return json.dumps(core.nearest_resources(float(lat), float(lon), kind), ensure_ascii=False)


@tool("weather_flood_risk")
def weather_tool(lat: float, lon: float) -> str:
    """Get rain forecast (next 24h) and river discharge trend for coordinates from Open-Meteo."""
    return json.dumps(core.weather_flood(float(lat), float(lon)), ensure_ascii=False)
