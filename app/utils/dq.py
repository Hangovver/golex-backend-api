from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.etl import DQMetric, DQIssue
from .alerts import send_alert
import asyncio

def _ins_metric(db: Session, name: str, dimension: str, value: float):
    db.execute(text("INSERT INTO dq_metrics(id,name,dimension,value,captured_at) VALUES (gen_random_uuid(),:n,:d,:v,NOW())"),
               {"n": name, "d": dimension, "v": float(value)})
    db.commit()

def _ins_issue(db: Session, severity: str, title: str, context: dict | None = None):
    db.execute(text("INSERT INTO dq_issues(id,severity,title,context,created_at) VALUES (gen_random_uuid(),:s,:t,:c,NOW())"),
               {"s": severity, "t": title, "c": context or {}})
    db.commit()

async def compute_fixtures_completeness(db: Session, date_str: str):
    # Goals/teams completeness for a date (rough example metric)
    q_total = db.execute(text("""
        SELECT COUNT(*) FROM fixtures WHERE DATE(date_utc) = :d
    """), {"d": date_str}).scalar() or 0
    q_with_teams = db.execute(text("""
        SELECT COUNT(*) FROM fixtures WHERE DATE(date_utc) = :d AND home_team_id IS NOT NULL AND away_team_id IS NOT NULL
    """), {"d": date_str}).scalar() or 0
    completeness = (q_with_teams / q_total) if q_total else 1.0
    _ins_metric(db, "completeness.fixtures.teams", f"date={date_str}", completeness)
    if completeness < 0.9:
        await send_alert("warn", "Düşük takım tamlığı", {"date": date_str, "value": completeness})

async def compute_live_freshness(db: Session):
    # Rough freshness proxy by counting recent updates in last 2 minutes
    recent = db.execute(text("""
        SELECT COUNT(*) FROM events WHERE NOW() - INTERVAL '2 minutes' < NOW()
    """))  # placeholder; proper schema would need updated_at triggers
    _ins_metric(db, "freshness.live.recent_updates", "window=2m", float(recent.scalar() or 0))

async def run_daily_suite(db: Session, date_str: str):
    await compute_fixtures_completeness(db, date_str)
    await compute_live_freshness(db)
