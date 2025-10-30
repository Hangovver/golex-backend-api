from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from .base import Base
import uuid as _uuid

def UUID_PK():
    from sqlalchemy.dialects.postgresql import UUID as _UUID
    from sqlalchemy import Column as _Column
    return _Column(_UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = UUID_PK()
    device_id = Column(String, nullable=False)
    token = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # android/ios
    lang = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("token", name="uq_token_unique"),)

class NotificationPreference(Base):
    __tablename__ = "notification_prefs"
    id = UUID_PK()
    device_id = Column(String, nullable=False)
    key = Column(String, nullable=False)   # e.g., notif.match.start, notif.goal, follow.team.<id>, follow.league.<id>
    value = Column(String, nullable=False) # "on"/"off" or JSON string
    __table_args__ = (UniqueConstraint("device_id", "key", name="uq_pref_device_key"),)
