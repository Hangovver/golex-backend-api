-- 012_search_index.sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS search_index (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  entity_type TEXT NOT NULL,      -- 'team'|'player'|'league'
  entity_id UUID NOT NULL,
  name TEXT NOT NULL,
  alt_names TEXT[] DEFAULT '{}',
  country TEXT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GIN index for fuzzy
CREATE INDEX IF NOT EXISTS idx_search_name_trgm ON search_index USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_search_alt_trgm ON search_index USING GIN (alt_names gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_search_country ON search_index (country);
CREATE INDEX IF NOT EXISTS idx_search_type ON search_index (entity_type);
