from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    name: Mapped[str] = mapped_column(String(140), index=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
