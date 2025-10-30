from dataclasses import dataclass
from typing import List, Dict, Any

TARGETS = ["1x2", "over25", "btts", "scoreDist"]

@dataclass
class Feature:
    key: str
    desc: str

FEATURE_POOL: List[Feature] = [
    Feature("team_form_home_5", "Home team last 5 form (points/5)"),
    Feature("team_form_away_5", "Away team last 5 form (points/5)"),
    Feature("avg_goals_home", "Home goals per match (season)"),
    Feature("avg_goals_away", "Away goals per match (season)"),
    Feature("head2head_last5_diff", "H2H goal diff last 5"),
    Feature("rest_days_diff", "Rest days (home-away)"),
    Feature("league_strength_home", "League strength index for home"),
    Feature("league_strength_away", "League strength index for away"),
    Feature("elo_home", "ELO-like rating home"),
    Feature("elo_away", "ELO-like rating away"),
]

def list_features() -> List[Dict[str, str]]:
    return [{"key": f.key, "desc": f.desc} for f in FEATURE_POOL]
