from pydantic import BaseModel, Field

class UserContext(BaseModel):
    user_id: str = Field(..., min_length=3)
    case_id: str = Field(..., min_length=3)
