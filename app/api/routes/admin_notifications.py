from fastapi import APIRouter
router = APIRouter(prefix="/admin/notifications", tags=["admin.notifications"])

_FAKE_PREFS = {
    "u1": {"goal": True, "kickoff": True, "final": True},
    "u2": {"goal": True, "kickoff": False, "final": True}
}

@router.get("/prefs/{user_id}")
async def get_prefs(user_id: str):
    return _FAKE_PREFS.get(user_id, {"goal": True, "kickoff": True, "final": True})
