from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
from ..security.rbac import require_role

router = APIRouter(tags=['privacy'], prefix='/privacy')

@router.get('/report', dependencies=[Depends(require_role('operator'))])
def report(db: Session = Depends(get_db)):
    total = db.execute(text("SELECT COUNT(*) FROM dsr_requests")).scalar() or 0
    exp7 = db.execute(text("SELECT COUNT(*) FROM dsr_requests WHERE kind='export' AND created_at >= NOW() - INTERVAL '7 days'")).scalar() or 0
    del7 = db.execute(text("SELECT COUNT(*) FROM dsr_requests WHERE kind='delete' AND created_at >= NOW() - INTERVAL '7 days'")).scalar() or 0
    optout = 0
    return {"users_total": None, "dsr_total": int(total), "dsr_export_7d": int(exp7), "dsr_delete_7d": int(del7), "opt_out_notifications": int(optout)}
