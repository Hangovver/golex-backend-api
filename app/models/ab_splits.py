from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class ABSplit(Base):
    __tablename__ = "ab_splits"
    id = UUID_PK()
    key = Column(String, nullable=False, unique=True)        # e.g., predictions.canary
    percent = Column(Integer, nullable=False, default=0)     # 0..100
    canary_model = Column(String, nullable=True)             # e.g., poisson_alt, lgbm
    active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
