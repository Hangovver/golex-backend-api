-- 017_fixtures_indexes.sql
CREATE INDEX IF NOT EXISTS idx_fix_date ON fixtures (DATE(starts_at_utc));
CREATE INDEX IF NOT EXISTS idx_fix_status ON fixtures (status);
CREATE INDEX IF NOT EXISTS idx_fix_country ON fixtures (country);
CREATE INDEX IF NOT EXISTS idx_fix_league ON fixtures (league_id);
