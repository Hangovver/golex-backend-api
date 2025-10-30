from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...security.deps import get_db

router = APIRouter(tags=['notify'], prefix='/notify/topic')

class TopicBody(BaseModel):
    device_id: str = Field(min_length=4)
    topic: str = Field(min_length=3)

@router.post('/subscribe')
def subscribe(b: TopicBody, db: Session = Depends(get_db)):
    if not (b.topic.startswith('team:') or b.topic.startswith('league:')):
        raise HTTPException(400, detail='topic must be team:{id} or league:{id}')
    db.execute(text("INSERT INTO user_topic_subs(device_id, topic) VALUES (:d, :t) ON CONFLICT DO NOTHING"),
               {'d': b.device_id, 't': b.topic})
    db.commit()
    return {'ok': True}

@router.post('/unsubscribe')
def unsubscribe(b: TopicBody, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM user_topic_subs WHERE device_id=:d AND topic=:t"), {'d': b.device_id, 't': b.topic})
    db.commit()
    return {'ok': True}

@router.get('/list/{device_id}')
def list_topics(device_id: str, db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT topic FROM user_topic_subs WHERE device_id=:d ORDER BY created_at DESC"),
                      {'d': device_id}).fetchall()
    return {'topics': [r[0] for r in rows]}
