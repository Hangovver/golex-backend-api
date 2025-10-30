from fastapi import APIRouter, Depends
from ..security.rbac import require_role
import random

router = APIRouter(tags=['experiments'], prefix='/experiments')

@router.get('/report', dependencies=[Depends(require_role('operator'))])
def report():
    # stubbed conversion metrics
    def fake():
        return { 'impr': random.randint(500,5000), 'clicks': random.randint(100,1000), 'conv': round(random.uniform(0.05,0.25),3) }
    return { 'timeline_layout_v2': { 'A': fake(), 'B': fake() },
             'ai_block_emphasis': { 'A': fake(), 'B': fake() } }
