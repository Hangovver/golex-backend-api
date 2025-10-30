-- 019_ingestion_tables.sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS leagues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_id INT UNIQUE,
  name TEXT NOT NULL,
  country TEXT,
  season INT
);
CREATE TABLE IF NOT EXISTS teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_id INT UNIQUE,
  name TEXT NOT NULL,
  country TEXT
);
CREATE TABLE IF NOT EXISTS fixtures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_id INT UNIQUE,
  league_id UUID REFERENCES leagues(id) ON DELETE SET NULL,
  home_team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
  away_team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
  status TEXT,
  starts_at_utc TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_fixtures_time ON fixtures (starts_at_utc);
