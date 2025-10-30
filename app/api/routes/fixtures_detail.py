"""
Fixtures Detail Routes - EXACT COPY from SofaScore backend
Source: FixtureDetailController.java
Features: Fixture details, ETag caching, API-Football adapter integration
"""
from fastapi import APIRouter, Path, Request
from ...services import apifootball_adapter as AF
from ...services import cache_utils as CU

router = APIRouter(prefix="/fixtures", tags=["fixtures-detail"])

@router.get("/{fixtureId}")
async def fixture_detail(fixtureId: str = Path(...), request: Request = None):
    fx = AF.get_fixture(fixtureId)
    return CU.respond_with_etag(request, fx)
