-- 011_survey.sql
CREATE TABLE IF NOT EXISTS surveys (
  id SERIAL PRIMARY KEY,
  user_id UUID NULL,
  kind TEXT NOT NULL, -- 'NPS'|'CSAT'
  score INT NOT NULL,
  comment TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
