from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db
from ...utils.fcm_sender import send_to_topic, send_to_token
import asyncio

router = APIRouter(tags=['notify'], prefix='/notify')

class NotifyBody(BaseModel):
    topic: str | None = None
    token: str | None = None
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    data: dict = Field(default_factory=dict)

@router.post('/test')
async def test_notify(b: NotifyBody):
    if not (b.topic or b.token):
        raise HTTPException(400, detail="topic or token required")
    data = b.data or {}
    data.setdefault('type', 'test')
    if b.topic:
        return await send_to_topic(b.topic, b.title, b.body, data)
    else:
        return await send_to_token(b.token, b.title, b.body, data)

class MatchNotifyBody(BaseModel):
    fixture_id: str
    home: str
    away: str
    league_id: str | None = None
    team_ids: list[str] | None = None

@router.post('/match_start')
async def match_start(b: MatchNotifyBody):
    title = f"{b.home} - {b.away} başladı"
    body = "Maç canlı! Anlık tahmin ve detaylar için dokunun."
    data = {"type": "match_start", "fixture_id": b.fixture_id}
    tasks = []
    # broadcast to league if provided
    if b.league_id:
        tasks.append(asyncio.create_task(send_to_topic(f"league:{b.league_id}", title, body, data)))
    # and to teams
    if b.team_ids:
        for tid in b.team_ids:
            tasks.append(asyncio.create_task(send_to_topic(f"team:{tid}", title, body, data)))
    # also to general kickoff
    tasks.append(asyncio.create_task(send_to_topic("kickoff", title, body, data)))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {"sent": len(results)}

@router.post('/prediction_ready')
async def prediction_ready(b: MatchNotifyBody):
    title = f"{b.home} - {b.away} tahmin güncellendi"
    body = "Anlık tahmini gör veya maç detayına git."
    data = {"type": "prediction_ready", "fixture_id": b.fixture_id}
    tasks = []
    if b.league_id:
        tasks.append(asyncio.create_task(send_to_topic(f"league:{b.league_id}", title, body, data)))
    if b.team_ids:
        for tid in b.team_ids:
            tasks.append(asyncio.create_task(send_to_topic(f"team:{tid}", title, body, data)))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {"sent": len(results)}
