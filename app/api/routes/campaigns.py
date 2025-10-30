from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ...utils.fcm_sender import send_to_topic
import asyncio

router = APIRouter(tags=['notify'], prefix='/notify/campaign')

class CampaignBody(BaseModel):
    topics: list[str] = Field(min_items=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    data: dict = Field(default_factory=dict)

@router.post('/send')
async def send_campaign(b: CampaignBody):
    tasks = []
    for t in b.topics:
        tasks.append(asyncio.create_task(send_to_topic(t, b.title, b.body, dict(b.data))))
    res = await asyncio.gather(*tasks, return_exceptions=True)
    ok = sum(1 for r in res if not isinstance(r, Exception))
    return {"requested": len(b.topics), "ok": ok}
