import os

MODEL = os.getenv("AIDMESH_MODEL", "openai/gpt-oss-120b")


def require_key() -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise SystemExit("Set GROQ_API_KEY (free at https://console.groq.com) to run the live crew.")
    return key


def langchain_llm(temperature: float = 0.0):
    from langchain_groq import ChatGroq

    return ChatGroq(model=MODEL, temperature=temperature, api_key=require_key())


def crewai_llm(temperature: float = 0.2):
    from crewai import LLM

    return LLM(model=f"groq/{MODEL}", temperature=temperature, api_key=require_key())
