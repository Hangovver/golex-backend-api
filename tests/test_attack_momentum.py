"""
Tests for Attack Momentum Service
"""
import pytest
from app.services.attack_momentum import calculate_attack_momentum


def test_calculate_attack_momentum_empty():
    """Test with empty events"""
    events = []
    result = calculate_attack_momentum(events)
    
    assert result == []


def test_calculate_attack_momentum_single_goal():
    """Test with single goal event"""
    events = [
        {
            "time": 10,
            "type": "GOAL",
            "team_id": 1,
            "home_team_id": 1,
            "away_team_id": 2
        }
    ]
    
    result = calculate_attack_momentum(events)
    
    assert len(result) > 0
    assert any(point["minute"] == 10 for point in result)


def test_calculate_attack_momentum_multiple_events():
    """Test with multiple events"""
    events = [
        {"time": 5, "type": "SHOT_ON_TARGET", "team_id": 1, "home_team_id": 1, "away_team_id": 2},
        {"time": 10, "type": "GOAL", "team_id": 1, "home_team_id": 1, "away_team_id": 2},
        {"time": 15, "type": "CORNER", "team_id": 2, "home_team_id": 1, "away_team_id": 2},
        {"time": 20, "type": "ATTACK", "team_id": 2, "home_team_id": 1, "away_team_id": 2},
    ]
    
    result = calculate_attack_momentum(events)
    
    assert len(result) > 0
    # Check that momentum values are between -1 and 1
    for point in result:
        assert -1.0 <= point["value"] <= 1.0


def test_momentum_values_range():
    """Test that momentum values stay within valid range"""
    events = [
        {"time": i, "type": "GOAL", "team_id": 1, "home_team_id": 1, "away_team_id": 2}
        for i in range(1, 91, 10)
    ]
    
    result = calculate_attack_momentum(events)
    
    for point in result:
        assert -1.0 <= point["value"] <= 1.0


def test_momentum_time_decay():
    """Test that recent events have more impact"""
    events = [
        {"time": 10, "type": "GOAL", "team_id": 1, "home_team_id": 1, "away_team_id": 2},
        {"time": 80, "type": "GOAL", "team_id": 2, "home_team_id": 1, "away_team_id": 2},
    ]
    
    result = calculate_attack_momentum(events)
    
    # At minute 85, the recent goal should have more impact
    minute_85 = next((p for p in result if abs(p["minute"] - 85) < 0.1), None)
    if minute_85:
        # Away team (id=2) scored at 80', so momentum should favor them
        assert minute_85["value"] < 0  # Negative = away team momentum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

