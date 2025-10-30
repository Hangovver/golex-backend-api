-- ==========================================
-- GOLEX DATABASE SCHEMA
-- Supabase PostgreSQL Migration
-- ==========================================

-- ==========================================
-- 1. FIXTURES (Maçlar)
-- ==========================================
CREATE TABLE IF NOT EXISTS fixtures (
    id VARCHAR PRIMARY KEY,
    league_id VARCHAR NOT NULL,
    home_team_id VARCHAR NOT NULL,
    away_team_id VARCHAR NOT NULL,
    match_date TIMESTAMP NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'NS',  -- NS, 1H, HT, 2H, FT, PST, CANC
    home_score INT,
    away_score INT,
    minute INT,
    venue VARCHAR,
    referee_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(match_date);
CREATE INDEX IF NOT EXISTS idx_fixtures_status ON fixtures(status);
CREATE INDEX IF NOT EXISTS idx_fixtures_league ON fixtures(league_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_home_team ON fixtures(home_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_away_team ON fixtures(away_team_id);

-- ==========================================
-- 2. TEAMS (Takımlar)
-- ==========================================
CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    logo_url VARCHAR,  -- Cloudflare R2 URL
    country VARCHAR,
    league_id VARCHAR,
    founded INT,
    venue VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league_id);

-- ==========================================
-- 3. PLAYERS (Oyuncular)
-- ==========================================
CREATE TABLE IF NOT EXISTS players (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    team_id VARCHAR,
    position VARCHAR,
    number INT,
    age INT,
    nationality VARCHAR,
    photo_url VARCHAR,  -- Cloudflare R2 URL
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);

-- ==========================================
-- 4. FIXTURE_STATS (Maç İstatistikleri)
-- ==========================================
CREATE TABLE IF NOT EXISTS fixture_stats (
    fixture_id VARCHAR PRIMARY KEY,
    home_xg FLOAT,
    away_xg FLOAT,
    home_possession INT,
    away_possession INT,
    home_shots INT,
    away_shots INT,
    home_shots_on_target INT,
    away_shots_on_target INT,
    home_corners INT,
    away_corners INT,
    home_fouls INT,
    away_fouls INT,
    home_yellow_cards INT,
    away_yellow_cards INT,
    home_red_cards INT,
    away_red_cards INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

-- ==========================================
-- 5. LINEUPS (Kadrolar)
-- ==========================================
CREATE TABLE IF NOT EXISTS lineups (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR NOT NULL,
    team_id VARCHAR NOT NULL,
    player_id VARCHAR NOT NULL,
    position VARCHAR,  -- GK, DF, MF, FW
    grid_position VARCHAR,  -- 4-4-2 formatında konum
    is_substitute BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lineups_fixture ON lineups(fixture_id);
CREATE INDEX IF NOT EXISTS idx_lineups_team ON lineups(team_id);
CREATE INDEX IF NOT EXISTS idx_lineups_player ON lineups(player_id);

-- ==========================================
-- 6. H2H_HISTORY (Karşılaşma Geçmişi)
-- ==========================================
CREATE TABLE IF NOT EXISTS h2h_history (
    id SERIAL PRIMARY KEY,
    team1_id VARCHAR NOT NULL,
    team2_id VARCHAR NOT NULL,
    fixture_id VARCHAR NOT NULL,
    match_date TIMESTAMP NOT NULL,
    team1_score INT,
    team2_score INT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (team1_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (team2_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_h2h_team1 ON h2h_history(team1_id);
CREATE INDEX IF NOT EXISTS idx_h2h_team2 ON h2h_history(team2_id);

-- ==========================================
-- 7. LEAGUES (Ligler)
-- ==========================================
CREATE TABLE IF NOT EXISTS leagues (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    country VARCHAR,
    logo_url VARCHAR,  -- Cloudflare R2 URL
    season VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leagues_country ON leagues(country);

-- ==========================================
-- 8. STANDINGS (Lig Tablosu)
-- ==========================================
CREATE TABLE IF NOT EXISTS standings (
    id SERIAL PRIMARY KEY,
    league_id VARCHAR NOT NULL,
    team_id VARCHAR NOT NULL,
    position INT NOT NULL,
    played INT,
    won INT,
    drawn INT,
    lost INT,
    goals_for INT,
    goals_against INT,
    goal_difference INT,
    points INT,
    form VARCHAR,  -- "WWDLL" formatı
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_standings_league ON standings(league_id);
CREATE INDEX IF NOT EXISTS idx_standings_team ON standings(team_id);

-- ==========================================
-- 9. ODDS (Bahis Oranları)
-- ==========================================
CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR NOT NULL,
    bookmaker VARCHAR NOT NULL,
    market_code VARCHAR NOT NULL,  -- "1X2", "O2.5", "KG_YES"
    outcome VARCHAR,  -- "home", "away", "over", "yes"
    odds FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_odds_fixture ON odds(fixture_id);
CREATE INDEX IF NOT EXISTS idx_odds_market ON odds(market_code);
CREATE INDEX IF NOT EXISTS idx_odds_bookmaker ON odds(bookmaker);

-- ==========================================
-- 10. BEST_ODDS (En İyi Oranlar - Cache)
-- ==========================================
CREATE TABLE IF NOT EXISTS best_odds (
    fixture_id VARCHAR NOT NULL,
    market_code VARCHAR NOT NULL,
    best_bookmaker VARCHAR NOT NULL,
    best_odds FLOAT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (fixture_id, market_code),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_best_odds_fixture ON best_odds(fixture_id);

-- ==========================================
-- 11. WEATHER (Hava Durumu)
-- ==========================================
CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR UNIQUE NOT NULL,
    location VARCHAR,
    temperature FLOAT,
    humidity INT,
    wind_speed FLOAT,
    precipitation FLOAT,
    weather_code VARCHAR,  -- "clear", "rain", "snow"
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_weather_fixture ON weather(fixture_id);

-- ==========================================
-- 12. PLAYER_VALUES (Transfermarkt)
-- ==========================================
CREATE TABLE IF NOT EXISTS player_values (
    player_id VARCHAR PRIMARY KEY,
    market_value BIGINT,  -- Euro cinsinden
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- ==========================================
-- 13. INJURIES (Sakatlıklar)
-- ==========================================
CREATE TABLE IF NOT EXISTS injuries (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR NOT NULL,
    team_id VARCHAR NOT NULL,
    injury_type VARCHAR,
    expected_return DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_injuries_player ON injuries(player_id);
CREATE INDEX IF NOT EXISTS idx_injuries_team ON injuries(team_id);

-- ==========================================
-- 14. NEWS (Haberler)
-- ==========================================
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content TEXT,
    source VARCHAR,
    url VARCHAR,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at);

-- ==========================================
-- 15. IMAGES_METADATA (Görsel Meta Verileri)
-- ==========================================
CREATE TABLE IF NOT EXISTS images_metadata (
    id SERIAL PRIMARY KEY,
    object_key VARCHAR UNIQUE NOT NULL,  -- R2 object key
    public_url VARCHAR NOT NULL,  -- R2 public URL
    entity_type VARCHAR NOT NULL,  -- "team", "player", "league"
    entity_id VARCHAR NOT NULL,
    file_size BIGINT,
    content_type VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_images_entity ON images_metadata(entity_type, entity_id);

-- ==========================================
-- 16. SYNC_LOG (Senkronizasyon Geçmişi)
-- ==========================================
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR NOT NULL,  -- "fixtures", "teams", "odds", "images"
    status VARCHAR NOT NULL,  -- "success", "failed", "partial"
    records_synced INT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sync_log_type ON sync_log(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_log_status ON sync_log(status);

-- ==========================================
-- ENABLE ROW LEVEL SECURITY (Optional)
-- ==========================================
-- Uncomment if you want RLS enabled
-- ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
-- ... (other tables)

-- ==========================================
-- DONE!
-- ==========================================

