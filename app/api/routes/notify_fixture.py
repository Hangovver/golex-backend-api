from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
from ...utils.fcm_sender import send_to_topic, send_to_token
import asyncio

router = APIRouter(tags=['notify'], prefix='/notify/fixture')

class FixtureTargetBody(BaseModel):
    fixture_id: str = Field(min_length=1)
    home: str
    away: str
    league_id: str | None = None
    team_ids: list[str] | None = None
    event: str = Field(description="kickoff|goal|final|prediction", regex="^(kickoff|goal|final|prediction)$")
    respect_prefs: bool = True

async def _broadcast_topics(b: FixtureTargetBody):
    title_map = {
        'kickoff': f"{'{home}'} - {'{away}'} başladı",
        'goal':    f"{'{home}'} - {'{away}'} gol oldu",
        'final':   f"{'{home}'} - {'{away}'} bitti",
        'prediction': f"{'{home}'} - {'{away}'} tahmin güncellendi",
    }
    title = title_map[b.event].format(home=b.home, away=b.away)
    body = "Detaylar için dokunun."
    data = {"type": b.event, "fixture_id": b.fixture_id, "home_team": (b.team_ids or [None])[0], "away_team": (b.team_ids or [None])[1] if b.team_ids and len(b.team_ids)>1 else None}
    tasks = []
    if b.league_id:
        tasks.append(asyncio.create_task(send_to_topic(f"league:{b.league_id}", title, body, data)))
    if b.team_ids:
        for tid in b.team_ids:
            tasks.append(asyncio.create_task(send_to_topic(f"team:{tid}", title, body, data)))
    if not tasks:
        raise HTTPException(400, detail="no topics derived from request")
    await asyncio.gather(*tasks, return_exceptions=True)
    return {"mode": "topic", "count": len(tasks)}

async def _send_per_token(db: Session, b: FixtureTargetBody):
    # Build candidate devices from topics
    topics = []
    if b.league_id:
        topics.append(f"league:{b.league_id}")
    if b.team_ids:
        topics.extend([f"team:{t}" for t in b.team_ids])

    if not topics:
        raise HTTPException(400, detail="no topics derived from request")

    # SQL: devices subscribed to any of topics
    rows = db.execute(text("""
        SELECT DISTINCT tkn.device_id, tkn.token
        FROM user_topic_subs uts
        JOIN user_device_tokens tkn ON tkn.device_id = uts.device_id
        LEFT JOIN user_notification_prefs p ON p.device_id = tkn.device_id
        WHERE uts.topic = ANY(:topics)
    """), {'topics': topics}).fetchall()

    # Filter by prefs
    good = []
    for r in rows:
        device_id, token = r[0], r[1]
        if b.respect_prefs:
            pref = db.execute(text("SELECT kickoff, goals, final, predictions FROM user_notification_prefs WHERE device_id=:d"), {'d': device_id}).fetchone()
            if pref:
                if b.event=='kickoff' and not pref[0]: continue
                if b.event=='goal' and not pref[1]: continue
                if b.event=='final' and not pref[2]: continue
                if b.event=='prediction' and not pref[3]: continue
        good.append(token)

    if not good:
        return {"mode": "per-token", "sent": 0}

    title_map = {
        'kickoff': f"{'{home}'} - {'{away}'} başladı",
        'goal':    f"{'{home}'} - {'{away}'} gol oldu",
        'final':   f"{'{home}'} - {'{away}'} bitti",
        'prediction': f"{'{home}'} - {'{away}'} tahmin güncellendi",
    }
    title = title_map[b.event].format(home=b.home, away=b.away)
    body = "Detaylar için dokunun."
    data = {"type": b.event, "fixture_id": b.fixture_id, "home_team": (b.team_ids or [None])[0], "away_team": (b.team_ids or [None])[1] if b.team_ids and len(b.team_ids)>1 else None}
    # Send in batches
    tasks = [asyncio.create_task(send_to_token(tok, title, body, data)) for tok in good]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    ok = sum(1 for r in res if not isinstance(r, Exception))
    return {"mode": "per-token", "requested": len(good), "sent": ok}

@router.post('/targeted')
async def targeted(b: FixtureTargetBody, db: Session = Depends(get_db)):
    if b.respect_prefs:
        return await _send_per_token(db, b)
    else:
        return await _broadcast_topics(b)
