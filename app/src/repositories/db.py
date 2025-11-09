from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, JSON, Integer
from src.infra.config import get_settings

_engine = create_async_engine(get_settings().db.dsn, pool_pre_ping=True)
async_session = async_sessionmaker(_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class AuditTable(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String)
    case_id: Mapped[str] = mapped_column(String)
    details: Mapped[dict] = mapped_column(JSON)
    previous_hash: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String)

    def as_dict(self):
        return {
            "timestamp": self.timestamp, "event_type": self.event_type,
            "user_id": self.user_id, "case_id": self.case_id,
            "details": self.details, "previous_hash": self.previous_hash, "hash": self.hash
        }
