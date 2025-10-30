from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id = UUID_PK()
    fixture_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    served_as = Column(String, nullable=False)  # baseline | canary | shadow
    payload = Column(JSONB, nullable=False)     # probabilities etc.
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
