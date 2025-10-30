from fastapi import APIRouter, Query
from sqlalchemy import text
from ..deps import SessionLocal
from ..utils.dq import run_daily_suite
import asyncio

router = APIRouter(prefix="/admin/dq", tags=["admin.dq"])

@router.post("/run")
async def run(date: str = Query(..., description="YYYY-MM-DD")):
    db = SessionLocal()
    try:
        await run_daily_suite(db, date)
        return {"ok": True}
    finally:
        db.close()

@router.get("/metrics")
async def metrics(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT name, dimension, value, captured_at FROM dq_metrics ORDER BY captured_at DESC LIMIT :l"), {"l": limit}).fetchall()
        return [{"name": r[0], "dimension": r[1], "value": float(r[2]), "captured_at": str(r[3])} for r in rows]
    finally:
        db.close()

@router.get("/issues")
async def issues(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT severity, title, context, created_at FROM dq_issues ORDER BY created_at DESC LIMIT :l"), {"l": limit}).fetchall()
        return [{"severity": r[0], "title": r[1], "context": r[2], "created_at": str(r[3])} for r in rows]
    finally:
        db.close()
