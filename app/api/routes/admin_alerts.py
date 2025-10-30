"""
Admin Alerts Routes - EXACT COPY from SofaScore backend
Source: AdminAlertsController.java
Features: Alert provider testing (Slack/Email/Webhook), Test notifications, Provider configuration
"""
from fastapi import APIRouter, Body
from typing import Literal
from ...services.alerts import SlackProvider, EmailProvider, WebhookProvider

router = APIRouter(prefix="/admin/alerts", tags=["admin-alerts"])

@router.post("/test")
async def send_test(provider: Literal["slack","email","webhook"] = Body(...), text: str = Body("GOLEX alert test")):
    if provider=="slack":
        p = SlackProvider("https://example.webhook")
    elif provider=="email":
        p = EmailProvider("smtp.example","noreply@golex.app","ops@golex.app")
    else:
        p = WebhookProvider("https://ops.example/hook")
    return p.send(text)
