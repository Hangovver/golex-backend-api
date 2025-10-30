-- Migration: Add player and team statistics tables
-- Version: 030
-- Description: Tables for storing match-level player and team statistics

-- Player statistics table
CREATE TABLE IF NOT EXISTS player_statistics (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Basic info
    minutes_played INTEGER DEFAULT 0,
    position VARCHAR(10),
    
    -- Rating
    rating DECIMAL(3, 1),
    
    -- Attacking
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    big_chances_created INTEGER DEFAULT 0,
    big_chances_missed INTEGER DEFAULT 0,
    
    -- Passing
    passes_total INTEGER DEFAULT 0,
    passes_accurate INTEGER DEFAULT 0,
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    long_balls INTEGER DEFAULT 0,
    through_balls INTEGER DEFAULT 0,
    
    -- Dribbling
    dribbles_attempted INTEGER DEFAULT 0,
    dribbles_successful INTEGER DEFAULT 0,
    
    -- Defensive
    tackles INTEGER DEFAULT 0,
    tackles_won INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    blocked_shots INTEGER DEFAULT 0,
    
    -- Duels
    duels_total INTEGER DEFAULT 0,
    duels_won INTEGER DEFAULT 0,
    aerial_duels_total INTEGER DEFAULT 0,
    aerial_duels_won INTEGER DEFAULT 0,
    
    -- Discipline
    fouls_committed INTEGER DEFAULT 0,
    fouls_won INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    
    -- Other
    touches INTEGER DEFAULT 0,
    possession_lost INTEGER DEFAULT 0,
    distance_covered_km DECIMAL(4, 2),
    
    -- Goalkeeper specific
    saves INTEGER DEFAULT 0,
    saves_inside_box INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    punches INTEGER DEFAULT 0,
    high_claims INTEGER DEFAULT 0,
    successful_keeper_sweeper INTEGER DEFAULT 0,
    
    -- Errors
    errors_leading_to_goal INTEGER DEFAULT 0,
    errors_leading_to_shot INTEGER DEFAULT 0,
    
    -- Substitution
    was_substituted BOOLEAN DEFAULT FALSE,
    substituted_in_minute INTEGER,
    substituted_out_minute INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fixture_id, player_id)
);

-- Indexes for player_statistics
CREATE INDEX IF NOT EXISTS idx_player_stats_fixture ON player_statistics(fixture_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_statistics(team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_rating ON player_statistics(rating DESC);
CREATE INDEX IF NOT EXISTS idx_player_stats_goals ON player_statistics(goals DESC);

-- Team statistics table
CREATE TABLE IF NOT EXISTS team_statistics (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Possession
    possession_percentage INTEGER,
    
    -- xG
    expected_goals DECIMAL(4, 2),
    
    -- Shots
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_off_target INTEGER DEFAULT 0,
    shots_blocked INTEGER DEFAULT 0,
    shots_inside_box INTEGER DEFAULT 0,
    shots_outside_box INTEGER DEFAULT 0,
    
    -- Passing
    passes_total INTEGER DEFAULT 0,
    passes_accurate INTEGER DEFAULT 0,
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    long_balls INTEGER DEFAULT 0,
    
    -- Defensive
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    
    -- Set pieces
    corners INTEGER DEFAULT 0,
    free_kicks INTEGER DEFAULT 0,
    
    -- Discipline
    fouls_committed INTEGER DEFAULT 0,
    fouls_won INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fixture_id, team_id)
);

-- Indexes for team_statistics
CREATE INDEX IF NOT EXISTS idx_team_stats_fixture ON team_statistics(fixture_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_statistics(team_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_xg ON team_statistics(expected_goals DESC);
CREATE INDEX IF NOT EXISTS idx_team_stats_possession ON team_statistics(possession_percentage DESC);

-- Shots table (for shot map)
CREATE TABLE IF NOT EXISTS shots (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Timing
    minute INTEGER NOT NULL,
    
    -- Location (field percentage, 0-100)
    x DECIMAL(5, 2) NOT NULL,
    y DECIMAL(5, 2) NOT NULL,
    
    -- Shot details
    xg DECIMAL(4, 3),  -- Expected goal value (0.0-1.0)
    distance_to_goal DECIMAL(5, 2),  -- meters
    angle_to_goal DECIMAL(5, 2),  -- degrees
    
    -- Categorization
    situation VARCHAR(50),  -- open_play, corner, free_kick, penalty, counter_attack
    shot_type VARCHAR(50),  -- on_target, off_target, blocked, goal
    body_part VARCHAR(20),  -- right_foot, left_foot, head
    
    -- Context
    goalkeeper_out BOOLEAN DEFAULT FALSE,
    defender_pressure DECIMAL(3, 2),  -- 0.0-1.0
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for shots
CREATE INDEX IF NOT EXISTS idx_shots_fixture ON shots(fixture_id);
CREATE INDEX IF NOT EXISTS idx_shots_player ON shots(player_id);
CREATE INDEX IF NOT EXISTS idx_shots_team ON shots(team_id);
CREATE INDEX IF NOT EXISTS idx_shots_xg ON shots(xg DESC);
CREATE INDEX IF NOT EXISTS idx_shots_type ON shots(shot_type);

-- Event graph data (for attack momentum)
CREATE TABLE IF NOT EXISTS event_graph_data (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    
    minute DECIMAL(5, 2) NOT NULL,
    value DECIMAL(4, 3) NOT NULL,  -- -1.0 to 1.0
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fixture_id, minute)
);

-- Index for event_graph_data
CREATE INDEX IF NOT EXISTS idx_graph_data_fixture ON event_graph_data(fixture_id);
CREATE INDEX IF NOT EXISTS idx_graph_data_minute ON event_graph_data(fixture_id, minute);

-- Comments
COMMENT ON TABLE player_statistics IS 'Match-level player statistics for rating calculation and display';
COMMENT ON TABLE team_statistics IS 'Match-level team statistics including xG and possession';
COMMENT ON TABLE shots IS 'Individual shot data for shot map visualization';
COMMENT ON TABLE event_graph_data IS 'Minute-by-minute momentum data for attack momentum graph';

