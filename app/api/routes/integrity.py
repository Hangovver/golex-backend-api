from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=['integrity'], prefix='/integrity')

class VerifyReq(BaseModel):
    token: str

@router.post('/verify')
def verify(req: VerifyReq):
    # TODO: call Google Play Integrity API; here we only validate presence
    ok = bool(req.token and len(req.token) > 10)
    return { 'ok': ok, 'advice': 'Server-side verification with Google API is recommended.' }
