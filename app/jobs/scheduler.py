from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import os, asyncio, logging

sched = AsyncIOScheduler()

async def job_live():
    logging.getLogger("golex").info("job_live tick")

async def job_upcoming():
    logging.getLogger("golex").info("job_upcoming tick")

async def job_standings():
    logging.getLogger("golex").info("job_standings tick")

def start_scheduler():
    if os.getenv('ENABLE_SCHEDULER','false').lower() != 'true':
        return None
    sched.add_job(lambda: asyncio.create_task(job_live()), 'interval', seconds=15, id='live')
    sched.add_job(lambda: asyncio.create_task(job_upcoming()), 'interval', minutes=10, id='upcoming')
    sched.add_job(lambda: asyncio.create_task(job_standings()), 'cron', hour=3, id='standings')
    sched.add_job(lambda: asyncio.create_task(job_prewarm()), 'cron', hour=5, id='prewarm_nextday')
    sched.add_job(lambda: asyncio.create_task(job_dsr_delete()), 'cron', minute='*/15', id='dsr_delete')
    sched.start()
    return sched


async def job_prewarm():
    logging.getLogger("golex").info("job_prewarm next-day fixtures")



async def job_dsr_delete():
    import asyncio
    from .dsr_delete import run_once
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_once)
