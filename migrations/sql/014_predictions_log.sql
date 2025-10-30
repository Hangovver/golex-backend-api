-- 014_predictions_log.sql
CREATE TABLE IF NOT EXISTS predictions_log (
  id BIGSERIAL PRIMARY KEY,
  fixture_id UUID NOT NULL,
  model_version TEXT NOT NULL,
  home_prob NUMERIC(6,5) NOT NULL,
  draw_prob NUMERIC(6,5) NOT NULL,
  away_prob NUMERIC(6,5) NOT NULL,
  outcome TEXT NOT NULL, -- 'home'|'draw'|'away'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pred_model ON predictions_log(model_version);
CREATE INDEX IF NOT EXISTS idx_pred_fixture ON predictions_log(fixture_id);
