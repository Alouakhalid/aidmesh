from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Incident(BaseModel):
    report_id: str
    language: str = Field(description="ISO code of the report language, e.g. ar or en")
    need: Literal["rescue", "medical", "water_food", "hazard", "shelter", "other"]
    location: str = Field(description="Most specific place named in the report, in English")
    people_affected: Optional[int] = None
    life_threatening: bool
    summary: str = Field(description="One neutral sentence in English")


class Incidents(BaseModel):
    incidents: List[Incident]
