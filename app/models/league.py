from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.session import Base

class League(Base):
    __tablename__ = "leagues"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid stored as text
    name: Mapped[str] = mapped_column(String(120), index=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    current_season_year: Mapped[int | None] = mapped_column(Integer)
