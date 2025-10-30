-- 026_favorites.sql
CREATE TABLE IF NOT EXISTS user_device_favorites (
  device_id TEXT NOT NULL,
  team_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(device_id, team_id)
);
