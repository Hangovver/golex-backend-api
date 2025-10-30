"""
API-Football adapter (LIVE_MODE).
If LIVE_MODE=1 in env, real calls should be made via the official API client / requests.
Here we keep placeholders to avoid leaking keys; integrate requests in production.
"""
import os, time, random
from . import proxy_client as PX
from . import apisports_client as AS

LIVE = os.getenv("LIVE_MODE", "0") == "1"

def get_league_context(league_id: str):
    if PX.enabled():
        try:
            j = PX.get_json(f"/leagues/{league_id}/context")
            return j
        except Exception:
            pass
    if AS.enabled():
        try:
            # Example upstream mapping; adjust to your proxy contract if needed
            j = {
                "standings": AS.get_json("/standings", params={"league": league_id, "season": "2024"}),
                "fixtures": {
                    "upcoming": AS.get_json("/fixtures", params={"league": league_id, "next": 5}),
                    "recent": AS.get_json("/fixtures", params={"league": league_id, "last": 5}),
                },
            }
            return j
        except Exception:
            pass
    if not LIVE:
        # fallback demo
        return {
            "standings": {
                "leagueId": league_id,
                "table": [
                    {"pos":1,"teamId":"GS","team":"Galatasaray","pts":24,"p":10,"w":7,"d":3,"l":0,"gd":"+12"},
                    {"pos":2,"teamId":"FB","team":"Fenerbahçe","pts":22,"p":10,"w":7,"d":1,"l":2,"gd":"+9"},
                    {"pos":3,"teamId":"BJK","team":"Beşiktaş","pts":19,"p":10,"w":6,"d":1,"l":3,"gd":"+6"}
                ]
            },
            "fixtures": {
                "upcoming":[{"fixtureId":"1001","home":"GS","away":"FB","ts": int(time.time())+86400}],
                "recent":[{"fixtureId":"991","home":"GS","away":"BJK","score":"2-1"}]
            }
        }
    # LIVE: implement real fetch & mapping here
    return {"standings": {"leagueId": league_id, "table": []}, "fixtures": {"upcoming": [], "recent": []}}

def get_team_form(team_id: str, window: int):
    if PX.enabled():
        try:
            j = PX.get_json(f"/teams/{team_id}/form", params={"window": window})
            return j.get("form", []) if isinstance(j, dict) else j
        except Exception:
            pass
    if AS.enabled():
        try:
            # API-Sports form: use last N results
            res = AS.get_json("/teams/statistics", params={"team": team_id, "season": "2024"})
            # Simplify to W/D/L array if available; fallback empty
            form = []
            try:
                f = res.get("response", {}).get("form", "")
                form = [c for c in f if c in ("W","D","L")][-window:]
            except Exception:
                form = []
            return form
        except Exception:
            pass
    if not LIVE:
        import random
        WDL = ["W","D","L"]
        random.seed(hash(team_id)%10000)
        return [random.choice(WDL) for _ in range(window)]
    return []

def get_team_xgtrend(team_id: str, window: int):
    if PX.enabled():
        try:
            j = PX.get_json(f"/teams/{team_id}/xgtrend", params={"window": window})
            if isinstance(j, dict) and all(k in j for k in ("x","xg","xga")):
                return j
        except Exception:
            pass
    if AS.enabled():
        try:
            # API-Sports does not expose xG; approximate with goals & shots as placeholder
            stats = AS.get_json("/teams/statistics", params={"team": team_id, "season": "2024"}).get("response", {})
            xs = list(range(1, window+1))
            xg  = [max(0.4, (stats.get("goals", {}).get("for", {}).get("total", {}).get("home", 10)/30.0)) for _ in xs]
            xga = [max(0.3, (stats.get("goals", {}).get("against", {}).get("total", {}).get("home", 8)/30.0)) for _ in xs]
            return {"x": xs, "xg": xg, "xga": xga}
        except Exception:
            pass
    if not LIVE:
        random.seed(hash(team_id)%10000+7)
        xs = list(range(1, window+1))
        xg  = [round(0.5 + random.random()*1.2, 2) for _ in xs]
        xga = [round(0.4 + random.random()*1.0, 2) for _ in xs]
        return {"x": xs, "xg": xg, "xga": xga}
    return {"x": [], "xg": [], "xga": []}

def fuzzy_search(q: str, type_: str, country: str|None, league_id: str|None, limit: int):
    if not LIVE:
        # same demo dataset as before; replace with real index in live
        DATA = {
            "team": [
                {"id":"GS","name":"Galatasaray","country":"TR","leagueId":"TR1"},
                {"id":"FB","name":"Fenerbahçe","country":"TR","leagueId":"TR1"},
                {"id":"BJK","name":"Beşiktaş","country":"TR","leagueId":"TR1"},
                {"id":"RMA","name":"Real Madrid","country":"ES","leagueId":"ES1"},
                {"id":"BAR","name":"Barcelona","country":"ES","leagueId":"ES1"},
            ],
            "league": [
                {"id":"TR1","name":"Süper Lig","country":"TR"},
                {"id":"ES1","name":"LaLiga","country":"ES"},
                {"id":"GB1","name":"Premier League","country":"GB"},
            ],
            "player": [
                {"id":"p1","name":"Mauro Icardi","teamId":"GS","country":"AR"},
                {"id":"p2","name":"Vinícius Júnior","teamId":"RMA","country":"BR"},
            ]
        }
        import difflib
        items = DATA.get(type_, [])
        if country:
            items = [x for x in items if x.get("country")==country]
        if league_id:
            items = [x for x in items if x.get("leagueId")==league_id]
        names = [x["name"] for x in items]
        hits = difflib.get_close_matches(q, names, n=limit, cutoff=0.3)
        res = [x for x in items if x["name"] in hits]
        out = [{"id":x["id"], "name":x["name"], "score": round(difflib.SequenceMatcher(None, q.lower(), x["name"].lower()).ratio(),3)} for x in res]
        out.sort(key=lambda r: r["score"], reverse=True)
        return out
    return []


def get_fixture(fixture_id: str):
    if not LIVE:
        # demo content for fixture
        rid = int("".join([c for c in fixture_id if c.isdigit()]) or 1001)
        random.seed(rid)
        home = random.choice(["Galatasaray","Fenerbahçe","Beşiktaş","Trabzonspor"])
        away = random.choice(["Fenerbahçe","Beşiktaş","Başakşehir","Adana Demir"])
        mu_home = round(1.2 + random.random()*1.4, 2)
        mu_away = round(0.8 + random.random()*1.2, 2)
        return {
            "fixtureId": fixture_id,
            "home": {"id":"HOME", "name": home},
            "away": {"id":"AWAY", "name": away},
            "status": "SCHEDULED",
            "timestamp": int(time.time()) + 3600,
            "mu": {"home": mu_home, "away": mu_away},
            "events": [
                {"min": 12, "team":"HOME", "type":"shot"},
                {"min": 35, "team":"AWAY", "type":"yellow"},
            ],
            "lineups": {"home": [], "away": []},
            "stats": {"possession":[52,48], "shots":[11,9], "xg":[round(mu_home,2), round(mu_away,2)]}
        }
    return {"fixtureId": fixture_id, "home": {"id":"H"}, "away":{"id":"A"}, "status":"SCHEDULED","timestamp": int(time.time()) + 3600, "mu": {"home":1.4,"away":1.1}}

def get_player_baseline(fixture_id: str, player_id: str, season: str|None=None):
    """
    Returns baseline dict for a player for given fixture:
      { "playerId": pid, "teamId": "...", "side": "H"|"A"|"?",
        "startProb": 0.7, "minutesExp": 70,
        "goal90": 0.35, "sog90": 0.8, "yc90": 0.12, "rc90": 0.01 }
    Heuristics:
      - If Proxy provides /players/baseline → trust it.
      - Else API-Sports: /players?id=...&season=... (defaults to env SEASON or 2024)
    """
    import os
    season = season or os.getenv("SEASON","2024")

    # 1) Proxy
    if PX.enabled():
        try:
            j = PX.get_json("/players/baseline", params={"fixtureId": fixture_id, "playerId": player_id, "season": season})
            if isinstance(j, dict) and j.get("playerId"):
                return j
        except Exception:
            pass

    # 2) API-Sports
    if AS.enabled():
        try:
            j = AS.get_json("/players", params={"id": player_id, "season": season})
            r = (j.get("response") or [])[0]
            stats = (r.get("statistics") or [])[0]
            team = stats.get("team",{}).get("id")
            # derive per-90
            apps = stats.get("games",{}).get("appearences") or 0
            minutes = stats.get("games",{}).get("minutes") or 0
            lineups = stats.get("games",{}).get("lineups") or 0
            goals = stats.get("goals",{}).get("total") or 0
            sog = stats.get("shots",{}).get("on") or 0
            yc = stats.get("cards",{}).get("yellow") or 0
            rc = stats.get("cards",{}).get("red") or 0
            m90 = max(1.0, minutes/90.0)
            goal90 = goals / m90
            sog90 = sog / m90
            yc90 = yc / m90
            rc90 = rc / m90
            minutesExp = min(90, (minutes/apps) if apps else 70)
            startProb = min(0.95, (lineups/apps) if apps else 0.6)
            # side infer from fixture
            fx = get_fixture(fixture_id)
            side = "?"
            try:
                hid = (fx.get("home") or {}).get("id")
                aid = (fx.get("away") or {}).get("id")
                if str(team)==str(hid): side="H"
                elif str(team)==str(aid): side="A"
            except Exception:
                pass
            return {"playerId": str(player_id), "teamId": str(team), "side": side,
                    "startProb": float(startProb), "minutesExp": float(minutesExp),
                    "goal90": float(goal90), "sog90": float(sog90),
                    "yc90": float(yc90), "rc90": float(rc90)}
        except Exception:
            pass

    # 3) Demo fallback
    return {"playerId": str(player_id), "teamId": "T?", "side": "?", "startProb": 0.6, "minutesExp": 65.0,
            "goal90": 0.25, "sog90": 0.7, "yc90": 0.12, "rc90": 0.01}


def list_leagues():
    # Demo: return cached popular leagues; in prod call /leagues endpoint of provider
    return [
        {"id":"39","name":"Premier League","country":"England"},
        {"id":"140","name":"La Liga","country":"Spain"},
        {"id":"78","name":"Bundesliga","country":"Germany"},
        {"id":"135","name":"Serie A","country":"Italy"},
        {"id":"61","name":"Ligue 1","country":"France"}
    ]

def list_teams(leagueId: str|None=None):
    # Demo: minimal list; in prod call /teams?league=..
    sample = [
        {"id":"33","name":"Manchester United","country":"England","leagueId":"39"},
        {"id":"40","name":"Liverpool","country":"England","leagueId":"39"},
        {"id":"541","name":"Real Madrid","country":"Spain","leagueId":"140"},
        {"id":"529","name":"Barcelona","country":"Spain","leagueId":"140"},
        {"id":"157","name":"Bayern Munich","country":"Germany","leagueId":"78"},
    ]
    return [t for t in sample if not leagueId or str(t.get("leagueId"))==str(leagueId)]
