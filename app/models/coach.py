from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Coach(Base):
    __tablename__ = "coaches"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    nationality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
