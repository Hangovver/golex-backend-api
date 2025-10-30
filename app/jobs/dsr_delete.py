import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import SessionLocal

log = logging.getLogger("golex")

def run_once():
    db: Session = SessionLocal()
    try:
        rows = db.execute(text("SELECT id, user_id FROM dsr_requests WHERE kind='delete' AND status='received'"))
        for r in rows:
            uid = r[1]
            db.execute(text("DELETE FROM favorites WHERE user_id=:u"), {'u': uid})
            db.execute(text("UPDATE dsr_requests SET status='done' WHERE id=:id"), {'id': r[0]})
            log.info("DSR delete executed for user %s", uid)
        db.commit()
    finally:
        db.close()
