from fastapi import APIRouter, Depends
from src.api.deps import _auditor

router = APIRouter(prefix="/api", tags=["audit"])

@router.get("/audit/verify")
async def verify():
    ok = await _auditor.verify_chain_integrity()
    return {"status": "ok" if ok else "error"}
