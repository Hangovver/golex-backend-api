-- 009_favorites.sql
CREATE TABLE IF NOT EXISTS favorites (
  user_id UUID NOT NULL,
  fixture_id UUID NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, fixture_id)
);
