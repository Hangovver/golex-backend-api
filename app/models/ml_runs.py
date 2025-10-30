from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class MLRun(Base):
    __tablename__ = "ml_runs"
    id = UUID_PK()
    run_id = Column(String, nullable=False)         # external/idempotent
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=True)
    params = Column(JSONB, nullable=True)
    metrics = Column(JSONB, nullable=True)
    status = Column(String, nullable=False, default="running")  # running|finished|failed
    artifact_uri = Column(Text, nullable=True)      # e.g., s3://bucket/... or file://...
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
