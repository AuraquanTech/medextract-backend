import pytest, asyncio
from src.services.audit import DigitalEvidenceAuditor
from src.repositories.audit_repo import AuditRepository

@pytest.mark.asyncio
async def test_chain_integrity():
    repo = AuditRepository()
    auditor = DigitalEvidenceAuditor(repo)
    e1 = await auditor.log_event("E1","u","c",{"x":1})
    e2 = await auditor.log_event("E2","u","c",{"y":2})
    assert await auditor.verify_chain_integrity()
