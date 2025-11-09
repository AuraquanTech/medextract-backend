from typing import Optional
from .db import AuditTable, async_session
from sqlalchemy import select

class AuditRepository:
    async def append(self, entry: dict) -> None:
        async with async_session() as s:
            s.add(AuditTable(**entry))
            await s.commit()

    async def last_hash(self) -> str:
        async with async_session() as s:
            q = await s.execute(select(AuditTable.hash).order_by(AuditTable.id.desc()).limit(1))
            row = q.first()
            return row[0] if row else "0"*64

    async def all(self) -> list[dict]:
        async with async_session() as s:
            q = await s.execute(select(AuditTable).order_by(AuditTable.id))
            return [row[0].as_dict() for row in q.all()]
