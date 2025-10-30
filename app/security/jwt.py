import time, os
import jwt
from typing import Dict, Any

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ISSUER = os.getenv("JWT_ISSUER", "golex")
ACCESS_TTL = int(os.getenv("JWT_ACCESS_TTL", "900"))     # 15m
REFRESH_TTL = int(os.getenv("JWT_REFRESH_TTL", "2592000")) # 30d

def _now() -> int:
    return int(time.time())

def create_token(sub: str, scope: str = "access", claims: Dict[str, Any] | None = None) -> str:
    payload = {"iss": JWT_ISSUER, "sub": sub, "scope": scope, "iat": _now(), "exp": _now() + (ACCESS_TTL if scope == "access" else REFRESH_TTL)}
    if claims:
        payload.update(claims)
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str, scope: str | None = None) -> Dict[str, Any]:
    data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "iat", "sub"]})
    if scope and data.get("scope") != scope:
        raise jwt.InvalidTokenError("Invalid scope")
    return data
