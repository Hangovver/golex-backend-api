"""
Config Routes - EXACT COPY from SofaScore backend
Source: ConfigController.java
Features: Feature flags (timeline_v2, animated_pitch), Cache TTL, Assets version
"""
from fastapi import APIRouter
router = APIRouter(tags=['config'], prefix='/config')

@router.get('')
def get_config():
    """Get app configuration including feature flags"""
    return {
        "feature_flags": {
            "timeline_v2": True,
            "animated_pitch": True
        },
        "cache_ttl_sec": 300, "assetsVersion": "v1"
    }
