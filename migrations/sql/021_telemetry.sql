-- 021_telemetry.sql
CREATE TABLE IF NOT EXISTS telemetry (id BIGSERIAL PRIMARY KEY, type TEXT NOT NULL, props JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS idx_tel_type ON telemetry(type);
CREATE INDEX IF NOT EXISTS idx_tel_created ON telemetry(created_at);
