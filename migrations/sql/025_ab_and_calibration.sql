-- 025_ab_and_calibration.sql
CREATE TABLE IF NOT EXISTS ab_config (
  id SMALLINT PRIMARY KEY DEFAULT 1,
  perc_b REAL NOT NULL DEFAULT 10.0,
  canary_version TEXT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO ab_config(id, perc_b) VALUES (1, 10.0)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS ab_assignments (
  device_id TEXT PRIMARY KEY,
  bucket CHAR(1) NOT NULL CHECK (bucket IN ('A','B')),
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS calibration_events (
  id BIGSERIAL PRIMARY KEY,
  fixture_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  p_home REAL NOT NULL,
  p_draw REAL NOT NULL,
  p_away REAL NOT NULL,
  outcome CHAR(1) NOT NULL CHECK (outcome IN ('H','D','A')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cal_events_ver ON calibration_events(model_version);
CREATE INDEX IF NOT EXISTS idx_cal_events_fixture ON calibration_events(fixture_id);
CREATE INDEX IF NOT EXISTS idx_cal_events_created ON calibration_events(created_at);
