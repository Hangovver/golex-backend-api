-- Migration: Add users and favorites tables
-- Version: 032
-- Description: Tables for user accounts and favorites

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Favorites table
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Entity information
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('team', 'player', 'league', 'match')),
    entity_id INTEGER NOT NULL,
    entity_name VARCHAR(255),
    
    -- Notification settings
    notify_matches BOOLEAN DEFAULT TRUE,
    notify_goals BOOLEAN DEFAULT TRUE,
    notify_news BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, entity_type, entity_id)
);

-- Indexes for favorites
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_entity_type ON favorites(entity_type);
CREATE INDEX IF NOT EXISTS idx_favorites_user_type ON favorites(user_id, entity_type);

-- Comments
COMMENT ON TABLE users IS 'User accounts';
COMMENT ON TABLE favorites IS 'User favorites (teams, players, leagues)';

COMMENT ON COLUMN users.hashed_password IS 'Bcrypt hashed password';
COMMENT ON COLUMN favorites.entity_type IS 'Type: team, player, league, match';
COMMENT ON COLUMN favorites.entity_id IS 'ID of the favorited entity';

