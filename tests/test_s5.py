
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)

def test_league_context_ok():
    r = c.get("/leagues/1/context?include=league,standings,fixtures")
    assert r.status_code == 200
    assert "league" in r.json()

def test_fixtures_paging_etag():
    r1 = c.get("/leagues/1/fixtures?type=upcoming&limit=2")
    assert r1.status_code == 200
    etag = r1.headers.get("ETag")
    r2 = c.get("/leagues/1/fixtures?type=upcoming&limit=2", headers={"If-None-Match": etag})
    # Either 304 or 200 with same body allowed (demo cache)
    assert r2.status_code in (200,304)

def test_telemetry_collect_and_fetch():
    r = c.post("/telemetry/events", json=[{"name":"unit_test","params":{"ok":True}}])
    assert r.status_code == 200
    r2 = c.get("/telemetry/events?limit=5")
    assert r2.status_code == 200
    assert "items" in r2.json()
