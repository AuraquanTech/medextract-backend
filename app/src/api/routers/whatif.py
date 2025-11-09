from fastapi import APIRouter, Depends
from src.api.deps import whatif_svc
router = APIRouter(prefix="/api", tags=["whatif"])

@router.post("/whatif/simulate")
async def simulate(context: dict, original: list[dict], changes: list[dict], svc=Depends(whatif_svc)):
    res = await svc.simulate(context["user_id"], context["case_id"], original, changes)
    return res
