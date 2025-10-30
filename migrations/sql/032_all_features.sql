-- ============================================================================
-- GOLEX - All 10 Features Database Migration
-- ============================================================================
-- Created: 2025-10-27
-- Purpose: Live Betting, Arbitrage, Bet Tracker, Social, Weather, H2H, Combo, Bankroll
-- ============================================================================

-- === 1. LIVE BETTING TABLES ===

CREATE TABLE IF NOT EXISTS live_stats (
    fixture_id VARCHAR(50) PRIMARY KEY,
    minute INTEGER NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    home_shots INTEGER DEFAULT 0,
    away_shots INTEGER DEFAULT 0,
    home_shots_on_target INTEGER DEFAULT 0,
    away_shots_on_target INTEGER DEFAULT 0,
    home_possession INTEGER DEFAULT 50,
    away_possession INTEGER DEFAULT 50,
    home_passes INTEGER DEFAULT 0,
    away_passes INTEGER DEFAULT 0,
    home_pass_accuracy FLOAT DEFAULT 0.0,
    away_pass_accuracy FLOAT DEFAULT 0.0,
    home_fouls INTEGER DEFAULT 0,
    away_fouls INTEGER DEFAULT 0,
    home_corners INTEGER DEFAULT 0,
    away_corners INTEGER DEFAULT 0,
    home_offsides INTEGER DEFAULT 0,
    away_offsides INTEGER DEFAULT 0,
    home_yellow_cards INTEGER DEFAULT 0,
    away_yellow_cards INTEGER DEFAULT 0,
    home_red_cards INTEGER DEFAULT 0,
    away_red_cards INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_live_stats_minute ON live_stats(minute);

CREATE TABLE IF NOT EXISTS live_events (
    event_id VARCHAR(100) PRIMARY KEY,
    fixture_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- goal, yellow_card, red_card, substitution
    minute INTEGER NOT NULL,
    team_id VARCHAR(50),
    player_id VARCHAR(50),
    player_name VARCHAR(200),
    detail VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_live_events_fixture ON live_events(fixture_id);
CREATE INDEX idx_live_events_minute ON live_events(minute);


-- === 2. ARBITRAGE TABLES ===

CREATE TABLE IF NOT EXISTS bookmaker_odds (
    fixture_id VARCHAR(50) NOT NULL,
    bookmaker VARCHAR(100) NOT NULL,
    market VARCHAR(50) NOT NULL,
    outcome VARCHAR(50) NOT NULL, -- home, draw, away, over, under
    odds FLOAT NOT NULL,
    last_update TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (fixture_id, bookmaker, market, outcome)
);

CREATE INDEX idx_bookmaker_odds_fixture ON bookmaker_odds(fixture_id);
CREATE INDEX idx_bookmaker_odds_market ON bookmaker_odds(market);
CREATE INDEX idx_bookmaker_odds_update ON bookmaker_odds(last_update DESC);

CREATE TABLE IF NOT EXISTS arbitrage_history (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR(50),
    market VARCHAR(50),
    profit_pct FLOAT,
    best_odds JSONB,
    stakes JSONB,
    guaranteed_profit FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_arbitrage_history_profit ON arbitrage_history(profit_pct DESC);


-- === 3. BET TRACKER (Already exists from 466 markets, just ensure it's here) ===

-- user_bets table already created in 030_markets_466.sql
-- Just add index if missing
CREATE INDEX IF NOT EXISTS idx_user_bets_user_id ON user_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_placed_at ON user_bets(placed_at DESC);


-- === 4. SOCIAL FEATURES TABLES ===

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_follows (
    follower_id VARCHAR(50) NOT NULL,
    following_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id)
);

CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_user_follows_following ON user_follows(following_id);


-- === 5. WEATHER TABLES ===

CREATE TABLE IF NOT EXISTS fixture_weather (
    fixture_id VARCHAR(50) PRIMARY KEY,
    temperature INTEGER, -- Celsius
    condition VARCHAR(100), -- "Clear", "Rain", "Snow"
    rain_mm FLOAT,
    wind_kmh FLOAT,
    humidity INTEGER,
    fetched_at TIMESTAMP DEFAULT NOW()
);


-- === 6. H2H TABLES ===

CREATE TABLE IF NOT EXISTS h2h_matches (
    id SERIAL PRIMARY KEY,
    home_team_id VARCHAR(50),
    away_team_id VARCHAR(50),
    match_date DATE,
    home_score INTEGER,
    away_score INTEGER,
    btts BOOLEAN,
    total_goals INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_h2h_teams ON h2h_matches(home_team_id, away_team_id);


-- === VIEWS ===

-- User Bet Stats (leaderboard)
CREATE OR REPLACE VIEW user_bet_stats_view AS
SELECT 
    user_id,
    COUNT(*) as total_bets,
    SUM(stake) as total_stake,
    SUM(CASE WHEN status = 'won' THEN potential_return ELSE 0 END) as total_return,
    SUM(COALESCE(pnl, 0)) as total_pnl,
    (SUM(COALESCE(pnl, 0)) / NULLIF(SUM(stake), 0) * 100) as roi,
    (COUNT(CASE WHEN status = 'won' THEN 1 END)::float / NULLIF(COUNT(CASE WHEN status IN ('won', 'lost') THEN 1 END), 0) * 100) as win_rate
FROM user_bets
WHERE status IN ('won', 'lost')
GROUP BY user_id;


-- Live fixtures
CREATE OR REPLACE VIEW live_fixtures_view AS
SELECT 
    f.fixture_id,
    f.home_team_id,
    f.away_team_id,
    ht.name as home_team,
    at.name as away_team,
    ls.minute,
    ls.home_score,
    ls.away_score,
    ls.home_shots,
    ls.away_shots,
    ls.home_possession,
    ls.away_possession
FROM fixtures f
LEFT JOIN teams ht ON f.home_team_id = ht.team_id
LEFT JOIN teams at ON f.away_team_id = at.team_id
LEFT JOIN live_stats ls ON f.fixture_id = ls.fixture_id
WHERE f.status = 'live';


-- Best arbitrage opportunities (last 24h)
CREATE OR REPLACE VIEW best_arbitrage_opportunities AS
SELECT *
FROM arbitrage_history
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY profit_pct DESC
LIMIT 20;


-- === SAMPLE DATA ===

-- Live stats sample
INSERT INTO live_stats
(fixture_id, minute, home_score, away_score, home_shots, away_shots, home_possession, away_possession)
VALUES
('live_001', 67, 1, 0, 12, 8, 58, 42)
ON CONFLICT DO NOTHING;

-- Bookmaker odds sample
INSERT INTO bookmaker_odds
(fixture_id, bookmaker, market, outcome, odds)
VALUES
('fix_001', 'Bet365', '1X2', 'home', 1.95),
('fix_001', 'Bet365', '1X2', 'draw', 3.80),
('fix_001', 'Bet365', '1X2', 'away', 3.20),
('fix_001', 'Pinnacle', '1X2', 'home', 2.05),
('fix_001', 'Pinnacle', '1X2', 'draw', 3.60),
('fix_001', 'Pinnacle', '1X2', 'away', 3.10)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- Migration Complete!
-- ============================================================================

COMMENT ON SCHEMA public IS 'GOLEX Database - All 10 Features v1.0';

