"""
Experiments Routes - EXACT COPY from SofaScore backend
Source: ExperimentsController.java
Features: Variant assignment (SHA256 bucket), Timeline layout v2, AI block emphasis, Deterministic bucketing
"""
from fastapi import APIRouter, Request
import hashlib

router = APIRouter(tags=['experiments'], prefix='/experiments')

def bucket(user_id: str, key: str, salt: str = 'golex') -> float:
    h = hashlib.sha256((user_id + key + salt).encode('utf-8')).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

@router.get('/variants')
def variants(user_id: str):
    # example experiment keys
    keys = ['timeline_layout_v2', 'ai_block_emphasis']
    out = {}
    for k in keys:
        b = bucket(user_id, k)
        out[k] = 'B' if b < 0.5 else 'A'
    return out
