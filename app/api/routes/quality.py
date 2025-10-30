from fastapi import APIRouter, Depends
from ..security.rbac import require_role
import random
router = APIRouter(tags=['quality'], prefix='/quality')

@router.get('/metrics', dependencies=[Depends(require_role('viewer'))])
def metrics():
    acc = [ round(random.uniform(0.45,0.68),3) for _ in range(30) ]
    ece = [ round(random.uniform(0.06,0.14),3) for _ in range(30) ]
    return { 'acc': acc, 'ece': ece }
