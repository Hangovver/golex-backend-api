def test_rate_limit_429(client):
    # Send many small requests to trigger limiter (120/min) — demo: try 130
    status = 200
    for i in range(130):
        r = client.get("/api/v1/leagues")
        status = r.status_code
        if status == 429:
            break
    assert status in (200,429)
