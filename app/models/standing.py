from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Standing(Base):
    __tablename__ = "standings"
    id: Mapped[str] = mapped_column(primary_key=True)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    season_id: Mapped[str] = mapped_column(ForeignKey("seasons.id"), index=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    rank: Mapped[int] = mapped_column(Integer, index=True)
    points: Mapped[int] = mapped_column(Integer)
    played: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    draws: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
