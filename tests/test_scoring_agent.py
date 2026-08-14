from agents.scoring_agent import calculate_final_score


def test_no_required_skills_returns_zero():
    assert calculate_final_score(["python"], []) == 0


def test_full_match_returns_100():
    assert calculate_final_score(["python", "sql"], ["python", "sql"]) == 100


def test_partial_match_returns_percentage():
    assert calculate_final_score(["python"], ["python", "sql"]) == 50.0


def test_no_overlap_returns_zero():
    assert calculate_final_score(["java"], ["python", "sql"]) == 0.0


def test_extra_candidate_skills_do_not_inflate_score():
    assert calculate_final_score(
        ["python", "sql", "docker", "aws"], ["python", "sql"]
    ) == 100
