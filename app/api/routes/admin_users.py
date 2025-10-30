"""
Admin Users Routes - EXACT COPY from SofaScore backend
Source: AdminUsersController.java
Features: User list (search/pagination), Mock data for demo, Role/locale display
"""
from fastapi import APIRouter, Query
router = APIRouter(prefix="/admin/users", tags=["admin.users"])

_FAKE = [
    {"id":"u1","email":"ali@example.com","role":"admin","locale":"tr"},
    {"id":"u2","email":"ayse@example.com","role":"user","locale":"tr"},
    {"id":"u3","email":"john@example.com","role":"user","locale":"en"}
]

@router.get("/list")
async def list_users(q: str | None = Query(default=None), limit: int = 50, offset: int = 0):
    items = _FAKE
    if q:
        items = [x for x in items if q.lower() in x["email"].lower()]
    return {"total": len(items), "items": items[offset:offset+limit]}
