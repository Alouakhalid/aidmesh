"""Stage 1 (LangChain): turn messy multilingual reports into structured incidents."""
import functools
import json

from .llm import langchain_llm
from .schemas import Incidents

SYSTEM_PROMPT = (
    "You are the intake desk of a disaster response room. Extract one incident per report. "
    "Reports may be Arabic, English or mixed. Translate locations and summaries to English. "
    "Never invent facts that are not in the text. Use null when a number is not stated."
)


@functools.lru_cache(maxsize=1)
def _prompt():
    # Imported on first use so the web server starts without loading LangChain.
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Reports as JSON:\n{reports}"),
    ])


def run_intake(reports: list[dict]) -> Incidents:
    chain = _prompt() | langchain_llm().with_structured_output(Incidents)
    return chain.invoke({"reports": json.dumps(reports, ensure_ascii=False)})
