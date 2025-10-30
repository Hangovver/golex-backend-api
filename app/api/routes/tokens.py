from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['notify'], prefix='/notify/token')

class TokenBody(BaseModel):
    device_id: str = Field(min_length=4)
    token: str = Field(min_length=8)
    platform: str = Field(default='android')

@router.post('/register')
def register(b: TokenBody, db: Session = Depends(get_db)):
    db.execute(text("""INSERT INTO user_device_tokens(device_id, token, platform, created_at, updated_at)
                      VALUES (:d, :t, :p, NOW(), NOW())
                      ON CONFLICT (device_id, token) DO UPDATE SET platform=:p, updated_at=NOW()"""),
               {'d': b.device_id, 't': b.token, 'p': b.platform})
    db.commit()
    return {'ok': True}

@router.post('/unregister')
def unregister(b: TokenBody, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM user_device_tokens WHERE device_id=:d AND token=:t"), {'d': b.device_id, 't': b.token})
    db.commit()
    return {'ok': True}
