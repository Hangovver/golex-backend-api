-- GOLEX (P010–P015): PostgreSQL schema (uuid via pgcrypto), indexes
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- leagues
CREATE TABLE IF NOT EXISTS leagues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(120) NOT NULL,
  country VARCHAR(80),
  api_football_id INT UNIQUE,
  current_season_year INT
);
CREATE INDEX IF NOT EXISTS ix_leagues_name ON leagues(name);

-- seasons
CREATE TABLE IF NOT EXISTS seasons (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id uuid NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
  year INT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_seasons_league_year ON seasons(league_id, year);

-- teams
CREATE TABLE IF NOT EXISTS teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(140) NOT NULL,
  country VARCHAR(80),
  api_football_id INT UNIQUE
);
CREATE INDEX IF NOT EXISTS ix_teams_name ON teams(name);

-- players
CREATE TABLE IF NOT EXISTS players (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(140) NOT NULL,
  nationality VARCHAR(80),
  birthdate DATE,
  position VARCHAR(24),
  api_football_id INT UNIQUE
);
CREATE INDEX IF NOT EXISTS ix_players_name ON players(name);

-- coaches
CREATE TABLE IF NOT EXISTS coaches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(120) NOT NULL,
  nationality VARCHAR(80),
  api_football_id INT UNIQUE
);

-- venues
CREATE TABLE IF NOT EXISTS venues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(160) NOT NULL,
  city VARCHAR(120),
  country VARCHAR(80),
  capacity INT,
  api_football_id INT UNIQUE
);
CREATE INDEX IF NOT EXISTS ix_venues_name ON venues(name);

-- fixtures
CREATE TABLE IF NOT EXISTS fixtures (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id uuid NOT NULL REFERENCES leagues(id),
  season_id uuid NOT NULL REFERENCES seasons(id),
  home_team_id uuid NOT NULL REFERENCES teams(id),
  away_team_id uuid NOT NULL REFERENCES teams(id),
  venue_id uuid REFERENCES venues(id),
  starts_at_utc TIMESTAMP NOT NULL,
  status VARCHAR(24) NOT NULL,
  round VARCHAR(60),
  referee VARCHAR(120),
  api_football_id INT UNIQUE
);
CREATE INDEX IF NOT EXISTS ix_fixtures_league ON fixtures(league_id);
CREATE INDEX IF NOT EXISTS ix_fixtures_date_status ON fixtures(starts_at_utc, status);

-- events
CREATE TABLE IF NOT EXISTS events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fixture_id uuid NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  minute INT,
  team_id uuid REFERENCES teams(id),
  player_id uuid REFERENCES players(id),
  type VARCHAR(40) NOT NULL,
  detail VARCHAR(80),
  result VARCHAR(80)
);
CREATE INDEX IF NOT EXISTS ix_events_fixture ON events(fixture_id);

-- lineups + players
CREATE TABLE IF NOT EXISTS lineups (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fixture_id uuid NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  team_id uuid NOT NULL REFERENCES teams(id),
  coach_id uuid REFERENCES coaches(id),
  formation VARCHAR(24)
);
CREATE INDEX IF NOT EXISTS ix_lineups_fixture_team ON lineups(fixture_id, team_id);

CREATE TABLE IF NOT EXISTS lineup_players (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lineup_id uuid NOT NULL REFERENCES lineups(id) ON DELETE CASCADE,
  player_id uuid NOT NULL REFERENCES players(id),
  position VARCHAR(12),
  grid VARCHAR(8),
  is_starter INT DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_lineup_players_lineup ON lineup_players(lineup_id);

-- standings
CREATE TABLE IF NOT EXISTS standings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id uuid NOT NULL REFERENCES leagues(id),
  season_id uuid NOT NULL REFERENCES seasons(id),
  team_id uuid NOT NULL REFERENCES teams(id),
  rank INT NOT NULL,
  points INT NOT NULL,
  played INT NOT NULL,
  wins INT NOT NULL,
  draws INT NOT NULL,
  losses INT NOT NULL,
  goals_for INT NOT NULL,
  goals_against INT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_standings_league_season_rank ON standings(league_id, season_id, rank);

-- fixture team stats
CREATE TABLE IF NOT EXISTS fixture_team_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fixture_id uuid NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  team_id uuid NOT NULL REFERENCES teams(id),
  shots_total INT,
  shots_on INT,
  possession FLOAT,
  corners INT,
  yellow INT,
  red INT,
  xg FLOAT
);
CREATE INDEX IF NOT EXISTS ix_fixture_team_stats_fixture_team ON fixture_team_stats(fixture_id, team_id);
