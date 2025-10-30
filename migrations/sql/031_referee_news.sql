-- ============================================================================
-- GOLEX - Referee Stats & News/Injury Migration
-- ============================================================================
-- Created: 2025-10-27
-- Purpose: Hakem istatistikleri ve sakatlık/haber veritabanı tabloları
-- ============================================================================

-- === 1. REFEREE MATCH DATA ===
-- Hakem maç verileri (her maç sonrası güncellenir)

CREATE TABLE IF NOT EXISTS referee_match_data (
    referee_id VARCHAR(50) NOT NULL,
    referee_name VARCHAR(200) NOT NULL,
    fixture_id VARCHAR(50) NOT NULL,
    match_date TIMESTAMP NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    
    -- İstatistikler
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    penalties INTEGER DEFAULT 0,
    total_goals INTEGER DEFAULT 0,
    home_won BOOLEAN DEFAULT FALSE,
    
    -- Meta
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (referee_id, fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_referee_match_referee_id ON referee_match_data(referee_id);
CREATE INDEX IF NOT EXISTS idx_referee_match_fixture_id ON referee_match_data(fixture_id);
CREATE INDEX IF NOT EXISTS idx_referee_match_league_id ON referee_match_data(league_id);
CREATE INDEX IF NOT EXISTS idx_referee_match_date ON referee_match_data(match_date DESC);

COMMENT ON TABLE referee_match_data IS 'Hakem maç verileri - her maç sonrası güncellenir';
COMMENT ON COLUMN referee_match_data.home_won IS 'Ev sahibi kazandı mı? (home bias hesaplamak için)';


-- === 2. PLAYER INJURIES ===
-- Oyuncu sakatlık verileri

CREATE TABLE IF NOT EXISTS player_injuries (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    
    -- Sakatlık bilgisi
    status VARCHAR(20) NOT NULL, -- healthy, doubtful, injured, suspended
    injury_type VARCHAR(100), -- muscle, knee, ankle vb.
    severity VARCHAR(20), -- minor, moderate, major, season_ending
    expected_return TIMESTAMP, -- Dönüş tarihi (tahmini)
    last_match TIMESTAMP, -- Son oynadığı maç
    
    -- Kaynak
    source VARCHAR(50) NOT NULL, -- transfermarkt, twitter, official
    confidence FLOAT NOT NULL DEFAULT 0.8, -- 0.0-1.0
    
    -- Meta
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_injuries_team_id ON player_injuries(team_id);
CREATE INDEX IF NOT EXISTS idx_player_injuries_league_id ON player_injuries(league_id);
CREATE INDEX IF NOT EXISTS idx_player_injuries_status ON player_injuries(status);
CREATE INDEX IF NOT EXISTS idx_player_injuries_expected_return ON player_injuries(expected_return);

COMMENT ON TABLE player_injuries IS 'Oyuncu sakatlık verileri - Transfermarkt/Twitter/RSS';
COMMENT ON COLUMN player_injuries.confidence IS 'Bilgi güvenilirliği (0.0-1.0)';


-- === 3. NEWS ITEMS ===
-- Haber öğeleri (Twitter, RSS, vb.)

CREATE TABLE IF NOT EXISTS news_items (
    news_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(50) NOT NULL, -- twitter, rss, official
    published_at TIMESTAMP NOT NULL,
    
    -- İlişkiler
    fixture_id VARCHAR(50), -- Hangi maçla ilgili
    team_ids VARCHAR(50)[] DEFAULT '{}', -- İlgili takımlar
    player_ids VARCHAR(50)[] DEFAULT '{}', -- İlgili oyuncular
    
    -- Analiz
    keywords VARCHAR(100)[] DEFAULT '{}', -- Anahtar kelimeler
    importance FLOAT NOT NULL DEFAULT 0.5, -- 0.0-1.0
    
    -- Meta
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_items_fixture_id ON news_items(fixture_id);
CREATE INDEX IF NOT EXISTS idx_news_items_source ON news_items(source);
CREATE INDEX IF NOT EXISTS idx_news_items_published_at ON news_items(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_items_team_ids ON news_items USING GIN(team_ids);
CREATE INDEX IF NOT EXISTS idx_news_items_player_ids ON news_items USING GIN(player_ids);

COMMENT ON TABLE news_items IS 'Haber öğeleri - Twitter/RSS/Resmi kaynaklar';
COMMENT ON COLUMN news_items.importance IS 'Haber önemi (0.0-1.0) - tahminlere etkisi';


-- === 4. NOTIFICATIONS ===
-- Kullanıcı bildirimleri (sakatlık, haber vb.)

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- injury_update, news_alert, lineup_change
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    
    -- İlişkiler
    fixture_id VARCHAR(50),
    team_id VARCHAR(50),
    player_id VARCHAR(50),
    
    -- Durum
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    
    -- Meta
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_fixture_id ON notifications(fixture_id);
CREATE INDEX IF NOT EXISTS idx_notifications_team_id ON notifications(team_id);
CREATE INDEX IF NOT EXISTS idx_notifications_player_id ON notifications(player_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_sent ON notifications(is_sent);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

COMMENT ON TABLE notifications IS 'Kullanıcı bildirimleri - sakatlık/haber/kadro';


-- === 5. PLAYER MATCH STATS ===
-- Oyuncu maç istatistikleri (xG contribution hesaplamak için)

CREATE TABLE IF NOT EXISTS player_match_stats (
    player_id VARCHAR(50) NOT NULL,
    fixture_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    match_date TIMESTAMP NOT NULL,
    
    -- İstatistikler
    xg FLOAT DEFAULT 0.0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    minutes_played INTEGER DEFAULT 0,
    
    -- Meta
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (player_id, fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_player_match_stats_player_id ON player_match_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_team_id ON player_match_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_match_date ON player_match_stats(match_date DESC);

COMMENT ON TABLE player_match_stats IS 'Oyuncu maç istatistikleri - xG contribution';


-- === 6. TEAMS TABLE (eğer yoksa) ===
-- Takım bilgileri

CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    short_name VARCHAR(50),
    logo_url VARCHAR(500),
    league_id VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_league_id ON teams(league_id);


-- === 7. FIXTURES TABLE (eğer yoksa) ===
-- Maç bilgileri

CREATE TABLE IF NOT EXISTS fixtures (
    fixture_id VARCHAR(50) PRIMARY KEY,
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    league_id VARCHAR(50) NOT NULL,
    match_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, live, finished
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fixtures_home_team_id ON fixtures(home_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_away_team_id ON fixtures(away_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_league_id ON fixtures(league_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_match_date ON fixtures(match_date DESC);


-- === 8. VIEWS ===

-- Hakem istatistikleri özeti (son 20 maç)
CREATE OR REPLACE VIEW referee_stats_summary AS
SELECT 
    referee_id,
    referee_name,
    COUNT(*) as total_matches,
    ROUND(AVG(yellow_cards + red_cards)::numeric, 2) as avg_cards_per_match,
    ROUND(AVG(yellow_cards)::numeric, 2) as avg_yellow_per_match,
    ROUND(AVG(red_cards)::numeric, 2) as avg_red_per_match,
    ROUND((SUM(red_cards)::float / COUNT(*)::float * 100)::numeric, 1) as red_card_percentage,
    ROUND(AVG(penalties)::numeric, 2) as avg_penalties_per_match,
    ROUND(AVG(total_goals)::numeric, 2) as avg_goals_per_match,
    ROUND((SUM(CASE WHEN home_won THEN 1 ELSE 0 END)::float / COUNT(*)::float)::numeric, 3) as home_win_rate
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY referee_id ORDER BY match_date DESC) as rn
    FROM referee_match_data
) sub
WHERE rn <= 20
GROUP BY referee_id, referee_name;

COMMENT ON VIEW referee_stats_summary IS 'Hakem istatistikleri özeti - son 20 maç';


-- Aktif sakatlıklar (dönüş tarihi gelmemiş veya belirsiz)
CREATE OR REPLACE VIEW active_injuries AS
SELECT 
    pi.*,
    t.name as team_name_full,
    t.logo_url as team_logo
FROM player_injuries pi
LEFT JOIN teams t ON pi.team_id = t.team_id
WHERE pi.status IN ('injured', 'doubtful', 'suspended')
AND (pi.expected_return IS NULL OR pi.expected_return >= NOW())
ORDER BY pi.updated_at DESC;

COMMENT ON VIEW active_injuries IS 'Aktif sakatlıklar - dönüş tarihi gelmemiş';


-- Son 24 saat haberleri
CREATE OR REPLACE VIEW recent_news AS
SELECT 
    ni.*,
    CASE 
        WHEN ni.fixture_id IS NOT NULL THEN 'match_news'
        WHEN array_length(ni.player_ids, 1) > 0 THEN 'player_news'
        WHEN array_length(ni.team_ids, 1) > 0 THEN 'team_news'
        ELSE 'general_news'
    END as news_category
FROM news_items ni
WHERE ni.published_at >= NOW() - INTERVAL '24 hours'
ORDER BY ni.importance DESC, ni.published_at DESC;

COMMENT ON VIEW recent_news IS 'Son 24 saat haberleri - önem sırasına göre';


-- === 9. TRIGGERS ===

-- updated_at otomatik güncelleme
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_referee_match_data_updated_at
    BEFORE UPDATE ON referee_match_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_injuries_updated_at
    BEFORE UPDATE ON player_injuries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- === 10. SAMPLE DATA (Testing) ===

-- Örnek hakem verisi
INSERT INTO referee_match_data 
(referee_id, referee_name, fixture_id, match_date, league_id, yellow_cards, red_cards, penalties, total_goals, home_won)
VALUES
('ref_12345', 'Halil Umut Meler', 'fix_001', NOW() - INTERVAL '7 days', 'league_1', 5, 1, 1, 3, true),
('ref_12345', 'Halil Umut Meler', 'fix_002', NOW() - INTERVAL '14 days', 'league_1', 6, 0, 0, 2, false),
('ref_12345', 'Halil Umut Meler', 'fix_003', NOW() - INTERVAL '21 days', 'league_1', 4, 1, 1, 4, true)
ON CONFLICT DO NOTHING;

-- Örnek sakatlık verisi
INSERT INTO player_injuries
(player_id, player_name, team_id, team_name, league_id, status, injury_type, severity, source, confidence)
VALUES
('player_001', 'Edin Dzeko', 'team_fb', 'Fenerbahçe', 'league_1', 'injured', 'muscle', 'moderate', 'transfermarkt', 0.9),
('player_002', 'Mauro Icardi', 'team_gs', 'Galatasaray', 'league_1', 'doubtful', 'knee', 'minor', 'twitter', 0.7)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- Migration Complete!
-- ============================================================================

COMMENT ON SCHEMA public IS 'GOLEX Database - Referee Stats & News/Injury System v1.0';

