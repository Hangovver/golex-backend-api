from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
from pathlib import Path
import json, hashlib

router = APIRouter(tags=['predictions'], prefix='/predictions')

BASE = Path(__file__).resolve().parents[2] / 'model'

def _load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def _bundle(path_name: str):
    p = BASE / path_name
    if not p.exists():
        return None
    return _load_json(p)

def _prob_from_seed(seed: str):
    h = int(hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8], 16)
    a = (h % 1000) / 1000.0
    b = ((h // 1000) % 1000) / 1000.0
    c = ((h // 1000000) % 1000) / 1000.0
    total = a + b + c + 1e-6
    return {'home': a/total, 'draw': b/total, 'away': c/total}

def _read_ab_cfg(db: Session):
    row = db.execute(text("SELECT perc_b, canary_version FROM ab_config WHERE id=1")).fetchone()
    if not row: return 10.0, None
    return float(row[0]), row[1]

def _assign_bucket(db: Session, device_id: str, perc_b: float) -> str:
    # try from table
    row = db.execute(text("SELECT bucket FROM ab_assignments WHERE device_id=:d"), {'d': device_id}).fetchone()
    if row: return row[0]
    # deterministic new assign
    import hashlib
    h = int(hashlib.sha1(device_id.encode('utf-8')).hexdigest()[:8], 16) % 10000
    threshold = int(perc_b * 100)
    bucket = 'B' if h < threshold else 'A'
    db.execute(text("INSERT INTO ab_assignments(device_id, bucket) VALUES (:d, :b) ON CONFLICT (device_id) DO NOTHING"),
               {'d': device_id, 'b': bucket})
    db.commit()
    return bucket

@router.get('/ab/{fixture_id}')
def predict_ab(fixture_id: str, device_id: str = Query(..., min_length=4), db: Session = Depends(get_db)):
    perc_b, canary_v = _read_ab_cfg(db)
    bucket = _assign_bucket(db, device_id, perc_b)

    if bucket == 'A':
        reg = _bundle('registry.json') or {}
        prod_ver = reg.get('version', '0.0.0')
        prob = _prob_from_seed(f'prod:{prod_ver}:{fixture_id}')
        return {'fixture_id': fixture_id, 'bucket': 'A', 'version': prod_ver, 'prob': prob}
    else:
        # Prefer actual canary bundle if exists, else use canary_v seed, else '-canary' suffix
        can_bundle = _bundle('model_canary.json')
        can_ver = (can_bundle or {}).get('version') if can_bundle else (canary_v or 'canary')
        prob = _prob_from_seed(f'canary:{can_ver}:{fixture_id}')
        return {'fixture_id': fixture_id, 'bucket': 'B', 'version': can_ver, 'prob': prob}
