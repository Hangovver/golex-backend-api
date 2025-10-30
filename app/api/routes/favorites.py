from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db

router = APIRouter(tags=['favorites'], prefix='/favorites')

class FavBody(BaseModel):
    device_id: str = Field(min_length=4)
    team_id: str = Field(min_length=1)

@router.post('/toggle')
def toggle_favorite(b: FavBody, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT 1 FROM user_device_favorites WHERE device_id=:d AND team_id=:t"),
                      {'d': b.device_id, 't': b.team_id}).fetchall()
    if rows:
        db.execute(text("DELETE FROM user_device_favorites WHERE device_id=:d AND team_id=:t"), {'d': b.device_id, 't': b.team_id})
        db.commit()
        return {'favorited': False}
    else:
        db.execute(text("INSERT INTO user_device_favorites(device_id, team_id) VALUES (:d, :t) ON CONFLICT DO NOTHING"),
                   {'d': b.device_id, 't': b.team_id})
        db.commit()
        return {'favorited': True}

@router.get('/list/{device_id}')
def list_favorites(device_id: str, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT team_id FROM user_device_favorites WHERE device_id=:d ORDER BY created_at DESC"),
                      {'d': device_id}).fetchall()
    return {'teams': [r[0] for r in rows]}


from fastapi import Body
class FavSetBody(FavBody):
    favorited: bool = Field(..., description="True to ensure favorite exists; False to ensure it's removed")

@router.post('/set')
def set_favorite(b: FavSetBody, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT 1 FROM user_device_favorites WHERE device_id=:d AND team_id=:t"),
                     {'d': b.device_id, 't': b.team_id}).fetchone()
    if b.favorited and not row:
        db.execute(text("INSERT INTO user_device_favorites(device_id, team_id) VALUES (:d, :t) ON CONFLICT DO NOTHING"),
                   {'d': b.device_id, 't': b.team_id})
        db.commit()
        return {'favorited': True}
    if (not b.favorited) and row:
        db.execute(text("DELETE FROM user_device_favorites WHERE device_id=:d AND team_id=:t"),
                   {'d': b.device_id, 't': b.team_id})
        db.commit()
        return {'favorited': False}
    return {'favorited': bool(row)}
