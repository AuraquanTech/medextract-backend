from fastapi import APIRouter, Depends, UploadFile, File
from src.api.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from src.api.deps import analyzer_svc
router = APIRouter(prefix="/api", tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, svc=Depends(analyzer_svc)):
    doc_bytes = b""
    res = await svc.analyze_document(req.context.user_id, req.context.case_id, doc_bytes, req.meta)
    return res
