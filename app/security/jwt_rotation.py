import os, json, time, jwt
from typing import Dict, Tuple

# Env: AUTH_JWT_KEYS='{"kid1":"secret1","kid2":"secret2"}'; AUTH_JWT_ACTIVE_KID='kid2'
def _load_keys() -> Tuple[Dict[str,str], str]:
    keys = json.loads(os.getenv('AUTH_JWT_KEYS','{}') or '{}')
    active = os.getenv('AUTH_JWT_ACTIVE_KID') or (list(keys.keys())[-1] if keys else 'default')
    if not keys and os.getenv('JWT_SECRET'):
        keys = { 'default': os.getenv('JWT_SECRET') }
        active = 'default'
    return keys, active

def sign(payload: dict) -> str:
    keys, active = _load_keys()
    secret = keys[active]
    headers = { 'kid': active }
    return jwt.encode(payload | {'iat': int(time.time())}, secret, algorithm='HS256', headers=headers)

def verify(token: str) -> dict:
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get('kid','default')
    keys, _ = _load_keys()
    secret = keys.get(kid) or next(iter(keys.values()))
    return jwt.decode(token, secret, algorithms=['HS256'])
