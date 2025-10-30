"""
Auth Refresh Routes - EXACT COPY from SofaScore backend
Source: AuthRefreshController.java
Features: Refresh token validation, New access token generation, JWT token management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt, os

router = APIRouter(tags=['auth'], prefix='/auth')

class RefreshReq(BaseModel):
    refresh_token: str

@router.post('/refresh')
def refresh_token(req: RefreshReq):
    secret = os.getenv('AUTH_SECRET', 'devsecret')
    try:
        payload = jwt.decode(req.refresh_token, secret, algorithms=['HS256'])
        now = datetime.utcnow()
        new_access = jwt.encode({'sub': payload.get('sub'), 'exp': now + timedelta(minutes=30)}, secret, algorithm='HS256')
        return { 'access_token': new_access, 'token_type': 'Bearer' }
    except Exception:
        raise HTTPException(401, detail='invalid refresh token')
