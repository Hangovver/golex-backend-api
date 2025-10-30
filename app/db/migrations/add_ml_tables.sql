-- ============================================================================
-- ML FEATURE ENGINEERING & PLAYER MODELING DATABASE SCHEMA
-- Supports LightGBM training and advanced feature extraction
-- ============================================================================

-- Player Injuries Table
CREATE TABLE IF NOT EXISTS player_injuries (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    injury_type VARCHAR(100),
    injury_start TIMESTAMP NOT NULL,
    expected_return TIMESTAMP,
    severity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX idx_player_injuries_player_id ON player_injuries(player_id);
CREATE INDEX idx_player_injuries_dates ON player_injuries(injury_start, expected_return);


-- Player Suspensions Table
CREATE TABLE IF NOT EXISTS player_suspensions (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    suspension_type VARCHAR(100),
    suspension_start TIMESTAMP NOT NULL,
    suspension_end TIMESTAMP NOT NULL,
    matches_remaining INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX idx_player_suspensions_player_id ON player_suspensions(player_id);
CREATE INDEX idx_player_suspensions_dates ON player_suspensions(suspension_start, suspension_end);


-- Player Match Stats Table (detailed per-match stats)
CREATE TABLE IF NOT EXISTS player_match_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    rating DECIMAL(3, 2),
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes INTEGER DEFAULT 0,
    passes_completed INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    
    UNIQUE (player_id, match_id)
);

CREATE INDEX idx_player_match_stats_player ON player_match_stats(player_id, match_date DESC);
CREATE INDEX idx_player_match_stats_team ON player_match_stats(team_id, match_date DESC);


-- Team Match Stats Table (advanced team stats per match)
CREATE TABLE IF NOT EXISTS team_match_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    match_date TIMESTAMP NOT NULL,
    xg_for DECIMAL(4, 2) DEFAULT 0.0,
    xg_against DECIMAL(4, 2) DEFAULT 0.0,
    shots_on_target_pct DECIMAL(5, 2) DEFAULT 0.0,
    possession DECIMAL(5, 2) DEFAULT 50.0,
    pass_accuracy DECIMAL(5, 2) DEFAULT 80.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    
    UNIQUE (team_id, match_id)
);

CREATE INDEX idx_team_match_stats_team ON team_match_stats(team_id, match_date DESC);


-- Team Tactical Stats Table (tactical style metrics)
CREATE TABLE IF NOT EXISTS team_tactical_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season VARCHAR(20) NOT NULL,
    shots_total DECIMAL(5, 2) DEFAULT 12.0,
    defensive_line_height DECIMAL(5, 2) DEFAULT 5.0,
    pressing_intensity DECIMAL(5, 2) DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    
    UNIQUE (team_id, season)
);

CREATE INDEX idx_team_tactical_stats_team ON team_tactical_stats(team_id);


-- Fixture Odds Table (bookmaker odds for Kelly Criterion)
CREATE TABLE IF NOT EXISTS fixture_odds (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    market_code VARCHAR(20) NOT NULL,
    odds DECIMAL(6, 2) NOT NULL,
    bookmaker VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX idx_fixture_odds_fixture ON fixture_odds(fixture_id);


-- Fixture Stats Table (xG and advanced stats)
CREATE TABLE IF NOT EXISTS fixture_stats (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    home_xg_for DECIMAL(4, 2) DEFAULT 1.5,
    home_xg_against DECIMAL(4, 2) DEFAULT 1.5,
    away_xg_for DECIMAL(4, 2) DEFAULT 1.5,
    away_xg_against DECIMAL(4, 2) DEFAULT 1.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    
    UNIQUE (fixture_id)
);

CREATE INDEX idx_fixture_stats_fixture ON fixture_stats(fixture_id);


-- Add fields to existing players table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='injured') THEN
        ALTER TABLE players ADD COLUMN injured BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='suspended') THEN
        ALTER TABLE players ADD COLUMN suspended BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='active') THEN
        ALTER TABLE players ADD COLUMN active BOOLEAN DEFAULT TRUE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='appearances') THEN
        ALTER TABLE players ADD COLUMN appearances INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='goals') THEN
        ALTER TABLE players ADD COLUMN goals INTEGER DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='players' AND column_name='assists') THEN
        ALTER TABLE players ADD COLUMN assists INTEGER DEFAULT 0;
    END IF;
END$$;


-- Add fields to existing teams table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='teams' AND column_name='city') THEN
        ALTER TABLE teams ADD COLUMN city VARCHAR(100);
    END IF;
END$$;


-- ML Model Training Metadata Table
CREATE TABLE IF NOT EXISTS ml_model_versions (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    training_date TIMESTAMP NOT NULL,
    accuracy DECIMAL(5, 4),
    log_loss DECIMAL(6, 4),
    brier_score DECIMAL(6, 4),
    training_samples INTEGER,
    test_samples INTEGER,
    feature_count INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (model_name, version)
);

CREATE INDEX idx_ml_model_versions_active ON ml_model_versions(model_name, is_active);


-- Comments for documentation
COMMENT ON TABLE player_injuries IS 'Tracks player injuries for impact modeling';
COMMENT ON TABLE player_suspensions IS 'Tracks player suspensions (cards, bans)';
COMMENT ON TABLE player_match_stats IS 'Detailed per-match player statistics for ML training';
COMMENT ON TABLE team_match_stats IS 'Advanced team statistics per match (xG, possession, etc.)';
COMMENT ON TABLE team_tactical_stats IS 'Team tactical style metrics for matchup analysis';
COMMENT ON TABLE fixture_odds IS 'Bookmaker odds for Kelly Criterion calculations';
COMMENT ON TABLE fixture_stats IS 'Advanced fixture statistics (xG data)';
COMMENT ON TABLE ml_model_versions IS 'ML model training metadata and versioning';

