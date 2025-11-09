from fastapi import APIRouter, Response
router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/ready")
async def ready():
    return {"status": "ready"}
