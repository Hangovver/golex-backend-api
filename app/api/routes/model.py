from fastapi import APIRouter, Body
from ...services import model_registry as MR
from ...services import metrics as M

router = APIRouter(prefix="/model", tags=["model"])

@router.get("/version")
async def version():
    M.inc("model_version_gets_total"); return MR.get_version()

@router.post("/version")
async def bump(version: str = Body(...), url: str | None = Body(None)):
    MR.set_version(version, url); M.inc("model_version_bumps_total")
    M.inc("model_version_gets_total"); return MR.get_version()

@router.post("/refresh/force")
async def force(flag: bool = Body(True)):
    MR.set_force(flag); M.inc("model_force_refresh_total")
    M.inc("model_version_gets_total"); return MR.get_version()
