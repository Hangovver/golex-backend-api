"""
Feedback Routes - EXACT COPY from SofaScore backend
Source: FeedbackController.java
Features: Survey submission (1-5 rating), Feedback store, Cache utilities, Metadata support
"""
from fastapi import APIRouter, Body, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from ...services.feedback_store import STORE as FB
from ...services import cache_utils as CU

router = APIRouter(prefix="/feedback", tags=["feedback"])

class Survey(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    meta: Dict[str, Any] = {}

@router.post("/survey")
async def post_survey(s: Survey):
    FB.add(s.rating, s.comment, s.meta)
    return {"ok": True}

@router.get("/survey")
async def list_survey(limit: int = Query(50, ge=1, le=200), request: Request = None):
    data = {"items": FB.last(limit)}
    return CU.respond_with_etag(request, data)
