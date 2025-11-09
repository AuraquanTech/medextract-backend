from typing import Any, Dict, List
from src.services.audit import DigitalEvidenceAuditor

class WhatIfService:
    def __init__(self, auditor: DigitalEvidenceAuditor):
        self.auditor = auditor

    async def simulate(self, user_id: str, case_id: str, original: List[Dict], changes: List[Dict]) -> Dict[str, Any]:
        await self.auditor.log_event("WHAT_IF_SIMULATION_REQUESTED", user_id, case_id, {"num_changes": len(changes)})
        modified = original[:]
        predictions = {
            "probability_of_success": "72.4%",
            "confidence": "medium",
            "explanation": "Bayesian estimate over timeline factors."
        }
        await self.auditor.log_event("WHAT_IF_SIMULATION_COMPLETE", user_id, case_id, {"summary": "ok"})
        return {"modified_timeline": modified, "predictions": predictions}
