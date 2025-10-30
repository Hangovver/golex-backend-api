from datetime import datetime
from ..utils.time_norm import parse_to_utc, season_year_for_date, season_name

SRC = "api-football"

def league(api_obj):
    l = api_obj.get("league", {}) if isinstance(api_obj.get("league", {}), dict) else api_obj
    country = api_obj.get("country", {}) if isinstance(api_obj.get("country", {}), dict) else {"name": api_obj.get("country")}
    return {
        "source": SRC,
        "entity": "league",
        "external_id": str(l.get("id")),
        "data": {
            "name": l.get("name"),
            "country": (country or {}).get("name") if country else None,
            "type": l.get("type"),
            "season_format": None
        }
    }

def team(api_obj):
    t = api_obj.get("team", {}) if isinstance(api_obj.get("team", {}), dict) else api_obj
    return {
        "source": SRC,
        "entity": "team",
        "external_id": str(t.get("id")),
        "data": {
            "name": t.get("name"),
            "country": t.get("country"),
            "code": t.get("code"),
            "founded": t.get("founded"),
            "venue": venue(api_obj.get("venue", {})) if isinstance(api_obj.get("venue", {}), dict) else None
        }
    }

def player(api_obj):
    p = api_obj.get("player", {}) if isinstance(api_obj.get("player", {}), dict) else api_obj
    stats_list = api_obj.get("statistics") or []
    s = stats_list[0] if isinstance(stats_list, list) and stats_list else {}
    team_info = s.get("team") or {}
    return {
        "source": SRC,
        "entity": "player",
        "external_id": str(p.get("id")),
        "data": {
            "name": p.get("name"),
            "position": (s.get("games") or {}).get("position"),
            "age": p.get("age"),
            "nationality": p.get("nationality"),
            "team_external_id": str(team_info.get("id")) if team_info else None
        }
    }

def venue(v):
    if not v: return None
    return {
        "source": SRC,
        "entity": "venue",
        "external_id": str(v.get("id")) if v.get("id") is not None else None,
        "data": {
            "name": v.get("name"),
            "city": v.get("city"),
            "capacity": v.get("capacity"),
        }
    }

def coach(c):
    if not c: return None
    return {
        "source": SRC,
        "entity": "coach",
        "external_id": str(c.get("id")) if c.get("id") is not None else None,
        "data": {
            "name": c.get("name"),
            "age": c.get("age"),
            "nationality": c.get("nationality"),
            "team_external_id": str((c.get("team") or {}).get("id")) if c.get("team") else None
        }
    }

def fixture(obj):
    f = obj.get("fixture", obj)
    league_obj = obj.get("league", {}) or {}
    teams_obj = obj.get("teams", {}) or {}
    venue_obj = (f.get("venue") or {}) if isinstance(f.get("venue"), dict) else {}
    date = parse_to_utc(f.get("date"))
    year = season_year_for_date(date)
    return {
        "source": SRC,
        "entity": "fixture",
        "external_id": str(f.get("id")),
        "data": {
            "league_external_id": str(league_obj.get("id")) if league_obj else None,
            "season_year_start": year,
            "date_utc": date.isoformat(),
            "status": (f.get("status") or {}).get("short") or f.get("status"),
            "venue_external_id": str(venue_obj.get("id")) if venue_obj else None,
            "home_team_external_id": str((teams_obj.get("home") or {}).get("id")) if teams_obj.get("home") else None,
            "away_team_external_id": str((teams_obj.get("away") or {}).get("id")) if teams_obj.get("away") else None,
            "round": (league_obj or {}).get("round"),
            "goals_home": (obj.get("goals") or {}).get("home"),
            "goals_away": (obj.get("goals") or {}).get("away"),
        }
    }

def event(e):
    return {
        "source": SRC,
        "entity": "event",
        "external_id": f"{(e.get('fixture') or {}).get('id')}-{(e.get('time') or {}).get('elapsed')}-{(e.get('player') or {}).get('id')}-{e.get('type')}-{e.get('detail')}",
        "data": {
            "fixture_external_id": str((e.get("fixture") or {}).get("id")) if e.get("fixture") else None,
            "minute": (e.get("time") or {}).get("elapsed"),
            "type": e.get("type"),
            "detail": e.get("detail"),
            "player_name": (e.get("player") or {}).get("name"),
            "assist_name": (e.get("assist") or {}).get("name"),
            "team_external_id": str((e.get("team") or {}).get("id")) if e.get("team") else None,
            "extra": {"comment": e.get("comments")}
        }
    }

def lineup(obj):
    return {
        "source": SRC,
        "entity": "lineup",
        "external_id": f"{(obj.get('team') or {}).get('id')}-{(obj.get('fixture') or {}).get('id')}",
        "data": {
            "fixture_external_id": str((obj.get("fixture") or {}).get("id")) if obj.get("fixture") else None,
            "team_external_id": str((obj.get("team") or {}).get("id")) if obj.get("team") else None,
            "formation": (obj.get("formation") or (obj.get("team") or {}).get("formation")),
            "players": obj.get("startXI") or obj.get("players")
        }
    }

def standing_row(obj):
    team = (obj.get("team") or {})
    allm = (obj.get("all") or {})
    goals = allm.get("goals") or {}
    return {
        "source": SRC,
        "entity": "standing",
        "external_id": str(team.get("id")),
        "data": {
            "team_external_id": str(team.get("id")),
            "rank": obj.get("rank"),
            "played": allm.get("played"),
            "win": allm.get("win"),
            "draw": allm.get("draw"),
            "loss": allm.get("lose") or allm.get("loss"),
            "goals_for": goals.get("for"),
            "goals_against": goals.get("against"),
            "points": obj.get("points")
        }
    }
