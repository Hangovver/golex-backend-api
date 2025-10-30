-- 015_dsr_requests.sql
CREATE TABLE IF NOT EXISTS dsr_requests (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NULL,
  kind TEXT NOT NULL,   -- 'export'|'delete'
  status TEXT NOT NULL DEFAULT 'received', -- 'received'|'done'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dsr_kind ON dsr_requests(kind);
CREATE INDEX IF NOT EXISTS idx_dsr_status ON dsr_requests(status);
