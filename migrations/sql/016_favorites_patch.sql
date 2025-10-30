-- 016_favorites_patch.sql
ALTER TABLE IF EXISTS favorites ADD COLUMN IF NOT EXISTS device_id TEXT;
ALTER TABLE IF EXISTS favorites ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_fav_updated ON favorites(updated_at);
