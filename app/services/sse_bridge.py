import asyncio, time
from typing import List, Dict
from .alerts import SlackProvider
from .metrics import inc

STATE = {"running": False, "room": None, "sent": 0, "last_ts": None}
QUEUE: asyncio.Queue = asyncio.Queue()

async def start(room: str = "fixture:1001"):
    if STATE["running"]: return
    STATE.update({"running": True, "room": room, "sent": 0, "last_ts": None})
    asyncio.create_task(_loop())

async def stop():
    STATE["running"] = False

async def inject(event: Dict):
    # event: {"type":"goal","fixtureId":"1001","team":"HOME","player":"X"}
    await QUEUE.put(event)

async def _loop():
    sp = SlackProvider("https://example.webhook")
    while STATE["running"]:
        try:
            ev = await asyncio.wait_for(QUEUE.get(), timeout=5.0)
            txt = f"[{ev.get('type','event').upper()}] fixture {ev.get('fixtureId','?')} :: {ev}"
            sp.send(txt)  # demo: no-op
            inc("sse_bridge_forwarded_total")
            STATE["sent"] += 1
            STATE["last_ts"] = time.time()
        except asyncio.TimeoutError:
            # heartbeat
            inc("sse_bridge_heartbeat_total")
            continue
