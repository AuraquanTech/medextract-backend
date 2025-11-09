from pydantic import BaseModel
from .common import UserContext

class AnalyzeRequest(BaseModel):
    context: UserContext
    meta: dict = {}

class AnalyzeResponse(BaseModel):
    success: bool
    extracted_data: dict | None = None
    confidence: float | None = None
    reason: str | None = None
    cached: bool | None = None
