#!/usr/bin/env python3
"""Load demo data for development."""
import asyncio
from src.services.audit import DigitalEvidenceAuditor
from src.repositories.audit_repo import AuditRepository

async def load_demo():
    repo = AuditRepository()
    auditor = DigitalEvidenceAuditor(repo)
    
    await auditor.log_event("DEMO_EVENT", "user1", "case1", {"demo": True})
    await auditor.log_event("DEMO_EVENT", "user2", "case2", {"demo": True})
    
    print("Demo data loaded!")

if __name__ == "__main__":
    asyncio.run(load_demo())
