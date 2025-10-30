from typing import Any, Dict, List
from datetime import datetime, timezone

def map_fixture(api_item: Dict[str, Any]) -> Dict[str, Any]:
    f = api_item.get("fixture", {})
    l = api_item.get("league", {})
    teams = api_item.get("teams", {})
    venue = f.get("venue") or {}
    # Defensive parsing
    return {
        "id": f.get("id_uuid") or api_uuid(f.get("id"), prefix="fix"),
        "league_id": api_uuid(l.get("id"), prefix="lea"),
        "season_id": api_uuid(l.get("season"), prefix="sea"),
        "home_team_id": api_uuid(teams.get("home", {}).get("id"), prefix="tm"),
        "away_team_id": api_uuid(teams.get("away", {}).get("id"), prefix="tm"),
        "venue_id": api_uuid(venue.get("id"), prefix="ven") if venue.get("id") else None,
        "starts_at_utc": to_dt(f.get("date")),
        from ..util.status import normalize_status
    "status": normalize_status((f.get("status") or {}).get("short")),
        "round": l.get("round"),
        "referee": f.get("referee"),
        "api_football_id": f.get("id"),
    }

def api_uuid(num: Any, prefix: str) -> str:
    return f"{prefix}-{num}" if num is not None else f"{prefix}-na"

def to_dt(s: Any):
    if not s:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception:
        return datetime.now(timezone.utc)
