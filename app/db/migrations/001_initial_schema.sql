-- ============================================================================
-- GOLEX INITIAL DATABASE SCHEMA
-- Core tables for football data
-- ============================================================================

-- ============================================================================
-- 1. LEAGUES
-- ============================================================================

CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    logo_url TEXT,
    season VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leagues_country ON leagues(country);
CREATE INDEX idx_leagues_name ON leagues(name);

COMMENT ON TABLE leagues IS 'Football leagues and competitions';


-- ============================================================================
-- 2. TEAMS
-- ============================================================================

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(10),
    country VARCHAR(100),
    founded INTEGER,
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_teams_name ON teams(name);
CREATE INDEX idx_teams_country ON teams(country);

COMMENT ON TABLE teams IS 'Football teams';


-- ============================================================================
-- 3. PLAYERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    name VARCHAR(200) NOT NULL,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    age INTEGER,
    birth_date DATE,
    nationality VARCHAR(100),
    height VARCHAR(20),
    weight VARCHAR(20),
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_nationality ON players(nationality);

COMMENT ON TABLE players IS 'Football players';


-- ============================================================================
-- 4. FIXTURES (MATCHES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fixtures (
    id SERIAL PRIMARY KEY,
    api_football_id INTEGER UNIQUE,
    league_id INTEGER,
    season VARCHAR(20),
    match_date TIMESTAMP NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(50),
    status_short VARCHAR(10),
    elapsed INTEGER,
    venue VARCHAR(200),
    round VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE SET NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE INDEX idx_fixtures_date ON fixtures(match_date DESC);
CREATE INDEX idx_fixtures_league ON fixtures(league_id);
CREATE INDEX idx_fixtures_home_team ON fixtures(home_team_id);
CREATE INDEX idx_fixtures_away_team ON fixtures(away_team_id);
CREATE INDEX idx_fixtures_status ON fixtures(status);

COMMENT ON TABLE fixtures IS 'Football matches/fixtures';


-- ============================================================================
-- 5. PLAYER STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_statistics (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    fixture_id INTEGER,
    season VARCHAR(20),
    minutes_played INTEGER DEFAULT 0,
    rating DECIMAL(3, 2),
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes_total INTEGER DEFAULT 0,
    passes_key INTEGER DEFAULT 0,
    passes_accuracy INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    duels_total INTEGER DEFAULT 0,
    duels_won INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE
);

CREATE INDEX idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX idx_player_stats_fixture ON player_statistics(fixture_id);
CREATE INDEX idx_player_stats_season ON player_statistics(season);

COMMENT ON TABLE player_statistics IS 'Player performance statistics';


-- ============================================================================
-- 6. TEAM STATISTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_statistics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    fixture_id INTEGER NOT NULL,
    possession INTEGER,
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_off_target INTEGER DEFAULT 0,
    corners INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    fouls INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    passes_total INTEGER DEFAULT 0,
    passes_accurate INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    UNIQUE (team_id, fixture_id)
);

CREATE INDEX idx_team_stats_team ON team_statistics(team_id);
CREATE INDEX idx_team_stats_fixture ON team_statistics(fixture_id);

COMMENT ON TABLE team_statistics IS 'Team match statistics';


-- ============================================================================
-- 7. STANDINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS standings (
    id SERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL,
    season VARCHAR(20) NOT NULL,
    team_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    points INTEGER DEFAULT 0,
    played INTEGER DEFAULT 0,
    win INTEGER DEFAULT 0,
    draw INTEGER DEFAULT 0,
    lose INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_diff INTEGER DEFAULT 0,
    form VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE (league_id, season, team_id)
);

CREATE INDEX idx_standings_league_season ON standings(league_id, season);
CREATE INDEX idx_standings_rank ON standings(rank);

COMMENT ON TABLE standings IS 'League standings/table';


-- ============================================================================
-- 8. MATCH EVENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS match_events (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    player_id INTEGER,
    time_elapsed INTEGER NOT NULL,
    time_extra INTEGER,
    event_type VARCHAR(50) NOT NULL,
    event_detail VARCHAR(100),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE SET NULL
);

CREATE INDEX idx_match_events_fixture ON match_events(fixture_id, time_elapsed);
CREATE INDEX idx_match_events_type ON match_events(event_type);

COMMENT ON TABLE match_events IS 'Match events (goals, cards, substitutions)';


-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Initial Database Schema Complete!';
    RAISE NOTICE '📊 Tables Created: leagues, teams, players, fixtures, player_statistics, team_statistics, standings, match_events';
    RAISE NOTICE '🚀 Ready for professional betting system migration!';
END$$;

