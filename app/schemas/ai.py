from pydantic import BaseModel
from typing import Dict, List, Optional

class FeatureInfo(BaseModel):
    key: str
    desc: str

class FeaturesResponse(BaseModel):
    fixtureId: str
    features: Dict[str, float]

class TargetsInfo(BaseModel):
    targets: List[str]
