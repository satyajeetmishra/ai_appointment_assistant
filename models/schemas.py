
from pydantic import BaseModel, Field
from typing import Optional

class Step1Output(BaseModel):
    raw_text: str
    confidence: float = Field(ge=0, le=1)

class Entities(BaseModel):
    date_phrase: Optional[str] = None
    time_phrase: Optional[str] = None
    department: Optional[str] = None

class Step2Output(BaseModel):
    entities: Entities
    entities_confidence: float = Field(ge=0, le=1)

class Normalized(BaseModel):
    date: Optional[str] = None    # YYYY-MM-DD
    time: Optional[str] = None    # HH:MM (24h)
    tz: str = "Asia/Kolkata"

class Step3Output(BaseModel):
    normalized: Normalized
    normalization_confidence: float = Field(ge=0, le=1)

class FinalAppointment(BaseModel):
    department: Optional[str]
    date: Optional[str]
    time: Optional[str]
    tz: str = "Asia/Kolkata"

class FinalOutput(BaseModel):
    step1: Step1Output
    step2: Step2Output
    step3: Step3Output
    appointment: Optional[FinalAppointment] = None
    status: str  # "ok" or "needs_clarification"
    message: Optional[str] = None
    class Config:
        exclude_none = True