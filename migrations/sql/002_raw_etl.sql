-- Raw ingest table for ETL (P020)
CREATE TABLE IF NOT EXISTS raw_ingest (
  id BIGSERIAL PRIMARY KEY,
  provider TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  key TEXT,
  payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_raw_ingest_provider_endpoint ON raw_ingest(provider, endpoint);
