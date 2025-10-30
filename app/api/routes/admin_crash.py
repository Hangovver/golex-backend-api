from fastapi import APIRouter, Body
from ...services import crash_grouping as CG

router = APIRouter(prefix="/admin/crash", tags=["admin-crash"])

@router.post("/group-test")
async def group_test(trace: str = Body(..., embed=True)):
    return CG.group_label(trace)
