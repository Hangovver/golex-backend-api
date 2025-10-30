from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db, get_current_user_optional

router = APIRouter(tags=['consent'], prefix='/consent')

class Consent(BaseModel):
    push: bool | None = None
    analytics: bool | None = None

@router.get('')
def get(db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    uid = user['id'] if user else None
    if not uid: return {'push': True, 'analytics': False}
    row = db.execute(text("SELECT push,analytics FROM user_consents WHERE user_id=:u"), {'u': uid}).fetchone()
    if row: return {'push': bool(row[0]), 'analytics': bool(row[1])}
    return {'push': True, 'analytics': False}

@router.post('')
def set_c(body: Consent, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    uid = user['id'] if user else None
    if not uid: return {'ok': False, 'reason': 'auth required'}
    db.execute(text("""INSERT INTO user_consents(user_id,push,analytics)
                       VALUES (:u, COALESCE(:p, TRUE), COALESCE(:a, FALSE))
                       ON CONFLICT (user_id) DO UPDATE SET
                         push = COALESCE(:p, user_consents.push),
                         analytics = COALESCE(:a, user_consents.analytics),
                         updated_at = NOW()"""),
               {'u': uid, 'p': body.push, 'a': body.analytics})
    db.commit()
    return {'ok': True}
