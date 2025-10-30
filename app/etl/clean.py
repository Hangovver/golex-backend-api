import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..repositories import upserts as U
from ..utils.hash import sha256_json

def _already_processed(db: Session, source: str, entity: str, external_id: str, fp: str) -> bool:
    row = db.execute(text("SELECT 1 FROM ingestion_log WHERE source=:s AND entity=:e AND external_id=:x AND fingerprint=:f"),
                     {"s": source, "e": entity, "x": external_id, "f": fp}).fetchone()
    return bool(row)

def _mark_processed(db: Session, source: str, entity: str, external_id: str, fp: str):
    db.execute(text("""
    INSERT INTO ingestion_log(id, source, entity, external_id, fingerprint, processed_at)
    VALUES (gen_random_uuid(), :s, :e, :x, :f, NOW())
    ON CONFLICT ON CONSTRAINT uq_ingest_once DO NOTHING
    """), {"s": source, "e": entity, "x": external_id, "f": fp})
    db.commit()

def upsert_fixtures(db: Session, staged_list):
    count = 0
    for m in staged_list:
        fp = sha256_json(m["data"])
        ext = m["external_id"]
        if _already_processed(db, m["source"], m["entity"], ext, fp):
            continue
        U.upsert_fixture(db, m)
        _mark_processed(db, m["source"], m["entity"], ext, fp)
        count += 1
    return count

def upsert_events(db: Session, staged_list):
    count = 0
    for m in staged_list:
        fp = sha256_json(m["data"])
        ext = m["external_id"]
        if _already_processed(db, m["source"], m["entity"], ext, fp):
            continue
        U.upsert_event(db, m)
        _mark_processed(db, m["source"], m["entity"], ext, fp)
        count += 1
    return count

def upsert_lineups(db: Session, staged_list):
    count = 0
    for m in staged_list:
        fp = sha256_json(m["data"])
        ext = m["external_id"]
        if _already_processed(db, m["source"], m["entity"], ext, fp):
            continue
        U.upsert_lineup(db, m)
        _mark_processed(db, m["source"], m["entity"], ext, fp)
        count += 1
    return count

def upsert_standings(db: Session, league_uuid, season_uuid, staged_list):
    count = 0
    for m in staged_list:
        fp = sha256_json(m["data"])
        ext = m["external_id"]
        if _already_processed(db, m["source"], m["entity"], ext, fp):
            continue
        U.upsert_standing(db, league_uuid, season_uuid, m)
        _mark_processed(db, m["source"], m["entity"], ext, fp)
        count += 1
    return count
