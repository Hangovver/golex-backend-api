import asyncio, json, time
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..deps import SessionLocal
from ..utils.redis_pool import get_redis

async def _fixture_channels(db: Session, fixture_ext: str):
    # map external fixture id -> internal + league/team
    row = db.execute(text("SELECT id, league_id, home_team_id, away_team_id FROM fixtures WHERE id = :id"), {"id": fixture_ext}).fetchone()
    if not row: return []
    fid, lid, hid, aid = str(row[0]), str(row[1]), str(row[2]), str(row[3])
    return [f"room:fixture:{fid}", f"room:league:{lid}", f"room:team:{hid}", f"room:team:{aid}"]

async def run_push_bridge():
    r = await get_redis()
    while True:
        try:
            val = await r.brpop("golex:push:events", timeout=1)
            if not val:
                await asyncio.sleep(0.2); continue
            if isinstance(val, (list, tuple)):
                payload = json.loads(val[1])
            else:
                payload = json.loads(val)
            db: Session = SessionLocal()
            try:
                chans = await _fixture_channels(db, payload.get("fixture_ext"))
            finally:
                db.close()
            for ch in chans:
                await r.publish(ch, json.dumps(payload))
        except Exception:
            await asyncio.sleep(0.5)
