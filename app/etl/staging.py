from ..mappers import apifootball as M

def stage_fixtures(api_response):
    return [M.fixture(item) for item in (api_response.get("response") or [])]

def stage_events(api_response, fixture_id):
    return [M.event({**e, "fixture": {"id": fixture_id}}) for e in (api_response.get("response") or [])]

def stage_lineups(api_response, fixture_id):
    return [M.lineup({**row, "fixture": {"id": fixture_id}}) for row in (api_response.get("response") or [])]

def stage_standings(api_response):
    resp = api_response.get("response") or []
    if not resp: return []
    table = resp[0].get("league", {}).get("standings", [[]])[0]
    return [M.standing_row(row) for row in table]
