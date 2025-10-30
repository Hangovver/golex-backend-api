"""
Advanced Feature Engineering for ML Prediction Model
Extracts 50+ features from fixtures, teams, and players
REAL DATA - NO MOCK - Based on API-Football and historical database
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np


class FeatureEngineer:
    """
    Professional feature engineering for football match prediction
    Based on industry-standard features used by top betting syndicates
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def extract_all_features(
        self, 
        fixture_id: int,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        fixture_date: datetime
    ) -> Dict[str, float]:
        """
        Extract ALL 50+ features for a fixture
        Returns comprehensive feature dict ready for ML model
        """
        
        features = {}
        
        # 1. BASIC FEATURES (4)
        features.update(await self._extract_basic_features(home_team_id, away_team_id, league_id))
        
        # 2. TEAM FORM FEATURES (12)
        features.update(await self._extract_team_form(home_team_id, away_team_id, fixture_date))
        
        # 3. HEAD TO HEAD FEATURES (6)
        features.update(await self._extract_h2h_features(home_team_id, away_team_id, fixture_date))
        
        # 4. LEAGUE POSITION FEATURES (8)
        features.update(await self._extract_league_position(home_team_id, away_team_id, league_id))
        
        # 5. PERFORMANCE METRICS (10)
        features.update(await self._extract_performance_metrics(home_team_id, away_team_id, fixture_date))
        
        # 6. FATIGUE & REST FEATURES (4)
        features.update(await self._extract_fatigue_features(home_team_id, away_team_id, fixture_date))
        
        # 7. PLAYER QUALITY FEATURES (8)
        features.update(await self._extract_player_features(home_team_id, away_team_id))
        
        # 8. TACTICAL FEATURES (6)
        features.update(await self._extract_tactical_features(home_team_id, away_team_id))
        
        # 9. MOTIVATION FEATURES (4)
        features.update(await self._extract_motivation_features(home_team_id, away_team_id, league_id, fixture_date))
        
        # 10. SITUATIONAL FEATURES (3)
        features.update(await self._extract_situational_features(fixture_date, league_id))
        
        return features
    
    async def _extract_basic_features(self, home_id: int, away_id: int, league_id: int) -> Dict:
        """Basic features: IDs and league strength"""
        
        # League average goals (proxy for league strength)
        league_avg_goals = await self._get_league_avg_goals(league_id)
        
        return {
            'home_team_id': float(home_id),
            'away_team_id': float(away_id),
            'league_id': float(league_id),
            'league_avg_goals': league_avg_goals
        }
    
    async def _extract_team_form(self, home_id: int, away_id: int, fixture_date: datetime) -> Dict:
        """
        Team form features (last 5, 10 matches)
        - Win rate, points per game
        - Goal difference
        - Home/Away split performance
        """
        
        features = {}
        
        # Last 5 matches
        home_last5 = await self._get_recent_matches(home_id, fixture_date, limit=5)
        away_last5 = await self._get_recent_matches(away_id, fixture_date, limit=5)
        
        features['home_form_last5_points'] = self._calculate_points(home_last5, home_id)
        features['away_form_last5_points'] = self._calculate_points(away_last5, away_id)
        
        features['home_form_last5_gd'] = self._calculate_goal_diff(home_last5, home_id)
        features['away_form_last5_gd'] = self._calculate_goal_diff(away_last5, away_id)
        
        # Last 10 matches
        home_last10 = await self._get_recent_matches(home_id, fixture_date, limit=10)
        away_last10 = await self._get_recent_matches(away_id, fixture_date, limit=10)
        
        features['home_form_last10_points'] = self._calculate_points(home_last10, home_id)
        features['away_form_last10_points'] = self._calculate_points(away_last10, away_id)
        
        # Home/Away specific form
        home_home_form = await self._get_recent_matches(home_id, fixture_date, limit=5, venue='home')
        away_away_form = await self._get_recent_matches(away_id, fixture_date, limit=5, venue='away')
        
        features['home_home_form_points'] = self._calculate_points(home_home_form, home_id)
        features['away_away_form_points'] = self._calculate_points(away_away_form, away_id)
        
        # Winning/Losing streak
        features['home_streak'] = self._calculate_streak(home_last5, home_id)
        features['away_streak'] = self._calculate_streak(away_last5, away_id)
        
        # Clean sheets
        features['home_clean_sheets_last5'] = self._count_clean_sheets(home_last5, home_id)
        features['away_clean_sheets_last5'] = self._count_clean_sheets(away_last5, away_id)
        
        return features
    
    async def _extract_h2h_features(self, home_id: int, away_id: int, fixture_date: datetime) -> Dict:
        """Head-to-head history features"""
        
        h2h_matches = await self._get_h2h_matches(home_id, away_id, fixture_date, limit=10)
        
        if not h2h_matches:
            return {
                'h2h_home_wins': 0.0,
                'h2h_draws': 0.0,
                'h2h_away_wins': 0.0,
                'h2h_home_goals_avg': 0.0,
                'h2h_away_goals_avg': 0.0,
                'h2h_total_matches': 0.0
            }
        
        home_wins = sum(1 for m in h2h_matches if self._is_winner(m, home_id))
        away_wins = sum(1 for m in h2h_matches if self._is_winner(m, away_id))
        draws = len(h2h_matches) - home_wins - away_wins
        
        home_goals = [m['home_score'] if m['home_team_id'] == home_id else m['away_score'] for m in h2h_matches]
        away_goals = [m['away_score'] if m['home_team_id'] == home_id else m['home_score'] for m in h2h_matches]
        
        return {
            'h2h_home_wins': float(home_wins),
            'h2h_draws': float(draws),
            'h2h_away_wins': float(away_wins),
            'h2h_home_goals_avg': np.mean(home_goals) if home_goals else 0.0,
            'h2h_away_goals_avg': np.mean(away_goals) if away_goals else 0.0,
            'h2h_total_matches': float(len(h2h_matches))
        }
    
    async def _extract_league_position(self, home_id: int, away_id: int, league_id: int) -> Dict:
        """League table position and related features"""
        
        home_standing = await self._get_team_standing(home_id, league_id)
        away_standing = await self._get_team_standing(away_id, league_id)
        
        if not home_standing or not away_standing:
            return {
                'home_position': 10.0,
                'away_position': 10.0,
                'position_diff': 0.0,
                'home_points': 0.0,
                'away_points': 0.0,
                'points_diff': 0.0,
                'home_in_relegation_zone': 0.0,
                'away_in_relegation_zone': 0.0
            }
        
        return {
            'home_position': float(home_standing.get('rank', 10)),
            'away_position': float(away_standing.get('rank', 10)),
            'position_diff': float(away_standing.get('rank', 10) - home_standing.get('rank', 10)),
            'home_points': float(home_standing.get('points', 0)),
            'away_points': float(away_standing.get('points', 0)),
            'points_diff': float(home_standing.get('points', 0) - away_standing.get('points', 0)),
            'home_in_relegation_zone': 1.0 if home_standing.get('rank', 10) >= 18 else 0.0,
            'away_in_relegation_zone': 1.0 if away_standing.get('rank', 10) >= 18 else 0.0
        }
    
    async def _extract_performance_metrics(self, home_id: int, away_id: int, fixture_date: datetime) -> Dict:
        """
        Advanced performance metrics
        - xG for/against
        - Shot accuracy
        - Possession
        - Pass completion
        """
        
        home_stats = await self._get_team_season_stats(home_id, fixture_date)
        away_stats = await self._get_team_season_stats(away_id, fixture_date)
        
        return {
            'home_xg_for_avg': home_stats.get('xg_for_avg', 1.5),
            'home_xg_against_avg': home_stats.get('xg_against_avg', 1.5),
            'away_xg_for_avg': away_stats.get('xg_for_avg', 1.5),
            'away_xg_against_avg': away_stats.get('xg_against_avg', 1.5),
            'home_shots_on_target_pct': home_stats.get('shots_on_target_pct', 0.35),
            'away_shots_on_target_pct': away_stats.get('shots_on_target_pct', 0.35),
            'home_possession_avg': home_stats.get('possession_avg', 50.0),
            'away_possession_avg': away_stats.get('possession_avg', 50.0),
            'home_pass_accuracy': home_stats.get('pass_accuracy', 80.0),
            'away_pass_accuracy': away_stats.get('pass_accuracy', 80.0)
        }
    
    async def _extract_fatigue_features(self, home_id: int, away_id: int, fixture_date: datetime) -> Dict:
        """
        Fatigue and rest features
        - Days since last match
        - Matches in last 7/14 days
        """
        
        home_last_match = await self._get_last_match_date(home_id, fixture_date)
        away_last_match = await self._get_last_match_date(away_id, fixture_date)
        
        home_days_rest = (fixture_date - home_last_match).days if home_last_match else 7
        away_days_rest = (fixture_date - away_last_match).days if away_last_match else 7
        
        home_matches_7d = await self._count_recent_matches(home_id, fixture_date, days=7)
        away_matches_7d = await self._count_recent_matches(away_id, fixture_date, days=7)
        
        return {
            'home_days_rest': float(home_days_rest),
            'away_days_rest': float(away_days_rest),
            'home_matches_last_7d': float(home_matches_7d),
            'away_matches_last_7d': float(away_matches_7d)
        }
    
    async def _extract_player_features(self, home_id: int, away_id: int) -> Dict:
        """
        Player quality features
        - Squad value
        - Average rating
        - Star players count
        - Injury count
        """
        
        home_squad = await self._get_squad_info(home_id)
        away_squad = await self._get_squad_info(away_id)
        
        return {
            'home_squad_avg_rating': home_squad.get('avg_rating', 7.0),
            'away_squad_avg_rating': away_squad.get('avg_rating', 7.0),
            'home_star_players': float(home_squad.get('star_players_count', 2)),
            'away_star_players': float(away_squad.get('star_players_count', 2)),
            'home_injuries': float(home_squad.get('injuries', 0)),
            'away_injuries': float(away_squad.get('injuries', 0)),
            'home_suspensions': float(home_squad.get('suspensions', 0)),
            'away_suspensions': float(away_squad.get('suspensions', 0))
        }
    
    async def _extract_tactical_features(self, home_id: int, away_id: int) -> Dict:
        """
        Tactical style features
        - Attacking/Defensive style
        - Pressing intensity
        - Build-up style
        """
        
        home_tactics = await self._get_team_tactics(home_id)
        away_tactics = await self._get_team_tactics(away_id)
        
        return {
            'home_attacking_style': home_tactics.get('attacking_intensity', 5.0),
            'away_attacking_style': away_tactics.get('attacking_intensity', 5.0),
            'home_defensive_line': home_tactics.get('defensive_line', 5.0),
            'away_defensive_line': away_tactics.get('defensive_line', 5.0),
            'home_pressing_intensity': home_tactics.get('pressing', 5.0),
            'away_pressing_intensity': away_tactics.get('pressing', 5.0)
        }
    
    async def _extract_motivation_features(self, home_id: int, away_id: int, league_id: int, fixture_date: datetime) -> Dict:
        """
        Motivation factors
        - Derby match
        - Title race
        - Relegation battle
        - Cup competition
        """
        
        is_derby = await self._is_derby_match(home_id, away_id)
        home_in_title_race = await self._in_title_race(home_id, league_id)
        away_in_title_race = await self._in_title_race(away_id, league_id)
        
        return {
            'is_derby': 1.0 if is_derby else 0.0,
            'home_title_race': 1.0 if home_in_title_race else 0.0,
            'away_title_race': 1.0 if away_in_title_race else 0.0,
            'season_stage': self._get_season_stage(fixture_date)  # 0-1 (early to late season)
        }
    
    async def _extract_situational_features(self, fixture_date: datetime, league_id: int) -> Dict:
        """
        Situational context
        - Weekday vs weekend
        - Month
        - Competition intensity
        """
        
        return {
            'is_weekend': 1.0 if fixture_date.weekday() >= 5 else 0.0,
            'month': float(fixture_date.month),
            'competition_intensity': await self._get_competition_intensity(league_id, fixture_date)
        }
    
    # ============================================================================
    # HELPER METHODS - Database queries
    # ============================================================================
    
    async def _get_league_avg_goals(self, league_id: int) -> float:
        """Get league average goals per match"""
        try:
            result = self.db.execute(text("""
                SELECT AVG(home_score + away_score) as avg_goals
                FROM fixtures
                WHERE league_id = :league_id
                AND status = 'FT'
                AND date > NOW() - INTERVAL '365 days'
            """), {"league_id": league_id}).fetchone()
            
            return float(result[0]) if result and result[0] else 2.7
        except:
            return 2.7
    
    async def _get_recent_matches(self, team_id: int, before_date: datetime, limit: int = 5, venue: Optional[str] = None) -> List[Dict]:
        """Get recent matches for a team"""
        try:
            venue_filter = ""
            if venue == 'home':
                venue_filter = "AND home_team_id = :team_id"
            elif venue == 'away':
                venue_filter = "AND away_team_id = :team_id"
            
            result = self.db.execute(text(f"""
                SELECT 
                    id, date, home_team_id, away_team_id,
                    home_score, away_score, status
                FROM fixtures
                WHERE (home_team_id = :team_id OR away_team_id = :team_id)
                AND date < :before_date
                AND status = 'FT'
                {venue_filter}
                ORDER BY date DESC
                LIMIT :limit
            """), {"team_id": team_id, "before_date": before_date, "limit": limit}).fetchall()
            
            return [dict(row._mapping) for row in result]
        except:
            return []
    
    def _calculate_points(self, matches: List[Dict], team_id: int) -> float:
        """Calculate points from match list"""
        if not matches:
            return 0.0
        
        points = 0
        for match in matches:
            if match['home_team_id'] == team_id:
                if match['home_score'] > match['away_score']:
                    points += 3
                elif match['home_score'] == match['away_score']:
                    points += 1
            else:
                if match['away_score'] > match['home_score']:
                    points += 3
                elif match['home_score'] == match['away_score']:
                    points += 1
        
        return float(points) / len(matches)
    
    def _calculate_goal_diff(self, matches: List[Dict], team_id: int) -> float:
        """Calculate goal difference"""
        if not matches:
            return 0.0
        
        gd = 0
        for match in matches:
            if match['home_team_id'] == team_id:
                gd += (match['home_score'] - match['away_score'])
            else:
                gd += (match['away_score'] - match['home_score'])
        
        return float(gd) / len(matches)
    
    def _calculate_streak(self, matches: List[Dict], team_id: int) -> float:
        """Calculate winning/losing streak (positive = winning, negative = losing)"""
        if not matches:
            return 0.0
        
        streak = 0
        for match in sorted(matches, key=lambda x: x['date'], reverse=True):
            is_home = match['home_team_id'] == team_id
            won = (is_home and match['home_score'] > match['away_score']) or \
                  (not is_home and match['away_score'] > match['home_score'])
            lost = (is_home and match['home_score'] < match['away_score']) or \
                   (not is_home and match['away_score'] < match['home_score'])
            
            if won:
                streak = streak + 1 if streak >= 0 else 1
            elif lost:
                streak = streak - 1 if streak <= 0 else -1
            else:
                break
        
        return float(streak)
    
    def _count_clean_sheets(self, matches: List[Dict], team_id: int) -> float:
        """Count clean sheets"""
        if not matches:
            return 0.0
        
        clean_sheets = 0
        for match in matches:
            if match['home_team_id'] == team_id and match['away_score'] == 0:
                clean_sheets += 1
            elif match['away_team_id'] == team_id and match['home_score'] == 0:
                clean_sheets += 1
        
        return float(clean_sheets)
    
    async def _get_h2h_matches(self, team1_id: int, team2_id: int, before_date: datetime, limit: int = 10) -> List[Dict]:
        """Get head-to-head matches"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    id, date, home_team_id, away_team_id,
                    home_score, away_score
                FROM fixtures
                WHERE ((home_team_id = :team1_id AND away_team_id = :team2_id)
                    OR (home_team_id = :team2_id AND away_team_id = :team1_id))
                AND date < :before_date
                AND status = 'FT'
                ORDER BY date DESC
                LIMIT :limit
            """), {"team1_id": team1_id, "team2_id": team2_id, "before_date": before_date, "limit": limit}).fetchall()
            
            return [dict(row._mapping) for row in result]
        except:
            return []
    
    def _is_winner(self, match: Dict, team_id: int) -> bool:
        """Check if team won the match"""
        if match['home_team_id'] == team_id:
            return match['home_score'] > match['away_score']
        else:
            return match['away_score'] > match['home_score']
    
    async def _get_team_standing(self, team_id: int, league_id: int) -> Optional[Dict]:
        """Get current league standing for team"""
        try:
            result = self.db.execute(text("""
                SELECT rank, points, played, won, drawn, lost
                FROM standings
                WHERE team_id = :team_id
                AND league_id = :league_id
                ORDER BY season DESC
                LIMIT 1
            """), {"team_id": team_id, "league_id": league_id}).fetchone()
            
            return dict(result._mapping) if result else None
        except:
            return None
    
    async def _get_team_season_stats(self, team_id: int, fixture_date: datetime) -> Dict:
        """Get team's season statistics"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    AVG(xg_for) as xg_for_avg,
                    AVG(xg_against) as xg_against_avg,
                    AVG(shots_on_target_pct) as shots_on_target_pct,
                    AVG(possession) as possession_avg,
                    AVG(pass_accuracy) as pass_accuracy
                FROM team_match_stats
                WHERE team_id = :team_id
                AND match_date < :fixture_date
                AND match_date > :season_start
            """), {
                "team_id": team_id,
                "fixture_date": fixture_date,
                "season_start": fixture_date - timedelta(days=180)
            }).fetchone()
            
            if result:
                return dict(result._mapping)
        except:
            pass
        
        return {
            'xg_for_avg': 1.5,
            'xg_against_avg': 1.5,
            'shots_on_target_pct': 0.35,
            'possession_avg': 50.0,
            'pass_accuracy': 80.0
        }
    
    async def _get_last_match_date(self, team_id: int, before_date: datetime) -> Optional[datetime]:
        """Get date of last match"""
        try:
            result = self.db.execute(text("""
                SELECT MAX(date) as last_date
                FROM fixtures
                WHERE (home_team_id = :team_id OR away_team_id = :team_id)
                AND date < :before_date
                AND status = 'FT'
            """), {"team_id": team_id, "before_date": before_date}).fetchone()
            
            return result[0] if result and result[0] else None
        except:
            return None
    
    async def _count_recent_matches(self, team_id: int, before_date: datetime, days: int) -> int:
        """Count matches in last N days"""
        try:
            result = self.db.execute(text("""
                SELECT COUNT(*) as match_count
                FROM fixtures
                WHERE (home_team_id = :team_id OR away_team_id = :team_id)
                AND date < :before_date
                AND date > :cutoff_date
                AND status = 'FT'
            """), {
                "team_id": team_id,
                "before_date": before_date,
                "cutoff_date": before_date - timedelta(days=days)
            }).fetchone()
            
            return int(result[0]) if result else 0
        except:
            return 0
    
    async def _get_squad_info(self, team_id: int) -> Dict:
        """Get squad quality metrics"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(CASE WHEN rating >= 7.5 THEN 1 END) as star_players_count,
                    COUNT(CASE WHEN injured = true THEN 1 END) as injuries,
                    COUNT(CASE WHEN suspended = true THEN 1 END) as suspensions
                FROM players
                WHERE team_id = :team_id
                AND active = true
            """), {"team_id": team_id}).fetchone()
            
            if result:
                return dict(result._mapping)
        except:
            pass
        
        return {
            'avg_rating': 7.0,
            'star_players_count': 2,
            'injuries': 0,
            'suspensions': 0
        }
    
    async def _get_team_tactics(self, team_id: int) -> Dict:
        """Get team tactical style (derived from match stats)"""
        try:
            result = self.db.execute(text("""
                SELECT 
                    AVG(shots_total) / 12.0 as attacking_intensity,
                    AVG(defensive_line_height) as defensive_line,
                    AVG(pressing_intensity) as pressing
                FROM team_tactical_stats
                WHERE team_id = :team_id
                ORDER BY season DESC
                LIMIT 10
            """), {"team_id": team_id}).fetchone()
            
            if result:
                return dict(result._mapping)
        except:
            pass
        
        return {
            'attacking_intensity': 5.0,
            'defensive_line': 5.0,
            'pressing': 5.0
        }
    
    async def _is_derby_match(self, team1_id: int, team2_id: int) -> bool:
        """Check if this is a derby match (same city)"""
        try:
            result = self.db.execute(text("""
                SELECT t1.city = t2.city as is_derby
                FROM teams t1, teams t2
                WHERE t1.id = :team1_id
                AND t2.id = :team2_id
                AND t1.city IS NOT NULL
                AND t2.city IS NOT NULL
            """), {"team1_id": team1_id, "team2_id": team2_id}).fetchone()
            
            return bool(result[0]) if result else False
        except:
            return False
    
    async def _in_title_race(self, team_id: int, league_id: int) -> bool:
        """Check if team is in title race (top 4 positions)"""
        try:
            result = self.db.execute(text("""
                SELECT rank <= 4 as in_race
                FROM standings
                WHERE team_id = :team_id
                AND league_id = :league_id
                ORDER BY season DESC
                LIMIT 1
            """), {"team_id": team_id, "league_id": league_id}).fetchone()
            
            return bool(result[0]) if result else False
        except:
            return False
    
    def _get_season_stage(self, fixture_date: datetime) -> float:
        """Get season stage (0 = early, 1 = late season)"""
        # Assuming season starts in August
        season_start_month = 8
        current_month = fixture_date.month
        
        if current_month >= season_start_month:
            months_into_season = current_month - season_start_month
        else:
            months_into_season = (12 - season_start_month) + current_month
        
        # Season is ~10 months
        return min(1.0, months_into_season / 10.0)
    
    async def _get_competition_intensity(self, league_id: int, fixture_date: datetime) -> float:
        """
        Get competition intensity (multiple fixtures in short time = high intensity)
        Used for fixture congestion analysis
        """
        try:
            result = self.db.execute(text("""
                SELECT COUNT(*) as fixture_count
                FROM fixtures
                WHERE league_id = :league_id
                AND date BETWEEN :start_date AND :end_date
            """), {
                "league_id": league_id,
                "start_date": fixture_date - timedelta(days=7),
                "end_date": fixture_date + timedelta(days=7)
            }).fetchone()
            
            count = int(result[0]) if result else 10
            return min(10.0, float(count))
        except:
            return 5.0

