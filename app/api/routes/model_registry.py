from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import json, hashlib, time

router = APIRouter(tags=['model'], prefix='/model')
BASE = Path(__file__).resolve().parents[2] / 'model'
REG = BASE / 'registry.json'
BUNDLE = BASE / 'model.json'

def _reg():
    if not REG.exists(): raise HTTPException(503, detail='registry missing')
    return json.loads(REG.read_text(encoding='utf-8'))

@router.get('/version')
def version():
    return _reg()

@router.get('/bundle')
def bundle():
    if not BUNDLE.exists(): raise HTTPException(503, detail='bundle missing')
    etag = hashlib.sha1(BUNDLE.read_bytes()).hexdigest()[:12]
    return JSONResponse(content=json.loads(BUNDLE.read_text(encoding='utf-8')), headers={'ETag': etag})

@router.post('/promote')
def promote(body: dict):
    if 'version' not in body or 'bundle' not in body: raise HTTPException(400, detail='version and bundle required')
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    BUNDLE.write_text(json.dumps(body['bundle']), encoding='utf-8')
    etag = hashlib.sha1(BUNDLE.read_bytes()).hexdigest()[:12]
    reg = _reg() if REG.exists() else {}
    reg.update({
        'model_id': reg.get('model_id','golex'),
        'version': body['version'],
        'bundle_etag': etag,
        'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    })
    if 'min_required' in body: reg['min_required'] = body['min_required']
    if 'notes' in body: reg['notes'] = body['notes']
    REG.write_text(json.dumps(reg, indent=2), encoding='utf-8')
    return {'ok': True, 'version': reg['version'], 'bundle_etag': etag}
