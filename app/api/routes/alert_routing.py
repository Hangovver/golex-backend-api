from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..deps import get_db
import json, requests

router = APIRouter(prefix="/admin/alerts", tags=["admin.alerts"])

def _ensure(db: Session):
    db.execute(text('''CREATE TABLE IF NOT EXISTS alert_providers(
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        kind TEXT CHECK (kind IN ('slack','email','webhook')),
        config JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    )'''))
    db.commit()

@router.post("/providers")
def upsert_provider(name: str, kind: str, config: dict, db: Session = Depends(get_db)):
    _ensure(db)
    if kind not in ("slack","email","webhook"):
        raise HTTPException(status_code=400, detail="invalid kind")
    db.execute(text("INSERT INTO alert_providers(name,kind,config) VALUES(:n,:k,:c) ON CONFLICT (name) DO UPDATE SET kind=:k, config=:c"),
               {"n": name, "k": kind, "c": json.dumps(config)})
    db.commit()
    return {"ok": True}

@router.get("/providers")
def list_providers(db: Session = Depends(get_db)):
    _ensure(db)
    rows = db.execute(text("SELECT id,name,kind,config FROM alert_providers ORDER BY id DESC")).fetchall()
    return {"providers": [{"id": r[0], "name": r[1], "kind": r[2], "config": r[3]} for r in rows]}

def _send_via_provider(kind: str, config: dict, title: str, body: str, severity: str = "info"):
    if kind == "slack":
        url = config.get("webhook_url")
        if not url: 
            raise RuntimeError("slack webhook_url missing")
        payload = {"text": f"*{title}*\n[{severity}] {body}"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass
    elif kind == "webhook":
        url = config.get("url")
        headers = config.get("headers") or {}
        payload = {"title": title, "body": body, "severity": severity}
        try:
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception:
            pass
    elif kind == "email":
        # Placeholder: in prod, wire SMTP here.
        # For demo we just no-op.
        pass

@router.post("/send")
def send_alert(provider: str, title: str, body: str, severity: str = "info", db: Session = Depends(get_db)):
    _ensure(db)
    row = db.execute(text("SELECT kind, config FROM alert_providers WHERE name=:n"), {"n": provider}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    kind, config = row[0], row[1] or {}
    _send_via_provider(kind, config, title, body, severity)
    return {"ok": True}
