import pytest
from src.services.analyzer import AnalyzerService
from src.services.audit import DigitalEvidenceAuditor
from src.repositories.audit_repo import AuditRepository

@pytest.mark.asyncio
async def test_analyze_returns_success():
    svc = AnalyzerService(DigitalEvidenceAuditor(AuditRepository()))
    res = await svc.analyze_document("u","c",b"",{})
    assert res["success"] is True
    assert "confidence" in res
