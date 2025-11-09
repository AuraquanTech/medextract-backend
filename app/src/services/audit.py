from src.repositories.audit_repo import AuditRepository
from src.utils.hashing import sha256_hex
from src.domain.audit import AuditEntry, utc_now_iso

class DigitalEvidenceAuditor:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def log_event(self, event_type: str, user_id: str, case_id: str, details: dict) -> AuditEntry:
        prev_hash = await self.repo.last_hash()
        base = {
            "timestamp": utc_now_iso(),
            "event_type": event_type,
            "user_id": user_id,
            "case_id": case_id,
            "details": details,
            "previous_hash": prev_hash
        }
        new_hash = sha256_hex({**base, "previous_hash": prev_hash})
        entry = AuditEntry(**base, hash=new_hash)
        await self.repo.append(entry.__dict__)
        return entry

    async def verify_chain_integrity(self) -> bool:
        entries = await self.repo.all()
        prev = "0"*64
        for e in entries:
            computed = sha256_hex({k:v for k,v in e.items() if k!="hash"})
            if computed != e["hash"] or e["previous_hash"] != prev:
                return False
            prev = e["hash"]
        return True
