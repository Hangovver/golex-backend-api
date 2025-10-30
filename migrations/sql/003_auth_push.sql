-- 003_auth_push.sql  (P030–P035)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(160) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  locale VARCHAR(8) DEFAULT 'tr'
);

CREATE TABLE IF NOT EXISTS device_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id),
  token VARCHAR(300) UNIQUE NOT NULL,
  platform VARCHAR(16) DEFAULT 'android',
  locale VARCHAR(8) DEFAULT 'tr'
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token_id uuid NOT NULL REFERENCES device_tokens(id) ON DELETE CASCADE,
  topic VARCHAR(120) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_subscription_token_topic ON subscriptions(token_id, topic);
