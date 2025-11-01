-- ============================================================================
-- PROFESSIONAL BETTING SYNDICATE SYSTEM - COMPLETE DATABASE SCHEMA
-- All tables required for Tony Bloom / Smartodds level system
-- NO SIMPLIFICATION - Production-ready schema
-- ============================================================================

-- ============================================================================
-- 1. ELO RATING SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_elo_ratings (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    date TIMESTAMP NOT NULL,
    elo_rating DECIMAL(8, 2) DEFAULT 1500.0,
    matches_played INTEGER DEFAULT 0,
    k_factor DECIMAL(4, 2) DEFAULT 20.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE (team_id, date)
);

CREATE INDEX idx_team_elo_team_date ON team_elo_ratings(team_id, date DESC);
CREATE INDEX idx_team_elo_rating ON team_elo_ratings(elo_rating DESC);

COMMENT ON TABLE team_elo_ratings IS 'ELO rating history for teams (FiveThirtyEight style)';


-- ============================================================================
-- 2. REFEREE STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS referees (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    nationality VARCHAR(100),
    experience_years INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_referees_name ON referees(name);

CREATE TABLE IF NOT EXISTS referee_match_stats (
    id SERIAL PRIMARY KEY,
    referee_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    league_id INTEGER,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    fouls_called INTEGER DEFAULT 0,
    home_cards INTEGER DEFAULT 0,
    away_cards INTEGER DEFAULT 0,
    penalties_awarded INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (referee_id) REFERENCES referees(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    UNIQUE (referee_id, match_id)
);

CREATE INDEX idx_referee_stats_referee ON referee_match_stats(referee_id, match_date DESC);
CREATE INDEX idx_referee_stats_league ON referee_match_stats(league_id);

COMMENT ON TABLE referee_match_stats IS 'Detailed referee statistics per match';


-- Add missing columns to fixtures table
DO $$
BEGIN
    -- Add date column (used by data ingestion)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fixtures' AND column_name='date') THEN
        ALTER TABLE fixtures ADD COLUMN date TIMESTAMP;
    END IF;
    
    -- Add season column (if not exists)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fixtures' AND column_name='season') THEN
        ALTER TABLE fixtures ADD COLUMN season INTEGER;
    END IF;
    
    -- Add venue column (if not exists)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fixtures' AND column_name='venue') THEN
        ALTER TABLE fixtures ADD COLUMN venue VARCHAR(200);
    END IF;
    
    -- Add round column (if not exists)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fixtures' AND column_name='round') THEN
        ALTER TABLE fixtures ADD COLUMN round VARCHAR(100);
    END IF;
    
    -- Add referee_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fixtures' AND column_name='referee_id') THEN
        ALTER TABLE fixtures ADD COLUMN referee_id INTEGER;
        ALTER TABLE fixtures ADD CONSTRAINT fk_fixtures_referee 
            FOREIGN KEY (referee_id) REFERENCES referees(id) ON DELETE SET NULL;
    END IF;
END$$;

-- Add missing columns to teams table
DO $$
BEGIN
    -- Add logo column (used by data ingestion)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='logo') THEN
        ALTER TABLE teams ADD COLUMN logo TEXT;
    END IF;
END$$;


-- ============================================================================
-- 3. WEATHER DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS fixture_weather (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    temperature DECIMAL(4, 1),          -- Celsius
    wind_speed DECIMAL(5, 2),           -- km/h
    rain_probability DECIMAL(3, 2),     -- 0-1
    snow BOOLEAN DEFAULT FALSE,
    humidity DECIMAL(5, 2),             -- %
    pressure DECIMAL(6, 2),             -- hPa
    weather_condition VARCHAR(100),     -- Clear, Cloudy, Rain, etc.
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    UNIQUE (fixture_id)
);

CREATE INDEX idx_fixture_weather_fixture ON fixture_weather(fixture_id);

COMMENT ON TABLE fixture_weather IS 'Weather conditions at match time (OpenWeather API)';


-- ============================================================================
-- 4. TEAM STADIUM & LOCATION
-- ============================================================================

-- Add stadium location fields to teams table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='stadium_lat') THEN
        ALTER TABLE teams ADD COLUMN stadium_lat DECIMAL(10, 7);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='stadium_lon') THEN
        ALTER TABLE teams ADD COLUMN stadium_lon DECIMAL(10, 7);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='stadium_name') THEN
        ALTER TABLE teams ADD COLUMN stadium_name VARCHAR(200);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='stadium_capacity') THEN
        ALTER TABLE teams ADD COLUMN stadium_capacity INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='timezone') THEN
        ALTER TABLE teams ADD COLUMN timezone VARCHAR(50);
    END IF;
END$$;


-- ============================================================================
-- 5. BETTING MARKET DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS betting_odds_history (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    bookmaker VARCHAR(100),
    market_type VARCHAR(50),            -- 1X2, O/U 2.5, BTTS, etc.
    odds_home DECIMAL(6, 2),
    odds_draw DECIMAL(6, 2),
    odds_away DECIMAL(6, 2),
    odds_value DECIMAL(6, 2),           -- For non-1X2 markets
    timestamp TIMESTAMP NOT NULL,
    is_closing_line BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX idx_betting_odds_fixture ON betting_odds_history(fixture_id, timestamp DESC);
CREATE INDEX idx_betting_odds_closing ON betting_odds_history(fixture_id, is_closing_line) 
    WHERE is_closing_line = TRUE;

COMMENT ON TABLE betting_odds_history IS 'Betting odds movements over time';


-- ============================================================================
-- 6. GOALKEEPER STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS goalkeeper_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    season VARCHAR(20) NOT NULL,
    saves_total INTEGER DEFAULT 0,
    shots_faced INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    penalties_faced INTEGER DEFAULT 0,
    penalties_saved INTEGER DEFAULT 0,
    distribution_accuracy DECIMAL(5, 2) DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE (player_id, season)
);

CREATE INDEX idx_gk_stats_player ON goalkeeper_stats(player_id);

COMMENT ON TABLE goalkeeper_stats IS 'Detailed goalkeeper statistics';


-- ============================================================================
-- 7. SET PIECE STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_setpiece_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season VARCHAR(20) NOT NULL,
    corners_total INTEGER DEFAULT 0,
    corners_scored INTEGER DEFAULT 0,
    freekicks_total INTEGER DEFAULT 0,
    freekicks_scored INTEGER DEFAULT 0,
    penalties_total INTEGER DEFAULT 0,
    penalties_scored INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE (team_id, season)
);

CREATE INDEX idx_setpiece_stats_team ON team_setpiece_stats(team_id);

COMMENT ON TABLE team_setpiece_stats IS 'Set piece conversion statistics';


-- ============================================================================
-- 8. MANAGER DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS managers (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    nationality VARCHAR(100),
    birth_date DATE,
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_managers_name ON managers(name);

CREATE TABLE IF NOT EXISTS team_manager_history (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    manager_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    matches_coached INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE
);

CREATE INDEX idx_manager_history_team ON team_manager_history(team_id, start_date DESC);
CREATE INDEX idx_manager_history_manager ON team_manager_history(manager_id);

COMMENT ON TABLE team_manager_history IS 'Manager tenure and performance history';


-- ============================================================================
-- 9. DATA INGESTION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_ingestion_log (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,     -- 'fixtures', 'elo_update', 'referee_stats', etc.
    status VARCHAR(20) NOT NULL,        -- 'pending', 'running', 'success', 'failed'
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ingestion_log_type ON data_ingestion_log(task_type, created_at DESC);
CREATE INDEX idx_ingestion_log_status ON data_ingestion_log(status);

COMMENT ON TABLE data_ingestion_log IS 'Tracking for data ingestion tasks';


-- ============================================================================
-- 10. MODEL METADATA & VERSIONING
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,    -- 'lightgbm', 'xgboost', 'neural_network', 'ensemble'
    version VARCHAR(20) NOT NULL,
    training_date TIMESTAMP NOT NULL,
    training_samples INTEGER,
    test_samples INTEGER,
    accuracy DECIMAL(5, 4),
    log_loss DECIMAL(6, 4),
    brier_score DECIMAL(6, 4),
    feature_count INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    model_path TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (model_name, version)
);

CREATE INDEX idx_ml_registry_active ON ml_model_registry(model_name, is_active);
CREATE INDEX idx_ml_registry_date ON ml_model_registry(training_date DESC);

COMMENT ON TABLE ml_model_registry IS 'ML model versioning and metadata';


-- ============================================================================
-- 11. FEATURE CACHE (for faster predictions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS feature_cache (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    feature_set VARCHAR(50) NOT NULL,   -- 'basic', 'advanced', 'player_impact'
    features JSONB NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    UNIQUE (fixture_id, feature_set)
);

CREATE INDEX idx_feature_cache_fixture ON feature_cache(fixture_id);
CREATE INDEX idx_feature_cache_expires ON feature_cache(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON TABLE feature_cache IS 'Cached feature computations for performance';


-- ============================================================================
-- INITIAL DATA SEEDING
-- ============================================================================

-- Insert default ELO ratings for all existing teams (1500 starting ELO)
INSERT INTO team_elo_ratings (team_id, date, elo_rating, matches_played)
SELECT 
    id as team_id,
    CURRENT_TIMESTAMP as date,
    1500.0 as elo_rating,
    0 as matches_played
FROM teams
ON CONFLICT (team_id, date) DO NOTHING;


-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to auto-expire feature cache after 24 hours
CREATE OR REPLACE FUNCTION set_feature_cache_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at := NEW.computed_at + INTERVAL '24 hours';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_feature_cache_expiry
    BEFORE INSERT ON feature_cache
    FOR EACH ROW
    EXECUTE FUNCTION set_feature_cache_expiry();


-- Function to cleanup old cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM feature_cache 
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Current ELO ratings view
CREATE OR REPLACE VIEW current_team_elo AS
SELECT DISTINCT ON (team_id)
    team_id,
    elo_rating,
    matches_played,
    date as updated_at
FROM team_elo_ratings
ORDER BY team_id, date DESC;

COMMENT ON VIEW current_team_elo IS 'Latest ELO rating for each team';


-- Referee performance summary view
CREATE OR REPLACE VIEW referee_performance_summary AS
SELECT 
    r.id as referee_id,
    r.name,
    COUNT(*) as total_matches,
    AVG(rms.yellow_cards + rms.red_cards) as avg_cards_per_match,
    AVG(rms.fouls_called) as avg_fouls_per_match,
    AVG(CASE WHEN rms.home_cards < rms.away_cards THEN 1.0 ELSE 0.0 END) as home_bias_score,
    MAX(rms.match_date) as last_match_date
FROM referees r
JOIN referee_match_stats rms ON rms.referee_id = r.id
GROUP BY r.id, r.name;

COMMENT ON VIEW referee_performance_summary IS 'Aggregated referee statistics';


-- ============================================================================
-- GRANTS (if using role-based access)
-- ============================================================================

-- Grant SELECT on all tables to app user
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO golex_app;
-- GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO golex_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO golex_app;


-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Professional Betting Syndicate Database Schema Complete!';
    RAISE NOTICE '📊 Tables Created: ELO ratings, Referee stats, Weather, Betting odds, GK stats, Set pieces, Managers';
    RAISE NOTICE '🚀 Views Created: current_team_elo, referee_performance_summary';
    RAISE NOTICE '⚡ Triggers Created: Feature cache auto-expiry';
    RAISE NOTICE '💾 Initial Data: Default ELO ratings seeded';
END$$;


