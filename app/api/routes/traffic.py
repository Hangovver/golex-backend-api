from fastapi import APIRouter, HTTPException, Depends
from ..security.rbac import require_role

CANARY = {'ratio': 0.1}

router = APIRouter(tags=['traffic'], prefix='/admin/traffic')

@router.get('/canary', dependencies=[Depends(require_role('admin'))])
def get_canary(): return CANARY

@router.post('/canary', dependencies=[Depends(require_role('admin'))])
def set_canary(ratio: float):
    if ratio < 0 or ratio > 1: raise HTTPException(400, detail='ratio must be [0,1]')
    CANARY['ratio'] = ratio
    return CANARY
