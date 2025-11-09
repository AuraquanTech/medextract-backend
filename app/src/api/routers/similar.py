from fastapi import APIRouter, Depends
from src.api.deps import similar_svc
router = APIRouter(prefix="/api", tags=["similar"])

@router.post("/similar/search")
async def search_similar(context: dict, case_summary: str, top_k: int = 5, svc=Depends(similar_svc)):
    res = await svc.search(context["user_id"], context["case_id"], case_summary, top_k)
    return res
