-- 023_push_topics.sql
CREATE TABLE IF NOT EXISTS user_push_tokens (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NULL,
  device_id TEXT NOT NULL,
  token TEXT NOT NULL UNIQUE,
  platform TEXT NOT NULL DEFAULT 'android',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_upt_user ON user_push_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_upt_device ON user_push_tokens(device_id);

CREATE TABLE IF NOT EXISTS user_topic_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NULL,
  token TEXT NULL,
  device_id TEXT NULL,
  topic TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_uts_user ON user_topic_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_uts_topic ON user_topic_subscriptions(topic);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_uts ON user_topic_subscriptions(COALESCE(token,''), COALESCE(device_id,''), topic);
