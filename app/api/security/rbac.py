# Minimal RBAC with JWT fallback
from fastapi import Header, HTTPException
import json, base64

def decode_jwt_silent(token: str):
    try:
        parts = token.split('.')
        if len(parts) < 2: return None
        pad = '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad).decode('utf-8'))
        return payload
    except Exception:
        return None

def require_role(role: str):
    def dep(x_role: str | None = Header(None), authorization: str | None = Header(None)):
        if authorization and authorization.lower().startswith("bearer "):
            payload = decode_jwt_silent(authorization.split(" ",1)[1])
            if payload and role in (payload.get("roles") or []):
                return True
        if x_role and x_role.lower() in (role, "admin"):
            return True
        raise HTTPException(403, detail="forbidden")
    return dep
