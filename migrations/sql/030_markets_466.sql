-- Migration 030: 466 Markets System Support
-- Adds tables for xG stats and bookmaker odds

-- ==========================================
-- Table: fixture_stats
-- Stores xG (Expected Goals) statistics per fixture
-- ==========================================
CREATE TABLE IF NOT EXISTS fixture_stats (
    fixture_id VARCHAR(100) PRIMARY KEY,
    home_xg_for FLOAT DEFAULT 1.5,
    home_xg_against FLOAT DEFAULT 1.5,
    away_xg_for FLOAT DEFAULT 1.5,
    away_xg_against FLOAT DEFAULT 1.5,
    home_possession FLOAT DEFAULT 0.5,
    away_possession FLOAT DEFAULT 0.5,
    home_shots INT DEFAULT 0,
    away_shots INT DEFAULT 0,
    home_shots_on_target INT DEFAULT 0,
    away_shots_on_target INT DEFAULT 0,
    home_corners INT DEFAULT 0,
    away_corners INT DEFAULT 0,
    home_cards_yellow INT DEFAULT 0,
    away_cards_yellow INT DEFAULT 0,
    home_cards_red INT DEFAULT 0,
    away_cards_red INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_fixture_stats_fixture ON fixture_stats(fixture_id);

-- ==========================================
-- Table: fixture_odds
-- Stores bookmaker odds for various markets
-- ==========================================
CREATE TABLE IF NOT EXISTS fixture_odds (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR(100) NOT NULL,
    market_code VARCHAR(50) NOT NULL,
    bookmaker VARCHAR(50) DEFAULT 'bet365',
    odds FLOAT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (fixture_id, market_code, bookmaker)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_fixture_odds_fixture ON fixture_odds(fixture_id);
CREATE INDEX IF NOT EXISTS idx_fixture_odds_market ON fixture_odds(market_code);
CREATE INDEX IF NOT EXISTS idx_fixture_odds_fixture_market ON fixture_odds(fixture_id, market_code);

-- ==========================================
-- Table: predictions_cache
-- Caches 466 market predictions (60 second TTL)
-- ==========================================
CREATE TABLE IF NOT EXISTS predictions_cache (
    fixture_id VARCHAR(100) PRIMARY KEY,
    markets_json JSONB NOT NULL,
    model_version VARCHAR(50) DEFAULT 'dixon_coles_v1',
    confidence FLOAT DEFAULT 0.85,
    expected_goals_home FLOAT,
    expected_goals_away FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '60 seconds')
);

-- Index for auto-cleanup
CREATE INDEX IF NOT EXISTS idx_predictions_cache_expires ON predictions_cache(expires_at);

-- ==========================================
-- Table: market_results
-- Stores actual match results for market validation
-- ==========================================
CREATE TABLE IF NOT EXISTS market_results (
    id SERIAL PRIMARY KEY,
    fixture_id VARCHAR(100) NOT NULL,
    market_code VARCHAR(50) NOT NULL,
    predicted_probability FLOAT,
    actual_result BOOLEAN NOT NULL,
    odds FLOAT,
    stake FLOAT,
    profit FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_market_results_fixture ON market_results(fixture_id);
CREATE INDEX IF NOT EXISTS idx_market_results_market ON market_results(market_code);
CREATE INDEX IF NOT EXISTS idx_market_results_created ON market_results(created_at DESC);

-- ==========================================
-- Table: user_bets
-- Tracks user betting history for performance analysis
-- ==========================================
CREATE TABLE IF NOT EXISTS user_bets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    fixture_id VARCHAR(100) NOT NULL,
    market_code VARCHAR(50) NOT NULL,
    odds FLOAT NOT NULL,
    stake FLOAT NOT NULL,
    predicted_probability FLOAT,
    strategy VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'kelly_half', 'kelly_quarter', etc.
    result VARCHAR(20),  -- 'pending', 'won', 'lost', 'void'
    profit FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    settled_at TIMESTAMP,
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

-- Indexes for user analytics
CREATE INDEX IF NOT EXISTS idx_user_bets_user ON user_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_fixture ON user_bets(fixture_id);
CREATE INDEX IF NOT EXISTS idx_user_bets_result ON user_bets(result);
CREATE INDEX IF NOT EXISTS idx_user_bets_created ON user_bets(created_at DESC);

-- ==========================================
-- View: user_bet_stats
-- Quick stats for user betting performance
-- ==========================================
CREATE OR REPLACE VIEW user_bet_stats AS
SELECT 
    user_id,
    COUNT(*) as total_bets,
    COUNT(CASE WHEN result = 'won' THEN 1 END) as wins,
    COUNT(CASE WHEN result = 'lost' THEN 1 END) as losses,
    ROUND(COUNT(CASE WHEN result = 'won' THEN 1 END)::NUMERIC / NULLIF(COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END), 0) * 100, 2) as win_rate_pct,
    ROUND(SUM(stake)::NUMERIC, 2) as total_staked,
    ROUND(SUM(CASE WHEN result = 'won' THEN profit ELSE 0 END)::NUMERIC, 2) as total_won,
    ROUND(SUM(CASE WHEN result = 'lost' THEN -stake ELSE 0 END)::NUMERIC, 2) as total_lost,
    ROUND(SUM(profit)::NUMERIC, 2) as net_profit,
    ROUND((SUM(profit) / NULLIF(SUM(stake), 0) * 100)::NUMERIC, 2) as roi_pct
FROM user_bets
WHERE result IN ('won', 'lost')
GROUP BY user_id;

-- ==========================================
-- View: market_performance
-- Track which markets perform best
-- ==========================================
CREATE OR REPLACE VIEW market_performance AS
SELECT 
    market_code,
    COUNT(*) as total_predictions,
    COUNT(CASE WHEN actual_result = true THEN 1 END) as hits,
    ROUND(COUNT(CASE WHEN actual_result = true THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as accuracy_pct,
    ROUND(AVG(predicted_probability)::NUMERIC, 3) as avg_predicted_prob,
    ROUND(AVG(CASE WHEN actual_result = true THEN 1.0 ELSE 0.0 END)::NUMERIC, 3) as avg_actual_prob,
    ROUND(SUM(CASE WHEN actual_result = true THEN profit ELSE -stake END)::NUMERIC, 2) as total_profit,
    ROUND((SUM(CASE WHEN actual_result = true THEN profit ELSE -stake END) / NULLIF(SUM(stake), 0) * 100)::NUMERIC, 2) as roi_pct
FROM market_results
GROUP BY market_code
ORDER BY total_predictions DESC;

-- ==========================================
-- Function: cleanup_expired_cache
-- Auto-cleanup expired predictions cache
-- ==========================================
CREATE OR REPLACE FUNCTION cleanup_expired_predictions_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM predictions_cache
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- Sample Data (Optional - for testing)
-- ==========================================

-- Insert sample fixture_stats
INSERT INTO fixture_stats (fixture_id, home_xg_for, home_xg_against, away_xg_for, away_xg_against, home_possession, away_possession)
VALUES 
    ('12345', 1.8, 1.2, 1.6, 1.3, 0.55, 0.45),
    ('12346', 2.1, 0.9, 1.1, 1.8, 0.62, 0.38),
    ('12347', 1.4, 1.5, 1.5, 1.4, 0.50, 0.50)
ON CONFLICT (fixture_id) DO NOTHING;

-- Insert sample odds
INSERT INTO fixture_odds (fixture_id, market_code, bookmaker, odds)
VALUES 
    ('12345', 'KG_YES', 'bet365', 1.85),
    ('12345', 'O2.5', 'bet365', 1.65),
    ('12345', '1X2', 'bet365', 2.10),
    ('12346', 'KG_YES', 'pinnacle', 1.80),
    ('12346', 'O2.5', 'pinnacle', 1.70),
    ('12347', 'KG_YES', 'betfair', 1.90),
    ('12347', 'O2.5', 'betfair', 1.60)
ON CONFLICT (fixture_id, market_code, bookmaker) DO NOTHING;

-- ==========================================
-- Grants (adjust for your user)
-- ==========================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON fixture_stats TO golex_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON fixture_odds TO golex_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON predictions_cache TO golex_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON market_results TO golex_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_bets TO golex_api;
-- GRANT SELECT ON user_bet_stats TO golex_api;
-- GRANT SELECT ON market_performance TO golex_api;

-- ==========================================
-- Comments
-- ==========================================
COMMENT ON TABLE fixture_stats IS '466 Markets: xG and match statistics';
COMMENT ON TABLE fixture_odds IS '466 Markets: Bookmaker odds for various markets';
COMMENT ON TABLE predictions_cache IS '466 Markets: Cached predictions (60s TTL)';
COMMENT ON TABLE market_results IS '466 Markets: Actual results for validation';
COMMENT ON TABLE user_bets IS 'User betting history for performance tracking';
COMMENT ON VIEW user_bet_stats IS 'User betting performance statistics';
COMMENT ON VIEW market_performance IS 'Market prediction accuracy and profitability';

-- Migration complete!


