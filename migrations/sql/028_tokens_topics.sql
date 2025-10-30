-- 028_tokens_topics.sql
CREATE TABLE IF NOT EXISTS user_device_tokens (
  device_id TEXT NOT NULL,
  token TEXT NOT NULL,
  platform TEXT NOT NULL DEFAULT 'android',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(device_id, token)
);

CREATE TABLE IF NOT EXISTS user_topic_subs (
  device_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY(device_id, topic)
);
CREATE INDEX IF NOT EXISTS idx_topic_topic ON user_topic_subs(topic);
