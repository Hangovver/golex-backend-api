-- 004_model_monitoring.sql (P059)
CREATE TABLE IF NOT EXISTS predictions_log (
  id BIGSERIAL PRIMARY KEY,
  fixture_id uuid NOT NULL,
  served_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  p_home FLOAT NOT NULL,
  p_draw FLOAT NOT NULL,
  p_away FLOAT NOT NULL,
  top_class SMALLINT NOT NULL,  -- 0 home,1 draw,2 away
  model_version TEXT
);
CREATE INDEX IF NOT EXISTS ix_predictions_log_fixture ON predictions_log(fixture_id);

CREATE TABLE IF NOT EXISTS model_metrics_daily (
  day DATE PRIMARY KEY,
  served INT NOT NULL DEFAULT 0,
  correct INT NOT NULL DEFAULT 0,
  brier_sum FLOAT NOT NULL DEFAULT 0,
  ece FLOAT,
  notes TEXT
);
