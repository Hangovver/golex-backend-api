def test_predictions_core(client):
    r = client.get("/api/v1/predictions/1001?markets=core&explain=false")
    assert r.status_code == 200
    js = r.json()
    assert js["fixtureId"] == "1001"
    assert "probabilities" in js and "mkt.1x2.H" in js["probabilities"]
    assert "explain" not in js

def test_predictions_all_with_explain(client):
    r = client.get("/api/v1/predictions/1001?markets=all&explain=true")
    assert r.status_code == 200
    js = r.json()
    assert "explain" in js and "top_features" in js["explain"]

def test_search_basic(client):
    r = client.get("/api/v1/search?q=gala")
    assert r.status_code == 200
    js = r.json()
    assert any("Galatasaray" in x.get("name","") for x in js.get("items", []))

def test_fixtures_schema(client):
    r = client.get("/api/v1/fixtures?status=LIVE&limit=2")
    js = r.json()
    assert "items" in js
    for it in js["items"]:
        assert set(["id","home","away","status","minute","score"]).issubset(it.keys())
