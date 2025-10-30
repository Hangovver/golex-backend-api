from fastapi import APIRouter, Body
from typing import Dict, Any
from ...services import feature_flags as FF

router = APIRouter(prefix="/flags", tags=["feature-flags"])

@router.get("")
async def get_flags():
    return FF.get_all()

@router.post("")
async def set_flags(patch: Dict[str, Any] = Body(...)):
    return FF.update(patch)
