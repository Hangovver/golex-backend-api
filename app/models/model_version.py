from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = UUID_PK()
    name = Column(String, nullable=False)          # e.g., poisson, poisson_alt, lgbm
    version = Column(String, nullable=False)       # e.g., 0.1.0
    label = Column(String, nullable=True)          # e.g., "prod", "canary"
    active = Column(Boolean, nullable=False, default=False)
    canary = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
