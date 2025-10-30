-- 022_fixtures_cursor_idx.sql
CREATE INDEX IF NOT EXISTS idx_fixtures_cursor ON fixtures (starts_at_utc ASC, id ASC);
