def test_login(client):
    r = client.post("/api/v1/auth/login", json={"email":"a@b.c","password":"1"})
    assert r.status_code == 200
    assert "access" in r.json()

def test_fixtures_paging(client):
    r = client.get("/api/v1/fixtures?status=LIVE&limit=1")
    assert r.status_code == 200
    js = r.json()
    assert "items" in js and len(js["items"])<=1
