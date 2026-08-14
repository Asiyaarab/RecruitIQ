from agents.recommendation_agent import get_recommendation


def test_hire_at_exactly_70():
    assert get_recommendation(70) == "Hire"


def test_hire_above_70():
    assert get_recommendation(85) == "Hire"


def test_second_round_at_exactly_50():
    assert get_recommendation(50) == "Second Round"


def test_second_round_between_50_and_70():
    assert get_recommendation(65) == "Second Round"


def test_reject_just_below_50():
    assert get_recommendation(49.9) == "Reject"


def test_reject_at_zero():
    assert get_recommendation(0) == "Reject"
