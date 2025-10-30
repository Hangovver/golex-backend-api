"""
Tests for Player Rating Service
"""
import pytest
from app.services.player_rating import calculate_player_rating, get_rating_color


def test_calculate_player_rating_base():
    """Test base rating calculation"""
    stats = {
        "goals": 0,
        "assists": 0,
        "shots_on_target": 0,
        "passes_accurate": 50,
        "passes_total": 60,
        "tackles": 0,
        "interceptions": 0
    }
    
    rating = calculate_player_rating(stats, "CM")
    
    # Base rating should be around 6.0
    assert 5.5 <= rating <= 7.0


def test_calculate_player_rating_with_goal():
    """Test rating with goal"""
    stats = {
        "goals": 1,
        "assists": 0,
        "shots_on_target": 3,
        "passes_accurate": 50,
        "passes_total": 60,
        "tackles": 2,
        "interceptions": 1
    }
    
    rating = calculate_player_rating(stats, "ST")
    
    # Rating should be higher with a goal
    assert rating >= 7.0


def test_calculate_player_rating_with_assists():
    """Test rating with assists"""
    stats = {
        "goals": 0,
        "assists": 2,
        "shots_on_target": 2,
        "passes_accurate": 70,
        "passes_total": 80,
        "key_passes": 5,
        "tackles": 1,
        "interceptions": 1
    }
    
    rating = calculate_player_rating(stats, "CAM")
    
    # Rating should be good with assists
    assert rating >= 7.5


def test_calculate_player_rating_poor_performance():
    """Test rating with poor performance"""
    stats = {
        "goals": 0,
        "assists": 0,
        "shots_on_target": 0,
        "passes_accurate": 20,
        "passes_total": 50,
        "tackles": 0,
        "interceptions": 0,
        "yellow_cards": 1,
        "fouls": 3
    }
    
    rating = calculate_player_rating(stats, "CM")
    
    # Rating should be below average
    assert rating < 6.5


def test_rating_bounds():
    """Test that rating stays within 0-10 range"""
    # Extreme positive stats
    stats_excellent = {
        "goals": 3,
        "assists": 2,
        "shots_on_target": 8,
        "passes_accurate": 90,
        "passes_total": 100,
        "key_passes": 10,
        "tackles": 5,
        "interceptions": 5
    }
    
    rating = calculate_player_rating(stats_excellent, "ST")
    assert 0.0 <= rating <= 10.0
    
    # Extreme negative stats
    stats_poor = {
        "goals": 0,
        "assists": 0,
        "shots_on_target": 0,
        "passes_accurate": 10,
        "passes_total": 50,
        "tackles": 0,
        "interceptions": 0,
        "yellow_cards": 2,
        "red_cards": 1,
        "fouls": 5
    }
    
    rating = calculate_player_rating(stats_poor, "CM")
    assert 0.0 <= rating <= 10.0


def test_get_rating_color():
    """Test rating color coding"""
    assert get_rating_color(9.5) == "#4CAF50"  # Green
    assert get_rating_color(8.5) == "#8BC34A"  # Light Green
    assert get_rating_color(7.5) == "#FFC107"  # Yellow
    assert get_rating_color(6.5) == "#FF9800"  # Orange
    assert get_rating_color(5.5) == "#F44336"  # Red


def test_position_multipliers():
    """Test that different positions get different ratings for same stats"""
    stats = {
        "goals": 1,
        "assists": 0,
        "shots_on_target": 3,
        "passes_accurate": 50,
        "passes_total": 60,
        "tackles": 2,
        "interceptions": 1
    }
    
    rating_striker = calculate_player_rating(stats, "ST")
    rating_defender = calculate_player_rating(stats, "CB")
    
    # Striker should get higher rating for goal than defender
    assert rating_striker > rating_defender


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

