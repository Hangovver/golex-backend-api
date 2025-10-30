-- 029_support.sql
CREATE TABLE IF NOT EXISTS user_support_events (
  id BIGSERIAL PRIMARY KEY,
  device_id TEXT NOT NULL,
  method TEXT NOT NULL, -- patreon|kofi|bank|other
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS user_support_badges (
  device_id TEXT NOT NULL,
  badge_key TEXT NOT NULL, -- supporter|super_supporter|founder etc.
  awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(device_id, badge_key)
);
