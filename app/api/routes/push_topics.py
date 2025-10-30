from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..security.deps import get_db, get_current_user_optional

router = APIRouter(tags=['push'], prefix='/push')

class RegisterBody(BaseModel):
    token: str = Field(min_length=8)
    device_id: str = Field(min_length=4)
    platform: str = Field(default='android')

@router.post('/token/register')
def register_token(b: RegisterBody, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    uid = user['id'] if user else None
    db.execute(text("""INSERT INTO user_push_tokens(user_id, device_id, token, platform)
                      VALUES (:u, :d, :t, :p)
                      ON CONFLICT (token) DO UPDATE SET user_id=COALESCE(EXCLUDED.user_id, user_push_tokens.user_id),
                                                       device_id=EXCLUDED.device_id,
                                                       platform=EXCLUDED.platform,
                                                       updated_at=NOW()"""),
               {'u': uid, 'd': b.device_id, 't': b.token, 'p': b.platform})
    db.commit()
    return {'ok': True}

def _validate_topic(topic: str):
    if not (topic.startswith('team:') or topic.startswith('league:') or topic in ('goals','kickoff','final')):
        raise HTTPException(400, detail='invalid topic')
    return topic

class TopicBody(BaseModel):
    topic: str
    token: str | None = None
    device_id: str | None = None

@router.post('/topic/subscribe')
def subscribe(b: TopicBody, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    topic = _validate_topic(b.topic)
    uid = user['id'] if user else None
    if not (uid or b.token or b.device_id):
        raise HTTPException(400, detail='user or token/device required')
    db.execute(text("""INSERT INTO user_topic_subscriptions(user_id, token, device_id, topic)
                      VALUES (:u, :t, :d, :topic)
                      ON CONFLICT ON CONSTRAINT uniq_uts DO NOTHING"""),
               {'u': uid, 't': b.token, 'd': b.device_id, 'topic': topic})
    db.commit()
    return {'ok': True}

@router.post('/topic/unsubscribe')
def unsubscribe(b: TopicBody, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    topic = _validate_topic(b.topic)
    uid = user['id'] if user else None
    if not (uid or b.token or b.device_id):
        raise HTTPException(400, detail='user or token/device required')
    q = "DELETE FROM user_topic_subscriptions WHERE topic=:topic AND ((:u IS NOT NULL AND user_id=:u) OR (:t IS NOT NULL AND token=:t) OR (:d IS NOT NULL AND device_id=:d))"
    db.execute(text(q), {'u': uid, 't': b.token, 'd': b.device_id, 'topic': topic})
    db.commit()
    return {'ok': True}

@router.get('/topics')
def list_topics(db: Session = Depends(get_db), user=Depends(get_current_user_optional), token: str | None = Query(None), device_id: str | None = Query(None)):
    uid = user['id'] if user else None
    if not (uid or token or device_id):
        raise HTTPException(400, detail='user or token/device required')
    q = "SELECT topic FROM user_topic_subscriptions WHERE (:u IS NOT NULL AND user_id=:u) OR (:t IS NOT NULL AND token=:t) OR (:d IS NOT NULL AND device_id=:d) ORDER BY created_at DESC"
    rows = db.execute(text(q), {'u': uid, 't': token, 'd': device_id}).fetchall()
    return {'topics': [r[0] for r in rows]}
