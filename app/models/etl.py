from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base
import uuid as _uuid
from datetime import datetime, timezone

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class RawPayload(Base):
    __tablename__ = "raw_payloads"
    id = UUID_PK()
    source = Column(String, nullable=False)         # api-football
    endpoint = Column(String, nullable=False)       # fixtures, events, standings...
    params_hash = Column(String, nullable=False)    # sha256 of sorted params
    payload_hash = Column(String, nullable=False)   # sha256(payload)
    received_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    payload = Column(JSONB, nullable=False)
    __table_args__ = (UniqueConstraint("source", "endpoint", "payload_hash", name="uq_raw_dedup"),)

class IngestionLog(Base):
    __tablename__ = "ingestion_log"
    id = UUID_PK()
    source = Column(String, nullable=False)         # api-football
    entity = Column(String, nullable=False)         # league/team/fixture/...
    external_id = Column(String, nullable=False)
    fingerprint = Column(String, nullable=False)    # stable hash for idempotency
    processed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("source", "entity", "external_id", "fingerprint", name="uq_ingest_once"),)

class DQMetric(Base):
    __tablename__ = "dq_metrics"
    id = UUID_PK()
    name = Column(String, nullable=False)           # e.g., completeness.fixtures.goals
    dimension = Column(String, nullable=True)       # e.g., date=2025-01-01
    value = Column(Float, nullable=False)
    captured_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class DQIssue(Base):
    __tablename__ = "dq_issues"
    id = UUID_PK()
    severity = Column(String, nullable=False)       # info/warn/critical
    title = Column(String, nullable=False)
    context = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
