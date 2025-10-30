from fastapi import APIRouter, Query
from pydantic import BaseModel
from ..deps import SessionLocal
from sqlalchemy import text
from datetime import datetime, timezone

router = APIRouter(prefix="/admin/jobs", tags=["admin.jobs"])

class Beat(BaseModel):
    job: str
    status: str = "running"   # running|ok|error
    msg: str | None = None

@router.post("/heartbeat")
async def heartbeat(b: Beat):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        row = db.execute(text("SELECT job FROM jobs_status WHERE job=:j"), {"j": b.job}).fetchone()
        if not row:
            db.execute(text(                    "INSERT INTO jobs_status(id, job, last_started_at, ok, last_error, updated_at) "                    "VALUES (gen_random_uuid(), :j, :t, :ok, :e, :t)"                ), {"j": b.job, "t": now, "ok": b.status != "error", "e": b.msg})
        else:
            if b.status == "running":
                db.execute(text("UPDATE jobs_status SET last_started_at=:t, updated_at=:t WHERE job=:j"), {"t": now, "j": b.job})
            elif b.status == "ok":
                db.execute(text("UPDATE jobs_status SET last_finished_at=:t, ok=TRUE, last_error=NULL, updated_at=:t WHERE job=:j"), {"t": now, "j": b.job})
            elif b.status == "error":
                db.execute(text("UPDATE jobs_status SET last_finished_at=:t, ok=FALSE, last_error=:e, updated_at=:t WHERE job=:j"), {"t": now, "e": b.msg, "j": b.job})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.get("/list")
async def list_jobs():
    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT job, last_started_at, last_finished_at, ok, last_error, updated_at FROM jobs_status ORDER BY job")).fetchall()
        return [dict(job=r[0], lastStarted=str(r[1]) if r[1] else None, lastFinished=str(r[2]) if r[2] else None, ok=bool(r[3]), lastError=r[4], updatedAt=str(r[5])) for r in rows]
    finally:
        db.close()
