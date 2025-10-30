from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
from sqlalchemy import text
from sqlalchemy.orm import Session

class ExtIdMap(Base):
    __tablename__ = "ext_id_map"
    source = Column(String, primary_key=True)
    entity = Column(String, primary_key=True)
    external_id = Column(String, primary_key=True)
    internal_uuid = Column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (UniqueConstraint("source", "entity", "external_id", name="uq_ext_id"),)

def upsert_map(db: Session, source: str, entity: str, external_id: str, internal_uuid):
    db.execute(text("""
    INSERT INTO ext_id_map(source, entity, external_id, internal_uuid)
    VALUES(:s, :e, :x, :i)
    ON CONFLICT (source, entity, external_id) DO UPDATE SET internal_uuid = EXCLUDED.internal_uuid
    """), {"s": source, "e": entity, "x": external_id, "i": internal_uuid})
    db.commit()

def get_uuid(db: Session, source: str, entity: str, external_id: str):
    row = db.execute(text("SELECT internal_uuid FROM ext_id_map WHERE source=:s AND entity=:e AND external_id=:x"),
                     {"s": source, "e": entity, "x": external_id}).fetchone()
    return row[0] if row else None
