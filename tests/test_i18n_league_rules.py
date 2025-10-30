from app.utils.i18n import normalize_league_name
def test_known_mapping():
    assert normalize_league_name("premier league") == "Premier League"
def test_turkish_super_lig():
    assert normalize_league_name("super lig") in ("Süper Lig","Super Lig")
def test_fallback_titlecase():
    assert normalize_league_name("serie a") == "Serie A"
