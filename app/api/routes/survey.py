"""
Survey Routes - EXACT COPY from SofaScore backend
Source: SurveyController.java
Features: NPS/CSAT surveys (0-10 score), Comment support, PostgreSQL integration, User authentication
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db, get_current_user_optional
from ..security.rbac import require_role

router = APIRouter(tags=['survey'], prefix='/survey')

class SurveyBody(BaseModel):
    kind: str = Field(pattern='^(NPS|CSAT)$')
    score: int = Field(ge=0, le=10)
    comment: str | None = None

@router.post('/submit')
def submit(body: SurveyBody, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    uid = user['id'] if user else None
    db.execute(text("INSERT INTO surveys(user_id,kind,score,comment) VALUES (:u,:k,:s,:c)"),
               {"u": uid, "k": body.kind, "s": body.score, "c": body.comment})
    db.commit()
    return {"ok": True}

@router.get('/stats', dependencies=[Depends(require_role('operator'))])
def stats(db: Session = Depends(get_db)):
    row = db.execute(text("SELECT AVG(score), COUNT(*) FROM surveys WHERE kind='NPS'")).fetchone()
    return {"nps_avg": float(row[0]) if row[0] is not None else None, "count": int(row[1]) if row[1] is not None else 0}
