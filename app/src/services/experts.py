from typing import List, Dict
from src.services.audit import DigitalEvidenceAuditor

class ExpertFinderService:
    def __init__(self, auditor: DigitalEvidenceAuditor):
        self.auditor = auditor

    async def find(self, user_id: str, case_id: str, case_summary: str, specialties: List[str], urgency: str="normal") -> List[Dict]:
        await self.auditor.log_event("EXPERT_SEARCH_QUERY", user_id, case_id, {"specialties": specialties, "urgency": urgency})
        experts = []
        await self.auditor.log_event("EXPERT_SEARCH_RESULTS", user_id, case_id, {"count": len(experts)})
        return experts
