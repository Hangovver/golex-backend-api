"""
Tests for xG Calculator Service
"""
import pytest
from app.services.xg_calculator import calculate_xg


def test_calculate_xg_empty():
    """Test with no shots"""
    shots = []
    result = calculate_xg(shots)
    
    assert result == 0.0


def test_calculate_xg_single_shot():
    """Test with single shot"""
    shots = [
        {
            "distance": 10,
            "angle": 30,
            "shot_type": "on_target",
            "situation": "open_play"
        }
    ]
    
    result = calculate_xg(shots)
    
    assert result > 0.0
    assert result <= 1.0


def test_calculate_xg_close_shot():
    """Test that close shots have higher xG"""
    close_shot = [{
        "distance": 5,
        "angle": 45,
        "shot_type": "on_target",
        "situation": "open_play"
    }]
    
    far_shot = [{
        "distance": 30,
        "angle": 10,
        "shot_type": "on_target",
        "situation": "open_play"
    }]
    
    xg_close = calculate_xg(close_shot)
    xg_far = calculate_xg(far_shot)
    
    assert xg_close > xg_far


def test_calculate_xg_penalty():
    """Test that penalties have high xG"""
    penalty = [{
        "distance": 11,
        "angle": 45,
        "shot_type": "on_target",
        "situation": "penalty"
    }]
    
    xg = calculate_xg(penalty)
    
    # Penalties should have ~0.75-0.80 xG
    assert xg >= 0.70


def test_calculate_xg_header():
    """Test header xG"""
    header = [{
        "distance": 8,
        "angle": 40,
        "shot_type": "on_target",
        "situation": "open_play",
        "body_part": "head"
    }]
    
    foot = [{
        "distance": 8,
        "angle": 40,
        "shot_type": "on_target",
        "situation": "open_play",
        "body_part": "right_foot"
    }]
    
    xg_header = calculate_xg(header)
    xg_foot = calculate_xg(foot)
    
    # Foot shots typically have higher xG than headers
    assert xg_foot >= xg_header


def test_calculate_xg_multiple_shots():
    """Test xG calculation with multiple shots"""
    shots = [
        {"distance": 10, "angle": 30, "shot_type": "on_target", "situation": "open_play"},
        {"distance": 15, "angle": 25, "shot_type": "on_target", "situation": "open_play"},
        {"distance": 20, "angle": 20, "shot_type": "off_target", "situation": "open_play"},
        {"distance": 5, "angle": 40, "shot_type": "on_target", "situation": "open_play"},
    ]
    
    total_xg = calculate_xg(shots)
    
    # Total xG should be sum of individual xGs
    individual_xgs = [calculate_xg([shot]) for shot in shots]
    expected_total = sum(individual_xgs)
    
    assert abs(total_xg - expected_total) < 0.01


def test_xg_bounds():
    """Test that xG values are within valid range"""
    # Extreme case: very close, perfect angle
    best_shot = [{
        "distance": 1,
        "angle": 90,
        "shot_type": "on_target",
        "situation": "open_play"
    }]
    
    xg = calculate_xg(best_shot)
    
    # Even the best shot shouldn't have xG > 1.0
    assert 0.0 <= xg <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

