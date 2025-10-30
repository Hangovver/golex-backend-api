-- Migration: Add lineup tables
-- Version: 031
-- Description: Tables for storing match lineups and formations

-- Lineups table
CREATE TABLE IF NOT EXISTS lineups (
    id SERIAL PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    
    is_home BOOLEAN NOT NULL,
    
    -- Formation
    formation VARCHAR(10),  -- e.g., "4-3-3", "4-4-2"
    
    -- Shirt colors
    player_shirt_color VARCHAR(7),  -- Hex color
    goalkeeper_shirt_color VARCHAR(7),  -- Hex color
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(fixture_id, is_home)
);

-- Indexes for lineups
CREATE INDEX IF NOT EXISTS idx_lineups_fixture ON lineups(fixture_id);
CREATE INDEX IF NOT EXISTS idx_lineups_team ON lineups(team_id);
CREATE INDEX IF NOT EXISTS idx_lineups_formation ON lineups(formation);

-- Lineup players table
CREATE TABLE IF NOT EXISTS lineup_players (
    id SERIAL PRIMARY KEY,
    lineup_id INTEGER NOT NULL REFERENCES lineups(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    
    -- Position
    position VARCHAR(10),  -- GK, CB, CM, ST, etc.
    shirt_number INTEGER NOT NULL,
    
    -- Field position (0-100 percentage)
    position_x DECIMAL(5, 2),
    position_y DECIMAL(5, 2),
    
    -- Role
    is_starter BOOLEAN DEFAULT TRUE,
    is_captain BOOLEAN DEFAULT FALSE,
    
    -- Substitution
    was_substituted BOOLEAN DEFAULT FALSE,
    substituted_minute INTEGER,
    
    -- Rating
    rating DECIMAL(3, 1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(lineup_id, player_id)
);

-- Indexes for lineup_players
CREATE INDEX IF NOT EXISTS idx_lineup_players_lineup ON lineup_players(lineup_id);
CREATE INDEX IF NOT EXISTS idx_lineup_players_player ON lineup_players(player_id);
CREATE INDEX IF NOT EXISTS idx_lineup_players_position ON lineup_players(position);
CREATE INDEX IF NOT EXISTS idx_lineup_players_starter ON lineup_players(is_starter);

-- Comments
COMMENT ON TABLE lineups IS 'Team lineups for matches including formation and shirt colors';
COMMENT ON TABLE lineup_players IS 'Individual players in lineups with field positions';

