from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.etl import RawPayload
from ..utils.hash import sha256_json

def save_raw(db: Session, source: str, endpoint: str, params: dict, payload: dict):
    params_hash = sha256_json(params or {})
    payload_hash = sha256_json(payload or {})
    # Insert if unique (dedup by payload_hash)
    db.execute(text("""
    INSERT INTO raw_payloads(id, source, endpoint, params_hash, payload_hash, received_at, payload)
    VALUES (gen_random_uuid(), :s, :e, :ph, :yh, NOW(), :p)
    ON CONFLICT ON CONSTRAINT uq_raw_dedup DO NOTHING
    """), {"s": source, "e": endpoint, "ph": params_hash, "yh": payload_hash, "p": payload})
    db.commit()
    return {"params_hash": params_hash, "payload_hash": payload_hash}
