from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AuditEntry:
    timestamp: str
    event_type: str
    user_id: str
    case_id: str
    details: Dict[str, Any]
    previous_hash: str
    hash: str


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
