from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db, get_current_user_optional

router = APIRouter(tags=['favorites'], prefix='/favorites')

@router.get('/summary')
def summary(db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    if not user: raise HTTPException(401, detail='auth required')
    row = db.execute(text("SELECT COALESCE(MAX(EXTRACT(EPOCH FROM updated_at))::bigint,0), COUNT(*) FROM favorites WHERE user_id=:u"), {"u": user['id']}).fetchone()
    return { "version": int(row[0]), "count": int(row[1]) }
