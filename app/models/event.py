from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    fixture_id: Mapped[str] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), index=True)
    minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    player_id: Mapped[str | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(40))  # Goal, Card, Substitution...
    detail: Mapped[str | None] = mapped_column(String(80), nullable=True)
    result: Mapped[str | None] = mapped_column(String(80), nullable=True)
