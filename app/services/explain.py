# Simple feature contribution explainer (heuristic for MVP)
# Computes z-score-ish contribution based on feature value vs neutral baseline.

NEUTRAL = {
    "team_form_home_5": 0.5,
    "team_form_away_5": 0.5,
    "avg_goals_home": 1.2,
    "avg_goals_away": 1.2,
    "head2head_last5_diff": 0.0,
    "rest_days_diff": 0.0,
    "league_strength_home": 0.50,
    "league_strength_away": 0.50,
    "elo_home": 1500,
    "elo_away": 1500,
}

WEIGHTS = {
    "team_form_home_5": 0.8,
    "team_form_away_5": -0.7,
    "avg_goals_home": 0.4,
    "avg_goals_away": -0.3,
    "head2head_last5_diff": 0.25,
    "rest_days_diff": 0.1,
    "league_strength_home": 0.6,
    "league_strength_away": -0.5,
    "elo_home": 0.002,
    "elo_away": -0.002,
}

def explain(features: dict, top_k: int = 6):
    contribs = []
    for k,v in features.items():
        base = NEUTRAL.get(k, 0.0)
        w = WEIGHTS.get(k, 0.0)
        score = (v - base) * w
        if score != 0:
            contribs.append({"key": k, "contribution": round(score, 4)})
    contribs.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return contribs[:top_k]
