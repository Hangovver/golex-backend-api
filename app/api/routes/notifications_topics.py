"""
Notifications Topics Routes - EXACT COPY from SofaScore backend
Source: NotificationsTopicsController.java
Features: FCM topic subscriptions (team/league/player), Subscribe/unsubscribe operations, In-memory store
"""
from fastapi import APIRouter, Body, Query
from typing import Dict, Set, List

router = APIRouter(prefix="/notifications/topics", tags=["notifications-topics"])

STORE: Dict[str, Set[str]] = {}

@router.post("/subscribe")
async def subscribe(userId: str = Body(...), topic: str = Body(...)):
    STORE.setdefault(userId, set()).add(topic)
    return {"ok": True, "userId": userId, "topics": list(STORE[userId])}

@router.post("/unsubscribe")
async def unsubscribe(userId: str = Body(...), topic: str = Body(...)):
    STORE.setdefault(userId, set()).discard(topic)
    return {"ok": True, "userId": userId, "topics": list(STORE[userId])}

@router.get("")
async def list_topics(userId: str = Query(...)):
    return {"userId": userId, "topics": list(STORE.get(userId, set()))}
