from src.services.audit import DigitalEvidenceAuditor
from src.repositories.audit_repo import AuditRepository
from src.services.analyzer import AnalyzerService
from src.services.experts import ExpertFinderService
from src.services.similar import SimilarityService
from src.services.whatif import WhatIfService

_repo = AuditRepository()
_auditor = DigitalEvidenceAuditor(_repo)

def analyzer_svc():
    return AnalyzerService(_auditor)

def experts_svc():
    return ExpertFinderService(_auditor)

def similar_svc():
    return SimilarityService(_auditor)

def whatif_svc():
    return WhatIfService(_auditor)
