from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
try:
    from ..security.deps import get_db, get_current_user_optional
except Exception:
    def get_db(): return None
    def get_current_user_optional(): return {'id':'demo-user'}

router = APIRouter(tags=['favorites'], prefix='/favorites')

class FavChange(BaseModel):
    fixture_id: str
    op: str  # add|remove
    ts: int
    device_id: str

class SyncBody(BaseModel):
    changes: list[FavChange]

@router.post('/sync')
def sync(body: SyncBody, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    if not user: raise HTTPException(401, 'auth required')
    for c in sorted(body.changes, key=lambda x: x.ts):
        if c.op == 'add':
            db.execute(text("""INSERT INTO favorites(user_id, fixture_id, device_id, updated_at)
                               VALUES (:u, :f, :d, NOW())
                               ON CONFLICT (user_id, fixture_id) DO UPDATE SET device_id=:d, updated_at=NOW()"""),
                      {'u': user['id'], 'f': c.fixture_id, 'd': c.device_id})
        else:
            db.execute(text("DELETE FROM favorites WHERE user_id=:u AND fixture_id=:f"), {'u': user['id'], 'f': c.fixture_id})
    db.commit()
    rows = db.execute(text("SELECT fixture_id::text FROM favorites WHERE user_id=:u"), {'u': user['id']}).fetchall()
    return {'fixtures': [r[0] for r in rows]}
