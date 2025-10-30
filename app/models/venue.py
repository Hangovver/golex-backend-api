from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
