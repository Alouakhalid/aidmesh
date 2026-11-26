"""Stage 2 (CrewAI): four specialist agents verify, rank, dispatch and communicate."""
from crewai import Agent, Crew, Process, Task

from .llm import crewai_llm
from .tools import credibility_tool, geocode_tool, language_tool, nearest_tool, weather_tool

FORMAT_RULES = "Be concise. Plain text. No markdown tables."


def build_crew(incidents_json: str, reports_json: str = "[]") -> Crew:
    llm = crewai_llm()

    verifier = Agent(
        role="Verification Analyst",
        goal="Find duplicate reports and flag claims that are unverified or likely rumours.",
        backstory=("A fact-checker from a newsroom who learned that during floods, "
                   "rumours cost lives and lorries."),
        llm=llm, allow_delegation=False, verbose=False,
        tools=[credibility_tool, language_tool])
    triager = Agent(
        role="Triage Lead",
        goal="Rank verified incidents by urgency (P1 life at risk now, P2 within hours, P3 later) with a one-line reason.",  # noqa: E501
        backstory="An emergency physician who ranks by time-to-harm, not by who shouts loudest.",
        llm=llm, allow_delegation=False, verbose=False,
        tools=[geocode_tool, weather_tool])
    dispatcher = Agent(
        role="Resource Dispatcher",
        goal="Match each incident to a concrete resource type and a safe first action, in priority order.",
        backstory="A logistics planner for civil defence who always checks hazards before sending people in.",
        llm=llm, allow_delegation=False, verbose=False,
        tools=[geocode_tool, nearest_tool, weather_tool])
    comms = Agent(
        role="Community Communicator",
        goal="Write short SMS-length alerts in Arabic and English for the public and for field teams.",
        backstory="A crisis communicator who writes calm, clear messages that never spread panic.",
        llm=llm, allow_delegation=False, verbose=False)

    t1 = Task(
        description=("Structured incidents:\n" + incidents_json + "\nRaw reports:\n" + reports_json +
                     "\nMerge duplicates (same place, same need). Mark each merged incident VERIFIED, "
                     "UNVERIFIED or RUMOUR with a short reason. Extreme claims with no place detail or "
                     "no second source are RUMOUR. " + FORMAT_RULES),
        expected_output="A list of merged incidents with a verification label and reason.",
        agent=verifier)
    t2 = Task(
        description="Rank the non-rumour incidents P1, P2 or P3 with one-line reasons. " + FORMAT_RULES,
        expected_output="Ranked list with priority and reason.", agent=triager, context=[t1])
    t3 = Task(
        description=("For each ranked incident: geocode_place the location (add Alexandria, Egypt), "
                     "call nearest_resources for the right kind, and weather_flood_risk once for the city. "
                     "Then give: the named nearest resource with distance in km, first safe action, "
                     "and one hazard to check before arrival. " + FORMAT_RULES),
        expected_output="Dispatch plan in priority order.", agent=dispatcher, context=[t2])
    t4 = Task(
        description=("Write one Arabic and one English SMS alert (under 160 characters each) for the top "
                     "two incidents, plus one public message correcting the rumour if any. " + FORMAT_RULES),
        expected_output="Alerts in Arabic and English.", agent=comms, context=[t3, t1])

    return Crew(agents=[verifier, triager, dispatcher, comms], tasks=[t1, t2, t3, t4],
                process=Process.sequential, verbose=False)
