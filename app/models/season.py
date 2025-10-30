from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..db.session import Base

class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[str] = mapped_column(primary_key=True)  # uuid
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)  # e.g., 2025
