from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..deps import SessionLocal
from sqlalchemy import text

router = APIRouter(prefix="/admin/ml", tags=["admin.ml"])

class StartReq(BaseModel):
    runId: str
    modelName: str
    modelVersion: str | None = None
    params: dict | None = None
    artifactUri: str | None = None

@router.post("/runs/start")
async def start(req: StartReq):
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO ml_runs(id, run_id, model_name, model_version, params, metrics, status, artifact_uri, created_at)
            VALUES (gen_random_uuid(), :rid, :name, :ver, :params, '{}'::jsonb, 'running', :a, NOW())
            ON CONFLICT (run_id) DO NOTHING
        """), {"rid": req.runId, "name": req.modelName, "ver": req.modelVersion, "params": req.params, "a": req.artifactUri})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

class LogReq(BaseModel):
    runId: str
    metrics: dict

@router.post("/runs/log")
async def log(req: LogReq):
    db = SessionLocal()
    try:
        db.execute(text("UPDATE ml_runs SET metrics = COALESCE(metrics,'{}'::jsonb) || :m::jsonb WHERE run_id=:rid"),
                  {"m": req.metrics, "rid": req.runId})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.post("/runs/finish")
async def finish(runId: str, status: str = Query("finished")):
    if status not in ("finished","failed"): status = "finished"
    db = SessionLocal()
    try:
        db.execute(text("UPDATE ml_runs SET status=:s WHERE run_id=:rid"), {"s": status, "rid": runId})
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@router.get("/runs")
async def list_runs(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT run_id, model_name, model_version, status, metrics, artifact_uri, created_at FROM ml_runs ORDER BY created_at DESC LIMIT :l"),
                          {"l": limit}).fetchall()
        return [dict(runId=r[0], modelName=r[1], modelVersion=r[2], status=r[3], metrics=r[4], artifactUri=r[5], createdAt=str(r[6])) for r in rows]
    finally:
        db.close()
