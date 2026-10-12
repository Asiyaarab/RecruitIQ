
import json
import pytest

from agents.scorecard_agent import (
    create_scorecard,
    save_scorecard,
)


@pytest.fixture
def scorecard_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path / "scorecards"


@pytest.fixture
def candidate():
    return {
        "name": "Amina.pdf",
        "score": 85,
        "matched_skills": ["Python", "NLP"],
        "missing_skills": ["Docker"],
        "recommendation": "Hire",
    }


def test_create_scorecard(candidate):
    result = create_scorecard(candidate)

    assert result == candidate


def test_create_scorecard_does_not_modify_candidate(candidate):
    original = candidate.copy()

    create_scorecard(candidate)

    assert candidate == original


def test_save_scorecard_creates_json(scorecard_dir, candidate):
    save_scorecard(candidate)

    output = scorecard_dir / "Amina.json"
    assert output.exists()

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved == create_scorecard(candidate)


def test_save_scorecard_overwrites_existing_file(
    scorecard_dir, candidate
):
    save_scorecard(candidate)
    candidate["score"] = 92

    save_scorecard(candidate)

    output = scorecard_dir / "Amina.json"
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert saved["score"] == 92


@pytest.mark.parametrize(
    "missing_key",
    [
        "name",
        "score",
        "matched_skills",
        "missing_skills",
        "recommendation",
    ],
)
def test_create_scorecard_missing_required_field(
    candidate, missing_key
):
    candidate.pop(missing_key)

    with pytest.raises(KeyError):
        create_scorecard(candidate)
