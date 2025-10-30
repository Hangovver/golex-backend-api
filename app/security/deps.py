from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..db.session import SessionLocal
from .jwt import verify_token
from ..core.config import settings

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_client_tag(x_client_tag: str | None = Header(default=None, alias="X-Client-Tag")):
    # Not a secret; just a tag to recognize our app traffic
    if x_client_tag != settings.app_client_token:
        raise HTTPException(status_code=403, detail="Invalid client tag")
    return True

def get_current_user(token: str | None = Header(default=None, alias="Authorization")):
    if not token or not token.lower().startswith("bearer "):
        raise HTTPException(401, detail="Missing bearer token")
    tok = token.split(" ", 1)[1]
    try:
        return verify_token(tok, scope="access")
    except Exception as e:
        raise HTTPException(401, detail="Invalid token")
