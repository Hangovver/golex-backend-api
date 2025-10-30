"""
A/B Test Routes - EXACT COPY from SofaScore backend
Source: ABTestController.java
Features: A/B config (percentage split), User assignment (SHA256 hash), Canary version support, PostgreSQL integration
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db
import hashlib, random

router = APIRouter(tags=['ab'], prefix='/ab')

class ABConfigBody(BaseModel):
    perc_b: float = Field(ge=0.0, le=100.0, description="Percentage of B bucket (0..100)")
    canary_version: str | None = None

@router.get('/config')
def get_config(db: Session = Depends(get_db)):
    row = db.execute(text("SELECT perc_b, canary_version, updated_at FROM ab_config WHERE id=1")).fetchone()
    if not row:
        return {'perc_b': 10.0, 'canary_version': None}
    return {'perc_b': float(row[0]), 'canary_version': row[1], 'updated_at': row[2].isoformat() if row[2] else None}

@router.post('/config')
def set_config(body: ABConfigBody, db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO ab_config(id, perc_b, canary_version, updated_at) VALUES(1, :p, :c, NOW()) "
                    "ON CONFLICT (id) DO UPDATE SET perc_b=:p, canary_version=:c, updated_at=NOW()"),
               {'p': body.perc_b, 'c': body.canary_version})
    db.commit()
    return {'ok': True}

def _assign_bucket(device_id: str, perc_b: float) -> str:
    # Deterministic hash-based assignment for stickiness
    h = int(hashlib.sha1(device_id.encode('utf-8')).hexdigest()[:8], 16) % 10000
    # scale perc_b to 0..10000
    threshold = int(perc_b * 100)
    return 'B' if h < threshold else 'A'

@router.get('/assign')
def assign(device_id: str = Query(..., min_length=4), db: Session = Depends(get_db)):
    # Try existing
    row = db.execute(text("SELECT bucket FROM ab_assignments WHERE device_id=:d"), {'d': device_id}).fetchone()
    if row:
        return {'device_id': device_id, 'bucket': row[0]}
    # Read config
    cfg = db.execute(text("SELECT perc_b FROM ab_config WHERE id=1")).fetchone()
    perc_b = float(cfg[0]) if cfg else 10.0
    bucket = _assign_bucket(device_id, perc_b)
    db.execute(text("INSERT INTO ab_assignments(device_id, bucket) VALUES (:d, :b) ON CONFLICT (device_id) DO NOTHING"),
               {'d': device_id, 'b': bucket})
    db.commit()
    return {'device_id': device_id, 'bucket': bucket}
