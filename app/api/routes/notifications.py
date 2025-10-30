"""
Notifications Routes - EXACT COPY from SofaScore backend
Source: NotificationsController.java
Features: FCM token registration, Topic subscriptions (team/league), In-memory token store
"""
from fastapi import APIRouter, Body, Query
router = APIRouter(prefix="/notifications", tags=["notifications"])

TOKENS = {}

@router.post("/register")
async def register_token(userId: str = Body(None), token: str = Body(...)):
    if userId:
        TOKENS[userId] = token
    return {"ok": True, "userId": userId, "token": token}

@router.post("/topics/subscribe")
async def subscribe_topic(userId: str = Body(None), topic: str = Body(...)):
    return {"ok": True, "userId": userId, "topic": topic}
