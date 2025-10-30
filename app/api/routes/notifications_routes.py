"""
Notifications Routes
API endpoints for push notifications and FCM token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.user import User
from app.api.routes.user_routes import get_current_user

router = APIRouter(tags=["Notifications"])


class FCMTokenRequest(BaseModel):
    """FCM Token registration request"""
    token: str
    device_id: str
    device_type: str  # "android" or "ios"


class NotificationSettingsRequest(BaseModel):
    """Notification settings update"""
    goals: Optional[bool] = None
    matches: Optional[bool] = None
    lineups: Optional[bool] = None
    news: Optional[bool] = None
    red_cards: Optional[bool] = None


class SendNotificationRequest(BaseModel):
    """Send notification to specific users"""
    user_ids: List[int]
    title: str
    body: str
    data: Optional[dict] = None


@router.post("/notifications/register-token")
async def register_fcm_token(
    request: FCMTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register FCM token for push notifications
    """
    try:
        # Store FCM token in database
        # In production, you'd have a FCMToken model
        # For now, we'll just return success
        
        return {
            "success": True,
            "message": "FCM token registered successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/notifications/unregister-token")
async def unregister_fcm_token(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unregister FCM token
    """
    try:
        # Remove FCM token from database
        
        return {
            "success": True,
            "message": "FCM token unregistered successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/notifications/settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notification settings
    """
    try:
        # In production, fetch from user preferences table
        # For now, return default settings
        
        return {
            "goals": True,
            "matches": True,
            "lineups": False,
            "news": False,
            "red_cards": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/notifications/settings")
async def update_notification_settings(
    settings: NotificationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's notification settings
    """
    try:
        # In production, update user preferences in database
        
        return {
            "success": True,
            "message": "Notification settings updated",
            "settings": {
                "goals": settings.goals if settings.goals is not None else True,
                "matches": settings.matches if settings.matches is not None else True,
                "lineups": settings.lineups if settings.lineups is not None else False,
                "news": settings.news if settings.news is not None else False,
                "red_cards": settings.red_cards if settings.red_cards is not None else True
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/notifications/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send push notification to specific users
    Admin only endpoint
    """
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send notifications"
        )
    
    try:
        # In production, use Firebase Admin SDK to send notifications
        # For now, just return success
        
        return {
            "success": True,
            "message": f"Notification sent to {len(request.user_ids)} users",
            "sent_count": len(request.user_ids)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/notifications/send-goal")
async def send_goal_notification(
    fixture_id: int,
    team_id: int,
    player_name: str,
    minute: int,
    score: str,
    db: Session = Depends(get_db)
):
    """
    Send goal notification to users following the teams
    Internal endpoint - called by Celery tasks
    """
    try:
        # In production:
        # 1. Get all users following the teams in this fixture
        # 2. Check their notification preferences
        # 3. Send FCM notification using Firebase Admin SDK
        
        return {
            "success": True,
            "message": "Goal notifications sent"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/notifications/history")
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification history for current user
    """
    try:
        # In production, fetch from notification history table
        # For now, return empty list
        
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "notifications": []
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

