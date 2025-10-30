from sqlalchemy import String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Player(Base):
    __tablename__ = "players"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    name: Mapped[str] = mapped_column(String(140), index=True)
    nationality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    birthdate: Mapped[Date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(24), nullable=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True)
