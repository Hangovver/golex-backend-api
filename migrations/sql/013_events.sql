-- 013_events.sql
CREATE TABLE IF NOT EXISTS raw_events (
  id BIGSERIAL PRIMARY KEY,
  fixture_id UUID NOT NULL,
  team_id UUID NULL,
  player_id UUID NULL,
  minute INT NOT NULL,
  second INT DEFAULT 0,
  x NUMERIC(5,2) NULL,  -- 0..100
  y NUMERIC(5,2) NULL,  -- 0..100
  type TEXT NOT NULL,   -- 'pass'|'shot'|'foul'|'card'|'corner'...
  subtype TEXT NULL,
  outcome TEXT NULL,    -- 'complete'|'incomplete'|'goal'...
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_fixture ON raw_events(fixture_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON raw_events(type);
