from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
import json, time
from .alert_routing import _send_via_provider

router = APIRouter(prefix="/admin/bridge", tags=["admin.bridge"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS push_queue(
        id SERIAL PRIMARY KEY,
        token TEXT,
        payload JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.commit()

@router.post("/emit-test")
def emit_test(event: str = "goal", fixture_id: str = "demo", provider: str | None = None, db: Session = Depends(get_db)):
    """Simulated critical event → enqueue to push_queue and (optional) route to provider (slack/webhook/email)."""
    _ensure(db)
    payload = {"type": event, "fixture_id": fixture_id, "ts": int(time.time())}
    # Fan-out to subscribed tokens (demo: we don't have FCM—queue tokens only)
    rows = db.execute(text("SELECT token FROM push_subs")).fetchall()
    for r in rows:
        db.execute(text("INSERT INTO push_queue(token, payload) VALUES(:t,:p)"), {"t": r[0], "p": json.dumps(payload)})
    db.commit()
    # Operator notification
    if provider:
        _send_via_provider("slack", {"webhook_url": provider} if provider.startswith("http") else {"url": provider}, f"Event {event}", json.dumps(payload), "info")
    return {"enqueued": len(rows)}

@router.get("/queue")
def queue(limit: int = 50, db: Session = Depends(get_db)):
    _ensure(db)
    rows = db.execute(text("SELECT id, token, payload, created_at FROM push_queue ORDER BY id DESC LIMIT :lim"), {"lim": limit}).fetchall()
    return {"items": [{"id": r[0], "token": r[1], "payload": r[2], "created_at": r[3].isoformat() if r[3] else None} for r in rows]}
