-- 024_predictions_shadow.sql
CREATE TABLE IF NOT EXISTS predictions_shadow_log (
  id BIGSERIAL PRIMARY KEY,
  fixture_id TEXT NOT NULL,
  prod_version TEXT NOT NULL,
  canary_version TEXT NOT NULL,
  prod JSONB NOT NULL,
  canary JSONB NOT NULL,
  l1 FLOAT8 NOT NULL,
  kl FLOAT8 NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_psl_fixture ON predictions_shadow_log(fixture_id);
CREATE INDEX IF NOT EXISTS idx_psl_created ON predictions_shadow_log(created_at);
