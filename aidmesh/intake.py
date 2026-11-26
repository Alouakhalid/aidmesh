"""Stage 1 (LangChain): turn messy multilingual reports into structured incidents."""
import json
from langchain_core.prompts import ChatPromptTemplate
from .llm import langchain_llm
from .schemas import Incidents

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the intake desk of a disaster response room. Extract one incident per report. "
     "Reports may be Arabic, English or mixed. Translate locations and summaries to English. "
     "Never invent facts that are not in the text. Use null when a number is not stated."),
    ("human", "Reports as JSON:\n{reports}"),
])


def run_intake(reports: list[dict]) -> Incidents:
    chain = PROMPT | langchain_llm().with_structured_output(Incidents)
    return chain.invoke({"reports": json.dumps(reports, ensure_ascii=False)})
