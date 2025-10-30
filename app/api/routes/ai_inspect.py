from fastapi import APIRouter
from ..deps import SessionLocal
from ..ai.features.feature_pool import list_features, TARGETS
from ..services.feature_service import compute_basic_features
from ...schemas.ai import FeatureInfo, FeaturesResponse, TargetsInfo

router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/features", response_model=list[FeatureInfo])
async def features():
    return list_features()

@router.get("/targets", response_model=TargetsInfo)
async def targets():
    return {"targets": TARGETS}

@router.get("/features/{fixture_id}", response_model=FeaturesResponse)
async def features_for_fixture(fixture_id: str):
    db = SessionLocal()
    try:
        f = await compute_basic_features(db, fixture_id)
        return {"fixtureId": fixture_id, "features": f}
    finally:
        db.close()
