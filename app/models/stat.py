from sqlalchemy import Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class FixtureTeamStat(Base):
    __tablename__ = "fixture_team_stats"
    id: Mapped[str] = mapped_column(primary_key=True)
    fixture_id: Mapped[str] = mapped_column(ForeignKey("fixtures.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    shots_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on: Mapped[int | None] = mapped_column(Integer, nullable=True)
    possession: Mapped[Float | None] = mapped_column(Float, nullable=True)   # 0..100
    corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yellow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xg: Mapped[Float | None] = mapped_column(Float, nullable=True)           # if available
