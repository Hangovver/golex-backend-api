-- 005_model_registry.sql
CREATE TABLE IF NOT EXISTS model_registry (
  id SERIAL PRIMARY KEY,
  version TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
-- Optional seed
INSERT INTO settings(key,value) VALUES ('accuracy_floor','0.50') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings(key,value) VALUES ('ece_ceil','0.12') ON CONFLICT (key) DO NOTHING;
