from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Fixture(Base):
    __tablename__ = "fixtures"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    season_id: Mapped[str] = mapped_column(ForeignKey("seasons.id"), index=True)
    home_team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    venue_id: Mapped[str | None] = mapped_column(ForeignKey("venues.id"), nullable=True)
    starts_at_utc: Mapped[DateTime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)  # SCHEDULED/LIVE/HT/FT/POSTPONED/CANCELLED
    round: Mapped[str | None] = mapped_column(String(60), nullable=True)
    referee: Mapped[str | None] = mapped_column(String(120), nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
