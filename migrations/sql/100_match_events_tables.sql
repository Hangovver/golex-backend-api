-- Match Events and Statistics Tables
-- For attack momentum, player ratings, xG, shot maps

-- Match Events table (for timeline and momentum)
CREATE TABLE IF NOT EXISTS match_events (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- goal, shot, corner, attack, etc.
    event_class VARCHAR(50),          -- penalty, own_goal, red, yellow, etc.
    minute INTEGER NOT NULL,
    added_time INTEGER,
    
    -- Team/Player
    is_home BOOLEAN NOT NULL,
    player_id INTEGER REFERENCES players(id),
    player_in_id INTEGER REFERENCES players(id),   -- For substitutions
    player_out_id INTEGER REFERENCES players(id),  -- For substitutions
    
    -- Scores at time of event
    home_score INTEGER,
    away_score INTEGER,
    
    -- Additional data
    details JSONB,
    
    -- For attack momentum
    momentum_weight FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_match_events_fixture (fixture_id),
    INDEX idx_match_events_type (event_type),
    INDEX idx_match_events_minute (minute),
    INDEX idx_match_events_player (player_id)
);

-- Player Match Statistics (for ratings)
CREATE TABLE IF NOT EXISTS player_match_stats (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    
    -- Playing time
    minutes_played INTEGER DEFAULT 0,
    position VARCHAR(10),  -- GK, CB, CM, ST, etc.
    
    -- Rating (0.0-10.0)
    rating FLOAT,
    rating_color VARCHAR(20),  -- excellent, very_good, good, average, poor
    
    -- Positive actions
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    key_passes INTEGER DEFAULT 0,
    successful_passes INTEGER DEFAULT 0,
    total_passes INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_total INTEGER DEFAULT 0,
    tackles_won INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    dribbles_successful INTEGER DEFAULT 0,
    dribbles_attempted INTEGER DEFAULT 0,
    duels_won INTEGER DEFAULT 0,
    duels_total INTEGER DEFAULT 0,
    aerial_duels_won INTEGER DEFAULT 0,
    aerial_duels_total INTEGER DEFAULT 0,
    
    -- Negative actions
    goals_conceded INTEGER DEFAULT 0,
    errors_leading_to_goal INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    possession_lost INTEGER DEFAULT 0,
    
    -- Goalkeeper specific
    saves INTEGER DEFAULT 0,
    saves_inside_box INTEGER DEFAULT 0,
    punches INTEGER DEFAULT 0,
    high_claims INTEGER DEFAULT 0,
    
    -- Physical
    distance_covered_km FLOAT,
    touches INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_player_stats_fixture (fixture_id),
    INDEX idx_player_stats_player (player_id),
    INDEX idx_player_stats_team (team_id),
    UNIQUE (fixture_id, player_id)
);

-- Team Match Statistics
CREATE TABLE IF NOT EXISTS team_match_stats (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    
    -- Possession
    possession_percentage INTEGER,
    
    -- Expected Goals
    expected_goals FLOAT,  -- xG
    
    -- Shots
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_off_target INTEGER DEFAULT 0,
    shots_blocked INTEGER DEFAULT 0,
    shots_inside_box INTEGER DEFAULT 0,
    shots_outside_box INTEGER DEFAULT 0,
    
    -- Passes
    passes_total INTEGER DEFAULT 0,
    passes_accurate INTEGER DEFAULT 0,
    pass_accuracy_percentage INTEGER,
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    long_balls INTEGER DEFAULT 0,
    through_balls INTEGER DEFAULT 0,
    
    -- Defense
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    blocked_shots INTEGER DEFAULT 0,
    
    -- Discipline
    corners INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    fouls_won INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_team_stats_fixture (fixture_id),
    INDEX idx_team_stats_team (team_id),
    UNIQUE (fixture_id, team_id)
);

-- Shot Data (for shot maps and xG)
CREATE TABLE IF NOT EXISTS shot_data (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    
    -- Timing
    minute INTEGER NOT NULL,
    added_time INTEGER,
    
    -- Location (0-100 field percentage)
    x FLOAT NOT NULL,  -- 0=own goal, 100=opponent goal
    y FLOAT NOT NULL,  -- 0=left, 100=right
    
    -- Shot details
    distance_to_goal FLOAT,  -- meters
    angle_to_goal FLOAT,     -- degrees
    body_part VARCHAR(20),   -- head, right_foot, left_foot, weak_foot
    situation VARCHAR(50),   -- open_play, corner, free_kick, penalty, one_on_one
    shot_type VARCHAR(20),   -- on_target, off_target, blocked, goal
    
    -- xG
    xg_value FLOAT,  -- 0.0 to 1.0
    
    -- Context
    goalkeeper_out BOOLEAN DEFAULT FALSE,
    defender_pressure FLOAT DEFAULT 0.0,  -- 0.0 to 1.0
    
    -- Result
    is_goal BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_shot_data_fixture (fixture_id),
    INDEX idx_shot_data_player (player_id),
    INDEX idx_shot_data_team (team_id),
    INDEX idx_shot_data_minute (minute)
);

-- Comments
COMMENT ON TABLE match_events IS 'Timeline events for attack momentum and match flow';
COMMENT ON TABLE player_match_stats IS 'Player statistics and ratings for individual matches';
COMMENT ON TABLE team_match_stats IS 'Team-level match statistics';
COMMENT ON TABLE shot_data IS 'Individual shot data for shot maps and xG calculations';

COMMENT ON COLUMN match_events.momentum_weight IS 'Pre-calculated weight for momentum algorithm';
COMMENT ON COLUMN player_match_stats.rating IS 'Player rating 0.0-10.0 scale';
COMMENT ON COLUMN player_match_stats.rating_color IS 'Color category: excellent/very_good/good/average/poor';
COMMENT ON COLUMN shot_data.xg_value IS 'Expected goals value 0.0-1.0';

