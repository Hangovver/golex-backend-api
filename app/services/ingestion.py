import asyncio
from datetime import datetime, timezone

STATE = {"runs":0, "last_run": None, "last_ok": None}

async def run_ingestion_loop():
    while True:
        STATE["runs"] += 1
        STATE["last_run"] = datetime.now(timezone.utc).isoformat()
        # demo: assume ok
        STATE["last_ok"] = STATE["last_run"]
        await asyncio.sleep(15)
