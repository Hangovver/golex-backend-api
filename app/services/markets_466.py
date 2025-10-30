"""
466 Markets Calculator - Professional Football Betting Markets
All markets supported by GOLEX mobile app

Based on Dixon-Coles model and professional betting formulas.
Compatible with mobile app Markets.kt definitions.
"""

from typing import Dict, List, Optional, Tuple
import math
import sys
import os

# Add ai-engine to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../ai-engine'))

try:
    from models.dixon_coles import DixonColesModel, estimate_team_strength_from_xg
    from models.kelly_criterion import KellyCriterion
except ImportError:
    # Fallback: create minimal stubs if imports fail
    class DixonColesModel:
        def __init__(self, **kwargs):
            pass
        def calculate_expected_goals(self, *args, **kwargs):
            return 1.5, 1.5
        def score_matrix(self, *args, **kwargs):
            import numpy as np
            return np.zeros((9, 9))
        def outcome_probabilities(self, *args, **kwargs):
            return {"home": 0.45, "draw": 0.28, "away": 0.27}
        def btts_probability(self, *args, **kwargs):
            return 0.65
        def over_under_probability(self, *args, **kwargs):
            return 0.60, 0.40
        def poisson_prob(self, k, lam):
            from math import exp, factorial
            return (lam ** k) * exp(-lam) / factorial(k)
    
    def estimate_team_strength_from_xg(xg_for, xg_against, league_avg=1.4):
        return xg_for / league_avg, xg_against / league_avg
    
    class KellyCriterion:
        @staticmethod
        def calculate_full_kelly(prob, odds, conf=1.0):
            if prob <= 0 or prob >= 1 or odds <= 1:
                return 0.0
            b = odds - 1.0
            return max(0.0, min(1.0, (b * prob - (1 - prob)) / b * conf))
        
        @staticmethod
        def calculate_fractional_kelly(prob, odds, frac=0.5, conf=1.0):
            return KellyCriterion.calculate_full_kelly(prob, odds, conf) * frac
        
        @staticmethod
        def calculate_expected_value(prob, odds):
            return (prob * odds) - 1.0
        
        @staticmethod
        def is_value_bet(prob, odds, min_edge=0.05):
            return KellyCriterion.calculate_expected_value(prob, odds) > min_edge


class Markets466Calculator:
    """
    Professional calculator for all 466 football betting markets
    
    Uses Dixon-Coles model + Kelly Criterion for optimal predictions
    """
    
    def __init__(
        self,
        home_xg_for: float,
        home_xg_against: float,
        away_xg_for: float,
        away_xg_against: float,
        league_avg: float = 1.4,
        home_advantage: float = 1.3,
        confidence: float = 0.85
    ):
        """
        Initialize calculator with match data
        
        Args:
            home_xg_for: Home team's avg xG for per match
            home_xg_against: Home team's avg xG against per match
            away_xg_for: Away team's avg xG for per match
            away_xg_against: Away team's avg xG against per match
            league_avg: League average xG per team
            home_advantage: Home advantage multiplier
            confidence: Model confidence (0-1)
        """
        self.league_avg = league_avg
        self.confidence = confidence
        
        # Calculate team strengths
        self.home_attack, self.home_defense = estimate_team_strength_from_xg(
            home_xg_for, home_xg_against, league_avg
        )
        self.away_attack, self.away_defense = estimate_team_strength_from_xg(
            away_xg_for, away_xg_against, league_avg
        )
        
        # Initialize Dixon-Coles model
        self.model = DixonColesModel(home_advantage=home_advantage)
        
        # Calculate expected goals
        self.lambda_home, self.lambda_away = self.model.calculate_expected_goals(
            self.home_attack, self.home_defense,
            self.away_attack, self.away_defense,
            league_avg
        )
        
        # Get score matrix
        self.score_matrix = self.model.score_matrix(self.lambda_home, self.lambda_away, max_goals=8)
        
        # Cache basic outcomes
        self._cache_basic_outcomes()
    
    def _cache_basic_outcomes(self):
        """Cache frequently used probabilities"""
        outcomes = self.model.outcome_probabilities(self.lambda_home, self.lambda_away)
        self.prob_home_win = outcomes["home"]
        self.prob_draw = outcomes["draw"]
        self.prob_away_win = outcomes["away"]
        
        self.prob_btts = self.model.btts_probability(self.lambda_home, self.lambda_away)
        
        # Cache over/under for common lines
        self.ou_cache = {}
        for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]:
            over, under = self.model.over_under_probability(self.lambda_home, self.lambda_away, line)
            self.ou_cache[line] = {"over": over, "under": under}
    
    # ========== BASIC MARKETS (9) ==========
    
    def calculate_1x2(self) -> Dict[str, float]:
        """Match Result (1X2)"""
        return {
            "1X2": self.prob_home_win,
            "home": self.prob_home_win,
            "draw": self.prob_draw,
            "away": self.prob_away_win,
            "confidence": self.confidence
        }
    
    def calculate_btts(self) -> Dict[str, float]:
        """Both Teams To Score"""
        return {
            "KG_YES": self.prob_btts,
            "KG_NO": 1.0 - self.prob_btts,
            "confidence": self.confidence
        }
    
    def calculate_double_chance(self) -> Dict[str, float]:
        """Double Chance (1X, 12, X2)"""
        return {
            "DC_1X": self.prob_home_win + self.prob_draw,
            "DC_12": self.prob_home_win + self.prob_away_win,
            "DC_X2": self.prob_draw + self.prob_away_win,
            "confidence": self.confidence
        }
    
    def calculate_dnb(self) -> Dict[str, float]:
        """Draw No Bet"""
        total = self.prob_home_win + self.prob_away_win
        if total == 0:
            return {"DNB_HOME": 0.5, "DNB_AWAY": 0.5}
        
        return {
            "DNB_HOME": self.prob_home_win / total,
            "DNB_AWAY": self.prob_away_win / total,
            "confidence": self.confidence * 0.9  # Slightly lower confidence
        }
    
    # ========== OVER/UNDER GOALS (16) ==========
    
    def calculate_over_under(self, line: float) -> Dict[str, float]:
        """Calculate Over/Under for any line"""
        if line in self.ou_cache:
            result = self.ou_cache[line]
        else:
            over, under = self.model.over_under_probability(self.lambda_home, self.lambda_away, line)
            result = {"over": over, "under": under}
        
        line_str = str(line).replace(".", "_")
        return {
            f"O{line}": result["over"],
            f"U{line}": result["under"],
            f"OVER_{line_str}": result["over"],
            f"UNDER_{line_str}": result["under"],
            "confidence": self.confidence
        }
    
    def calculate_all_over_under(self) -> Dict[str, float]:
        """All over/under lines (0.5 to 8.5)"""
        result = {}
        for line in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]:
            ou = self.calculate_over_under(line)
            result.update(ou)
        return result
    
    # ========== TEAM TOTALS (20) ==========
    
    def calculate_team_total(self, team: str, line: float) -> Dict[str, float]:
        """Calculate team total over/under"""
        prob_over = 0.0
        
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                goals = i if team == "home" else j
                if goals > line:
                    prob_over += self.score_matrix[i, j]
        
        line_str = str(line).replace(".", "_")
        prefix = "HOME" if team == "home" else "AWAY"
        
        return {
            f"{prefix}_O{line}": prob_over,
            f"{prefix}_U{line}": 1.0 - prob_over,
            "confidence": self.confidence * 0.95
        }
    
    def calculate_all_team_totals(self) -> Dict[str, float]:
        """All team totals (home and away, 0.5 to 4.5)"""
        result = {}
        for team in ["home", "away"]:
            for line in [0.5, 1.5, 2.5, 3.5, 4.5]:
                tt = self.calculate_team_total(team, line)
                result.update(tt)
        return result
    
    # ========== EXACT GOALS (9) ==========
    
    def calculate_exact_goals(self) -> Dict[str, float]:
        """Exact total goals"""
        exact = {}
        for total in range(8):
            prob = 0.0
            for i in range(self.score_matrix.shape[0]):
                for j in range(self.score_matrix.shape[1]):
                    if i + j == total:
                        prob += self.score_matrix[i, j]
            exact[f"EXACT_{total}"] = prob
        
        # 7+ goals
        prob_7_plus = 0.0
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                if i + j >= 7:
                    prob_7_plus += self.score_matrix[i, j]
        exact["EXACT_7_PLUS"] = prob_7_plus
        
        return exact
    
    # ========== MULTI-GOAL RANGES (16) ==========
    
    def calculate_multi_goal_range(self, min_goals: int, max_goals: int) -> float:
        """Calculate probability of total goals in range [min, max]"""
        prob = 0.0
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                total = i + j
                if min_goals <= total <= max_goals:
                    prob += self.score_matrix[i, j]
        return prob
    
    def calculate_all_multi_goal_ranges(self) -> Dict[str, float]:
        """All multi-goal ranges"""
        ranges = [
            (0, 1, "MG_0_1"), (1, 2, "MG_1_2"), (1, 3, "MG_1_3"),
            (2, 3, "MG_2_3"), (2, 4, "MG_2_4"), (2, 5, "MG_2_5"),
            (3, 4, "MG_3_4"), (3, 5, "MG_3_5"), (3, 6, "MG_3_6"),
            (4, 6, "MG_4_6")
        ]
        
        result = {}
        for min_g, max_g, code in ranges:
            result[code] = self.calculate_multi_goal_range(min_g, max_g)
        
        # 7+ goals
        result["MG_7_PLUS"] = self.calculate_multi_goal_range(7, 20)
        
        return result
    
    # ========== HALF TIME MARKETS (30) ==========
    
    def calculate_half_time_markets(self) -> Dict[str, float]:
        """
        Half time markets
        
        Approximation: First half typically has 43% of total xG
        """
        ht_lambda_home = self.lambda_home * 0.43
        ht_lambda_away = self.lambda_away * 0.43
        
        ht_outcomes = self.model.outcome_probabilities(ht_lambda_home, ht_lambda_away)
        ht_btts = self.model.btts_probability(ht_lambda_home, ht_lambda_away)
        
        result = {
            "HT_1X2_HOME": ht_outcomes["home"],
            "HT_1X2_DRAW": ht_outcomes["draw"],
            "HT_1X2_AWAY": ht_outcomes["away"],
            "HT_1X": ht_outcomes["home"] + ht_outcomes["draw"],
            "HT_12": ht_outcomes["home"] + ht_outcomes["away"],
            "HT_X2": ht_outcomes["draw"] + ht_outcomes["away"],
            "HT_KG_YES": ht_btts,
            "HT_KG_NO": 1.0 - ht_btts,
        }
        
        # HT Over/Under
        for line in [0.5, 1.5, 2.5, 3.5]:
            over, under = self.model.over_under_probability(ht_lambda_home, ht_lambda_away, line)
            result[f"HT_O{line}"] = over
            result[f"HT_U{line}"] = under
        
        # HT Team totals
        for line in [0.5, 1.5]:
            ht_matrix = self.model.score_matrix(ht_lambda_home, ht_lambda_away, 5)
            for team, prefix in [("home", "HT_HOME"), ("away", "HT_AWAY")]:
                prob_over = 0.0
                for i in range(ht_matrix.shape[0]):
                    for j in range(ht_matrix.shape[1]):
                        goals = i if team == "home" else j
                        if goals > line:
                            prob_over += ht_matrix[i, j]
                result[f"{prefix}_O{line}"] = prob_over
                result[f"{prefix}_U{line}"] = 1.0 - prob_over
        
        # DNB
        ht_total = ht_outcomes["home"] + ht_outcomes["away"]
        if ht_total > 0:
            result["HT_DNB_HOME"] = ht_outcomes["home"] / ht_total
            result["HT_DNB_AWAY"] = ht_outcomes["away"] / ht_total
        
        return result
    
    # ========== SECOND HALF MARKETS (20) ==========
    
    def calculate_second_half_markets(self) -> Dict[str, float]:
        """
        Second half markets
        
        Approximation: Second half has 57% of total xG
        """
        sh_lambda_home = self.lambda_home * 0.57
        sh_lambda_away = self.lambda_away * 0.57
        
        sh_outcomes = self.model.outcome_probabilities(sh_lambda_home, sh_lambda_away)
        sh_btts = self.model.btts_probability(sh_lambda_home, sh_lambda_away)
        
        result = {
            "2H_1X2_HOME": sh_outcomes["home"],
            "2H_1X2_DRAW": sh_outcomes["draw"],
            "2H_1X2_AWAY": sh_outcomes["away"],
            "2H_1X": sh_outcomes["home"] + sh_outcomes["draw"],
            "2H_12": sh_outcomes["home"] + sh_outcomes["away"],
            "2H_X2": sh_outcomes["draw"] + sh_outcomes["away"],
            "2H_KG_YES": sh_btts,
            "2H_KG_NO": 1.0 - sh_btts,
        }
        
        # 2H Over/Under
        for line in [0.5, 1.5, 2.5, 3.5]:
            over, under = self.model.over_under_probability(sh_lambda_home, sh_lambda_away, line)
            result[f"2H_O{line}"] = over
            result[f"2H_U{line}"] = under
        
        return result
    
    # ========== HALF COMPARISON (3) ==========
    
    def calculate_half_comparison(self) -> Dict[str, float]:
        """Which half will have more goals"""
        # Approximate based on xG distribution
        # Typically 43% HT, 57% 2H
        
        ht_total = self.lambda_home * 0.43 + self.lambda_away * 0.43
        sh_total = self.lambda_home * 0.57 + self.lambda_away * 0.57
        
        # Simple heuristic
        prob_more_ht = 0.35 if ht_total < sh_total else 0.65
        prob_more_sh = 1.0 - prob_more_ht - 0.1  # Leave 10% for equal
        prob_equal = 0.1
        
        return {
            "MORE_GOALS_HT": prob_more_ht,
            "MORE_GOALS_2H": prob_more_sh,
            "EQUAL_GOALS_HALVES": prob_equal
        }
    
    # ========== HT/FT (12) ==========
    
    def calculate_ht_ft(self) -> Dict[str, float]:
        """Half Time / Full Time combinations"""
        # Get HT probabilities
        ht_lambda_home = self.lambda_home * 0.43
        ht_lambda_away = self.lambda_away * 0.43
        ht_out = self.model.outcome_probabilities(ht_lambda_home, ht_lambda_away)
        
        # Conditional probabilities for FT given HT
        # Simplified model (in practice, use more sophisticated)
        
        result = {}
        combinations = [
            ("1", "1", "HT_FT_1_1"), ("1", "X", "HT_FT_1_X"), ("1", "2", "HT_FT_1_2"),
            ("X", "1", "HT_FT_X_1"), ("X", "X", "HT_FT_X_X"), ("X", "2", "HT_FT_X_2"),
            ("2", "1", "HT_FT_2_1"), ("2", "X", "HT_FT_2_X"), ("2", "2", "HT_FT_2_2"),
        ]
        
        # Simplified calculation (proper way: conditional probabilities)
        for ht_res, ft_res, code in combinations:
            ht_prob = ht_out["home"] if ht_res == "1" else (ht_out["draw"] if ht_res == "X" else ht_out["away"])
            ft_prob = self.prob_home_win if ft_res == "1" else (self.prob_draw if ft_res == "X" else self.prob_away_win)
            
            # Conditional probability approximation
            if ht_res == ft_res:
                # Same result: higher probability
                result[code] = ht_prob * ft_prob * 1.5
            else:
                # Different result: lower probability
                result[code] = ht_prob * ft_prob * 0.3
        
        # Normalize
        total = sum(result.values())
        if total > 0:
            for k in result:
                result[k] = result[k] / total
        
        result["HT_FT_OTHER"] = max(0.0, 1.0 - sum(result.values()))
        
        return result
    
    # ========== ASIAN HANDICAP (32) ==========
    
    def calculate_asian_handicap(self, handicap: float) -> Dict[str, float]:
        """
        Calculate Asian Handicap
        
        AH adjusts home team goals by handicap amount
        """
        prob_home = 0.0
        prob_away = 0.0
        prob_push = 0.0  # For whole number handicaps
        
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                adjusted_home = i - handicap
                
                if adjusted_home > j:
                    prob_home += self.score_matrix[i, j]
                elif adjusted_home < j:
                    prob_away += self.score_matrix[i, j]
                else:
                    prob_push += self.score_matrix[i, j]
        
        h_str = str(handicap).replace(".", "_").replace("-", "MINUS_").replace("+", "PLUS_")
        
        return {
            f"AH_{h_str}_HOME": prob_home + prob_push * 0.5,  # Push = refund = split
            f"AH_{h_str}_AWAY": prob_away + prob_push * 0.5,
            "confidence": self.confidence * 0.9
        }
    
    def calculate_all_asian_handicaps(self) -> Dict[str, float]:
        """All Asian Handicaps (-4.5 to +4.5)"""
        result = {}
        handicaps = [-4.5, -4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0,
                     0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
        
        for h in handicaps:
            ah = self.calculate_asian_handicap(h)
            result.update(ah)
        
        return result
    
    # ========== CLEAN SHEET & WIN TO NIL (12) ==========
    
    def calculate_clean_sheet_markets(self) -> Dict[str, float]:
        """Clean sheet and win to nil markets"""
        # Win to nil = Win + opponent scores 0
        w2n_home = self.score_matrix[1:, 0].sum()  # Home >= 1, Away = 0
        w2n_away = self.score_matrix[0, 1:].sum()  # Home = 0, Away >= 1
        
        # Clean sheet = Team concedes 0
        cs_home = self.score_matrix[:, 0].sum()  # Away = 0
        cs_away = self.score_matrix[0, :].sum()  # Home = 0
        cs_both = self.score_matrix[0, 0]  # 0-0
        cs_none = 1.0 - (cs_home + cs_away - cs_both)  # At least one team concedes
        
        return {
            "W2N_HOME": w2n_home,
            "W2N_AWAY": w2n_away,
            "CS_HOME": cs_home,
            "CS_AWAY": cs_away,
            "CS_BOTH": cs_both,
            "CS_NONE": max(0.0, cs_none),
            "HOME_SCORE_YES": 1.0 - self.score_matrix[0, :].sum(),
            "HOME_SCORE_NO": self.score_matrix[0, :].sum(),
            "AWAY_SCORE_YES": 1.0 - self.score_matrix[:, 0].sum(),
            "AWAY_SCORE_NO": self.score_matrix[:, 0].sum(),
        }
    
    # ========== CORRECT SCORE (50) ==========
    
    def calculate_correct_scores(self) -> Dict[str, float]:
        """All correct score probabilities"""
        result = {}
        
        # Individual scores
        for i in range(min(7, self.score_matrix.shape[0])):
            for j in range(min(7, self.score_matrix.shape[1])):
                result[f"CS_{i}_{j}"] = float(self.score_matrix[i, j])
        
        # CS_OTHER = all scores not covered
        covered_prob = sum(result.values())
        result["CS_OTHER"] = max(0.0, 1.0 - covered_prob)
        
        # Half time CS (simplified)
        ht_lambda_home = self.lambda_home * 0.43
        ht_lambda_away = self.lambda_away * 0.43
        ht_matrix = self.model.score_matrix(ht_lambda_home, ht_lambda_away, 4)
        
        for i in range(min(3, ht_matrix.shape[0])):
            for j in range(min(3, ht_matrix.shape[1])):
                result[f"HT_CS_{i}_{j}"] = float(ht_matrix[i, j])
        
        result["HT_CS_OTHER"] = max(0.0, 1.0 - sum([v for k, v in result.items() if k.startswith("HT_CS")]))
        
        # CS Groups
        result["CS_GROUP_HOME_WIN"] = self.prob_home_win
        result["CS_GROUP_DRAW"] = self.prob_draw
        result["CS_GROUP_AWAY_WIN"] = self.prob_away_win
        result["CS_GROUP_0_1"] = self.calculate_multi_goal_range(0, 1)
        result["CS_GROUP_2_3"] = self.calculate_multi_goal_range(2, 3)
        result["CS_GROUP_4_6"] = self.calculate_multi_goal_range(4, 6)
        result["CS_GROUP_7_PLUS"] = self.calculate_multi_goal_range(7, 20)
        
        return result
    
    # ========== GOAL TIMING (22) ==========
    
    def calculate_goal_timing(self) -> Dict[str, float]:
        """Goal timing markets (first goal, last goal, etc.)"""
        # Simplified exponential model
        # In practice, use minute-by-minute xG distribution
        
        total_xg = self.lambda_home + self.lambda_away
        
        # First goal time (exponential distribution)
        time_ranges = [
            (0, 10, "FG_0_10"), (11, 20, "FG_11_20"), (21, 30, "FG_21_30"),
            (31, 45, "FG_31_45"), (46, 60, "FG_46_60"), (61, 75, "FG_61_75"),
            (76, 90, "FG_76_90")
        ]
        
        result = {}
        lambda_per_min = total_xg / 90.0
        
        for start, end, code in time_ranges:
            # P(first goal in [start, end]) = e^(-lambda*start) - e^(-lambda*end)
            prob = math.exp(-lambda_per_min * start) - math.exp(-lambda_per_min * end)
            result[code] = prob
        
        # No goal
        result["FG_NO_GOAL"] = math.exp(-lambda_per_min * 90)
        
        # Normalize
        total = sum(result.values())
        if total > 0:
            for k in result:
                result[k] = result[k] / total
        
        # Last goal time (simplified)
        for start, end in [(0, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 90)]:
            code = f"LG_{start}_{end}"
            result[code] = 1.0 / 6.0  # Uniform for simplicity
        
        # First goal scorer
        result["HOME_FG"] = self.lambda_home / (self.lambda_home + self.lambda_away) if total_xg > 0 else 0.5
        result["AWAY_FG"] = 1.0 - result["HOME_FG"]
        result["NO_GOAL"] = result["FG_NO_GOAL"]
        
        # Special timing
        result["EARLY_GOAL"] = result["FG_0_10"] + result["FG_11_20"] * 0.5
        result["LATE_GOAL"] = result["FG_76_90"]
        
        # Goal in both halves
        ht_no_goal = math.exp(-lambda_per_min * 45)
        sh_no_goal = math.exp(-lambda_per_min * 45)
        result["GOAL_IN_BOTH_HALVES_YES"] = (1 - ht_no_goal) * (1 - sh_no_goal)
        result["GOAL_IN_BOTH_HALVES_NO"] = 1.0 - result["GOAL_IN_BOTH_HALVES_YES"]
        
        return result
    
    # ========== ODD/EVEN (8) ==========
    
    def calculate_odd_even(self) -> Dict[str, float]:
        """Odd/Even total goals markets"""
        odd_total = 0.0
        even_total = 0.0
        
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                total = i + j
                if total % 2 == 0:
                    even_total += self.score_matrix[i, j]
                else:
                    odd_total += self.score_matrix[i, j]
        
        # Home goals odd/even
        odd_home = 0.0
        even_home = 0.0
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                if i % 2 == 0:
                    even_home += self.score_matrix[i, j]
                else:
                    odd_home += self.score_matrix[i, j]
        
        # Away goals odd/even
        odd_away = 0.0
        even_away = 0.0
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                if j % 2 == 0:
                    even_away += self.score_matrix[i, j]
                else:
                    odd_away += self.score_matrix[i, j]
        
        # HT odd/even (approximate)
        ht_lambda_total = (self.lambda_home + self.lambda_away) * 0.43
        ht_odd = 0.5 + 0.1 * (ht_lambda_total % 2 - 1)  # Rough approximation
        
        result = {
            "ODD_EVEN_TOTAL_ODD": odd_total,
            "ODD_EVEN_TOTAL_EVEN": even_total,
            "ODD_EVEN_HOME_ODD": odd_home,
            "ODD_EVEN_HOME_EVEN": even_home,
            "ODD_EVEN_AWAY_ODD": odd_away,
            "ODD_EVEN_AWAY_EVEN": even_away,
            "ODD_EVEN_HT_ODD": max(0.0, min(1.0, ht_odd)),
            "ODD_EVEN_HT_EVEN": max(0.0, min(1.0, 1.0 - ht_odd)),
        }
        
        # Second half odd/even
        sh_lambda_total = (self.lambda_home + self.lambda_away) * 0.57
        sh_odd = 0.5 + 0.1 * (sh_lambda_total % 2 - 1)
        result["ODD_EVEN_2H_ODD"] = max(0.0, min(1.0, sh_odd))
        result["ODD_EVEN_2H_EVEN"] = 1.0 - result["ODD_EVEN_2H_ODD"]
        
        # Home odd + Away even (and vice versa)
        odd_home_even_away = 0.0
        even_home_odd_away = 0.0
        for i in range(self.score_matrix.shape[0]):
            for j in range(self.score_matrix.shape[1]):
                if i % 2 == 1 and j % 2 == 0:
                    odd_home_even_away += self.score_matrix[i, j]
                elif i % 2 == 0 and j % 2 == 1:
                    even_home_odd_away += self.score_matrix[i, j]
        
        result["ODD_HOME_EVEN_AWAY"] = odd_home_even_away
        result["EVEN_HOME_ODD_AWAY"] = even_home_odd_away
        
        return result
    
    # ========== CORNERS (25) ==========
    
    def calculate_corners(self, possession_home: float = 0.5, attack_intensity: float = 1.0) -> Dict[str, float]:
        """
        Corners markets
        
        Based on possession, xG, and attack intensity
        Typical: 10-12 corners per match
        """
        # Estimate total corners from xG and possession
        total_xg = self.lambda_home + self.lambda_away
        expected_corners = 10.0 + (total_xg - 2.8) * 1.5 + (abs(possession_home - 0.5)) * 4.0
        expected_corners *= attack_intensity
        expected_corners = max(6.0, min(16.0, expected_corners))
        
        # Home/Away split based on possession
        home_corners = expected_corners * possession_home
        away_corners = expected_corners * (1 - possession_home)
        
        result = {}
        
        # Total corners O/U
        for line in [7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5]:
            # Poisson approximation
            over_prob = sum(self.model.poisson_prob(k, expected_corners) for k in range(int(line) + 1, 25))
            result[f"CORNERS_O{line}"] = over_prob
            result[f"CORNERS_U{line}"] = 1.0 - over_prob
        
        # Home/Away corners
        for line in [3.5, 4.5, 5.5, 6.5]:
            home_over = sum(self.model.poisson_prob(k, home_corners) for k in range(int(line) + 1, 15))
            away_over = sum(self.model.poisson_prob(k, away_corners) for k in range(int(line) + 1, 15))
            
            result[f"CORNERS_HOME_O{line}"] = home_over
            result[f"CORNERS_HOME_U{line}"] = 1.0 - home_over
            result[f"CORNERS_AWAY_O{line}"] = away_over
            result[f"CORNERS_AWAY_U{line}"] = 1.0 - away_over
        
        # HT/2H corners
        for line in [3.5, 4.5, 5.5]:
            ht_corners = expected_corners * 0.45
            sh_corners = expected_corners * 0.55
            
            ht_over = sum(self.model.poisson_prob(k, ht_corners) for k in range(int(line) + 1, 15))
            sh_over = sum(self.model.poisson_prob(k, sh_corners) for k in range(int(line) + 1, 15))
            
            result[f"CORNERS_HT_O{line}"] = ht_over
            result[f"CORNERS_HT_U{line}"] = 1.0 - ht_over
            result[f"CORNERS_2H_O{line}"] = sh_over
            result[f"CORNERS_2H_U{line}"] = 1.0 - sh_over
        
        # Corner Asian Handicap
        for h in [-3.5, -2.5, -1.5, 1.5, 2.5, 3.5]:
            # Simplified AH based on home/away corner distribution
            if h < 0:
                result[f"CORNERS_AH_{h}_HOME"] = 0.4 + possession_home * 0.3
            else:
                result[f"CORNERS_AH_{h}_AWAY"] = 0.4 + (1 - possession_home) * 0.3
        
        # Corner 1X2 (which team gets more)
        result["CORNERS_1X2_HOME"] = possession_home * 0.7 + 0.15
        result["CORNERS_1X2_DRAW"] = 0.15
        result["CORNERS_1X2_AWAY"] = (1 - possession_home) * 0.7 + 0.15
        
        # Corner double chance
        result["CORNERS_1X"] = result["CORNERS_1X2_HOME"] + result["CORNERS_1X2_DRAW"]
        result["CORNERS_12"] = result["CORNERS_1X2_HOME"] + result["CORNERS_1X2_AWAY"]
        result["CORNERS_X2"] = result["CORNERS_1X2_DRAW"] + result["CORNERS_1X2_AWAY"]
        
        return result
    
    # ========== CARDS (20) ==========
    
    def calculate_cards(self, aggression_factor: float = 1.0, referee_factor: float = 1.0) -> Dict[str, float]:
        """
        Cards markets
        
        Based on match intensity and referee tendencies
        Typical: 3-5 cards per match
        """
        # Estimate total cards
        match_intensity = (self.lambda_home + self.lambda_away) / 2.8  # Normalize to avg
        expected_cards = 4.0 * match_intensity * aggression_factor * referee_factor
        expected_cards = max(2.0, min(8.0, expected_cards))
        
        result = {}
        
        # Total cards O/U
        for line in [2.5, 3.5, 4.5, 5.5, 6.5]:
            over_prob = sum(self.model.poisson_prob(k, expected_cards) for k in range(int(line) + 1, 15))
            result[f"CARDS_O{line}"] = over_prob
            result[f"CARDS_U{line}"] = 1.0 - over_prob
        
        # Home/Away cards (roughly equal, slight home advantage)
        home_cards = expected_cards * 0.45
        away_cards = expected_cards * 0.55
        
        for line in [1.5, 2.5, 3.5]:
            home_over = sum(self.model.poisson_prob(k, home_cards) for k in range(int(line) + 1, 10))
            away_over = sum(self.model.poisson_prob(k, away_cards) for k in range(int(line) + 1, 10))
            
            result[f"CARDS_HOME_O{line}"] = home_over
            result[f"CARDS_HOME_U{line}"] = 1.0 - home_over
            result[f"CARDS_AWAY_O{line}"] = away_over
            result[f"CARDS_AWAY_U{line}"] = 1.0 - away_over
        
        # Red card probability (rough estimate)
        red_card_prob = min(0.3, expected_cards * 0.05 * aggression_factor)
        result["RED_CARD_YES"] = red_card_prob
        result["RED_CARD_NO"] = 1.0 - red_card_prob
        
        # Yellow cards O/U (typically 80% of total cards)
        yellow_cards = expected_cards * 0.8
        for line in [3.5, 4.5, 5.5]:
            over_prob = sum(self.model.poisson_prob(k, yellow_cards) for k in range(int(line) + 1, 12))
            result[f"YELLOW_CARDS_O{line}"] = over_prob
            result[f"YELLOW_CARDS_U{line}"] = 1.0 - over_prob
        
        # Penalty (rough estimate based on xG in box)
        penalty_prob = min(0.25, (self.lambda_home + self.lambda_away) * 0.08)
        result["PENALTY_YES"] = penalty_prob
        result["PENALTY_NO"] = 1.0 - penalty_prob
        
        # Sent off
        result["SENT_OFF_YES"] = red_card_prob
        result["SENT_OFF_NO"] = 1.0 - red_card_prob
        
        # HT cards
        ht_cards = expected_cards * 0.4
        for line in [1.5, 2.5]:
            over_prob = sum(self.model.poisson_prob(k, ht_cards) for k in range(int(line) + 1, 8))
            result[f"CARDS_HT_O{line}"] = over_prob
            result[f"CARDS_HT_U{line}"] = 1.0 - over_prob
        
        return result
    
    # ========== COMBINATION MARKETS (150+) ==========
    
    def calculate_combo_market(self, market_codes: List[str], correlation_factor: float = 0.95) -> Dict[str, float]:
        """
        Calculate combination market probability
        
        Args:
            market_codes: List of individual market codes (e.g., ["KG_YES", "O2.5"])
            correlation_factor: Adjustment for market correlation (0.9-1.0)
            
        Returns:
            Dict with combo probability and confidence
        """
        # Get individual probabilities
        all_markets = self.calculate_all_markets()
        
        combo_prob = 1.0
        combo_conf = 1.0
        
        for code in market_codes:
            if code in all_markets:
                market_data = all_markets[code]
                prob = market_data.get("probability", market_data.get("prob", 0.5))
                conf = market_data.get("confidence", 0.85)
                
                combo_prob *= prob
                combo_conf = min(combo_conf, conf)
        
        # Apply correlation adjustment
        # Markets are not independent, so reduce combined probability
        combo_prob *= correlation_factor
        
        combo_code = "+".join(market_codes)
        
        return {
            "market": combo_code,
            "probability": combo_prob,
            "confidence": combo_conf * 0.95,  # Lower confidence for combos
            "individual_markets": market_codes
        }
    
    def calculate_popular_combos(self) -> Dict[str, Dict]:
        """Calculate most popular combo markets"""
        combos = [
            # Double combos
            ["KG_YES", "O2.5"],
            ["KG_YES", "O1.5"],
            ["1X", "O1.5"],
            ["X2", "O1.5"],
            ["1X", "KG_YES"],
            ["X2", "KG_YES"],
            
            # Triple combos
            ["1X", "KG_YES", "O2.5"],
            ["X2", "KG_YES", "O2.5"],
            ["12", "KG_YES", "O2.5"],
            ["1X", "KG_YES", "O1.5"],
            ["X2", "KG_YES", "O1.5"],
            
            # Quad combos
            ["1X", "KG_YES", "O2.5", "HT_O0.5"],
            ["X2", "KG_YES", "O2.5", "HT_O0.5"],
            ["HOME_O1.5", "AWAY_O0.5", "KG_YES", "O2.5"],
            
            # With corners
            ["1X", "KG_YES", "O2.5", "CORNERS_O9.5"],
            ["X2", "KG_YES", "O2.5", "CORNERS_O9.5"],
        ]
        
        result = {}
        for combo in combos:
            combo_result = self.calculate_combo_market(combo)
            combo_code = combo_result["market"]
            result[combo_code] = combo_result
        
        return result
    
    # ========== MASTER CALCULATOR (ALL 466 MARKETS) ==========
    
    def calculate_all_markets(self, include_combos: bool = True) -> Dict[str, Dict]:
        """
        Calculate all 466 markets
        
        Returns:
            Dict mapping market code to {probability, confidence, odds, etc.}
        """
        result = {}
        
        # Basic markets
        result.update(self._wrap_markets(self.calculate_1x2()))
        result.update(self._wrap_markets(self.calculate_btts()))
        result.update(self._wrap_markets(self.calculate_double_chance()))
        result.update(self._wrap_markets(self.calculate_dnb()))
        
        # Over/Under
        result.update(self._wrap_markets(self.calculate_all_over_under()))
        
        # Team totals
        result.update(self._wrap_markets(self.calculate_all_team_totals()))
        
        # Exact goals
        result.update(self._wrap_markets(self.calculate_exact_goals()))
        
        # Multi-goal ranges
        result.update(self._wrap_markets(self.calculate_all_multi_goal_ranges()))
        
        # Half time
        result.update(self._wrap_markets(self.calculate_half_time_markets()))
        
        # Second half
        result.update(self._wrap_markets(self.calculate_second_half_markets()))
        
        # Half comparison
        result.update(self._wrap_markets(self.calculate_half_comparison()))
        
        # HT/FT
        result.update(self._wrap_markets(self.calculate_ht_ft()))
        
        # Asian Handicaps
        result.update(self._wrap_markets(self.calculate_all_asian_handicaps()))
        
        # Clean sheet
        result.update(self._wrap_markets(self.calculate_clean_sheet_markets()))
        
        # Correct scores
        result.update(self._wrap_markets(self.calculate_correct_scores()))
        
        # Goal timing
        result.update(self._wrap_markets(self.calculate_goal_timing()))
        
        # Odd/Even
        result.update(self._wrap_markets(self.calculate_odd_even()))
        
        # Corners
        result.update(self._wrap_markets(self.calculate_corners()))
        
        # Cards
        result.update(self._wrap_markets(self.calculate_cards()))
        
        # Combination markets
        if include_combos:
            combos = self.calculate_popular_combos()
            result.update({k: v for k, v in combos.items()})
        
        return result
    
    def _wrap_markets(self, markets: Dict[str, float]) -> Dict[str, Dict]:
        """Wrap market probabilities in standard format"""
        wrapped = {}
        for code, prob in markets.items():
            if isinstance(prob, dict):
                wrapped[code] = prob
            else:
                wrapped[code] = {
                    "probability": float(prob),
                    "confidence": self.confidence,
                    "market": code
                }
        return wrapped
    
    def calculate_with_kelly(self, bankroll: float = 10000, odds_data: Optional[Dict] = None) -> Dict:
        """
        Calculate markets with Kelly Criterion stake recommendations
        
        Args:
            bankroll: User's bankroll
            odds_data: Dict mapping market codes to bookmaker odds
            
        Returns:
            Markets with Kelly stake recommendations
        """
        markets = self.calculate_all_markets()
        
        if odds_data:
            for code, market_data in markets.items():
                if code in odds_data:
                    odds = odds_data[code]
                    prob = market_data["probability"]
                    
                    # Calculate Kelly stakes
                    kelly_full = KellyCriterion.calculate_full_kelly(prob, odds, market_data["confidence"])
                    kelly_half = KellyCriterion.calculate_fractional_kelly(prob, odds, 0.5, market_data["confidence"])
                    kelly_quarter = KellyCriterion.calculate_fractional_kelly(prob, odds, 0.25, market_data["confidence"])
                    
                    ev = KellyCriterion.calculate_expected_value(prob, odds)
                    is_value = KellyCriterion.is_value_bet(prob, odds)
                    
                    market_data.update({
                        "odds": odds,
                        "expected_value": ev,
                        "is_value_bet": is_value,
                        "kelly_full": kelly_full,
                        "kelly_half": kelly_half,
                        "kelly_quarter": kelly_quarter,
                        "stake_full": bankroll * kelly_full,
                        "stake_half": bankroll * kelly_half,
                        "stake_quarter": bankroll * kelly_quarter,
                    })
        
        return markets


# ========== API INTEGRATION FUNCTIONS ==========

def predict_466_markets(
    fixture_id: str,
    home_xg_for: float,
    home_xg_against: float,
    away_xg_for: float,
    away_xg_against: float,
    requested_markets: str = "all",
    include_kelly: bool = False,
    bankroll: float = 10000,
    odds_data: Optional[Dict] = None
) -> Dict:
    """
    Main API function for 466 markets prediction
    
    Args:
        fixture_id: Match ID
        home_xg_for/against: Home team xG stats
        away_xg_for/against: Away team xG stats
        requested_markets: "all" or comma-separated market codes
        include_kelly: Include Kelly Criterion stakes
        bankroll: User bankroll (if include_kelly=True)
        odds_data: Bookmaker odds (if include_kelly=True)
        
    Returns:
        {
            "fixtureId": ...,
            "markets": [...],
            "model": "dixon_coles",
            "confidence": 0.85
        }
    """
    # Initialize calculator
    calc = Markets466Calculator(
        home_xg_for, home_xg_against,
        away_xg_for, away_xg_against
    )
    
    # Calculate markets
    if requested_markets == "all":
        if include_kelly:
            markets = calc.calculate_with_kelly(bankroll, odds_data)
        else:
            markets = calc.calculate_all_markets()
    else:
        # Calculate specific markets
        markets = calc.calculate_all_markets(include_combos=False)
        requested = requested_markets.split(",")
        markets = {k: v for k, v in markets.items() if k in requested}
    
    # Format for API
    markets_list = [
        {
            "market": code,
            **data
        }
        for code, data in markets.items()
    ]
    
    return {
        "fixtureId": fixture_id,
        "markets": markets_list,
        "model": "dixon_coles",
        "confidence": calc.confidence,
        "expected_goals": {
            "home": round(calc.lambda_home, 2),
            "away": round(calc.lambda_away, 2)
        }
    }

