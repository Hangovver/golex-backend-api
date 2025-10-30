import os
from ..ai.models import poisson_dc, lgbm_stub, poisson_alt
from ..services.feature_service import compute_basic_features

MODEL = os.environ.get("AI_MODEL", "poisson")

async def predict_fixture_ml(db, fixture_id: str):
    feats = await compute_basic_features(db, fixture_id)
    if MODEL == "lgbm" and getattr(lgbm_stub, "ACTIVE", False):
        out = lgbm_stub.predict(feats)
        if out: return {"modelVersion": getattr(lgbm_stub, "VERSION","lgbm-stub"), "out": out, "features": feats}
    out = poisson_dc.predict(feats)
    return {"modelVersion": "poisson-dc-0.1", "out": out, "features": feats}


async def predict_with_model(db, fixture_id: str, model_name: str):
    feats = await compute_basic_features(db, fixture_id)
    if model_name == "lgbm" and getattr(lgbm_stub, "ACTIVE", False):
        out = lgbm_stub.predict(feats)
        if out: return {"modelVersion": getattr(lgbm_stub, "VERSION","lgbm-stub"), "out": out, "features": feats}
    if model_name == "poisson_alt":
        out = poisson_alt.predict(feats)
        return {"modelVersion": "poisson-alt-0.1", "out": out, "features": feats}
    # default
    out = poisson_dc.predict(feats)
    return {"modelVersion": "poisson-dc-0.1", "out": out, "features": feats}
