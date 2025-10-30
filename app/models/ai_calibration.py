from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class AICalibration(Base):
    __tablename__ = "ai_calibrations"
    id = UUID_PK()
    model_version = Column(String, nullable=False)   # e.g., poisson-dc-0.1
    key = Column(String, nullable=False)             # e.g., 1x2.H / over25 / btts
    method = Column(String, nullable=False)          # platt | isotonic
    params = Column(JSONB, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
