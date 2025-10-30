from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(16), default="android")  # android/ios/web
    locale: Mapped[str] = mapped_column(String(8), default="tr")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    token_id: Mapped[str] = mapped_column(ForeignKey("device_tokens.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("token_id", "topic", name="uq_subscription_token_topic"), )
