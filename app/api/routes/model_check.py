from fastapi import APIRouter, Query
from pathlib import Path
import json

router = APIRouter(tags=['model'], prefix='/model')

def _read_registry():
    p = Path(__file__).resolve().parents[2] / 'model' / 'registry.json'
    return json.loads(p.read_text(encoding='utf-8'))

def _cmp(a: str, b: str) -> int:
    def parse(s): return [int(x) for x in s.split('.') if x.isdigit()]
    pa, pb = parse(a), parse(b)
    for i in range(max(len(pa), len(pb))):
        va = pa[i] if i < len(pa) else 0
        vb = pb[i] if i < len(pb) else 0
        if va != vb: return -1 if va < vb else 1
    return 0

@router.get('/check')
def check(device_version: str = Query("0.0.0")):
    reg = _read_registry()
    ver = reg.get('version', '0.0.0')
    min_req = reg.get('min_required', '0.0.0')
    need_update = _cmp(device_version, min_req) < 0
    return {'current': ver, 'min_required': min_req, 'updateRequired': need_update, 'etag': reg.get('etag')}
