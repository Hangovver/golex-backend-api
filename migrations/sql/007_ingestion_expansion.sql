-- 007_ingestion_expansion.sql
CREATE TABLE IF NOT EXISTS referees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS venues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  city TEXT NULL,
  country TEXT NULL,
  capacity INT NULL
);
ALTER TABLE fixtures
  ADD COLUMN IF NOT EXISTS referee_id UUID NULL,
  ADD COLUMN IF NOT EXISTS venue_id UUID NULL,
  ADD COLUMN IF NOT EXISTS ft_home INT NULL,
  ADD COLUMN IF NOT EXISTS ft_away INT NULL;

CREATE TABLE IF NOT EXISTS player_status (
  player_id UUID NOT NULL,
  team_id UUID NOT NULL,
  status TEXT NOT NULL, -- 'injured' | 'suspended'
  detail TEXT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (player_id, team_id, status)
);

CREATE TABLE IF NOT EXISTS team_form (
  team_id UUID PRIMARY KEY,
  last5 TEXT NOT NULL, -- e.g. 'WWDLW'
  gf INT NOT NULL DEFAULT 0,
  ga INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS h2h_cache (
  team_a UUID NOT NULL,
  team_b UUID NOT NULL,
  last_n INT NOT NULL DEFAULT 5,
  summary JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (team_a, team_b, last_n)
);
