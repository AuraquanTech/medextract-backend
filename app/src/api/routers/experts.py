from fastapi import APIRouter, Depends
from src.api.deps import experts_svc
router = APIRouter(prefix="/api", tags=["experts"])

@router.post("/experts/find")
async def find_experts(context: dict, case_summary: str, specialties: list[str], urgency: str = "normal", svc=Depends(experts_svc)):
    res = await svc.find(context["user_id"], context["case_id"], case_summary, specialties, urgency)
    return res
