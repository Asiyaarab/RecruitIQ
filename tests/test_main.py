
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

import main


@pytest.fixture
def mock_dependencies():
    with (
        patch("main.extract_text") as mock_extract,
        patch("main.extract_skills") as mock_skills,
        patch("main.calculate_final_score") as mock_score,
        patch("main.get_recommendation") as mock_recommendation,
    ):
        mock_recommendation.side_effect = (
            lambda score: "Hire" if score >= 70
            else "Second Round" if score >= 50
            else "Reject"
        )

        yield {
            "extract_text": mock_extract,
            "extract_skills": mock_skills,
            "calculate_final_score": mock_score,
            "get_recommendation": mock_recommendation,
        }


def make_file(name):
    file = BytesIO(b"resume content")
    file.name = name
    return file


def test_process_resumes_ranks_candidates_by_score(mock_dependencies):
    deps = mock_dependencies

    deps["extract_text"].side_effect = [
        "job description",
        "resume one",
        "resume two",
    ]
    deps["extract_skills"].side_effect = [
        ["Python", "SQL"],
        ["Python"],
        ["Python", "SQL"],
    ]
    deps["calculate_final_score"].side_effect = [60, 90]

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("candidate1.pdf"), make_file("candidate2.pdf")],
        make_file("job.pdf"),
    )

    assert len(candidates) == 2
    assert candidates[0]["name"] == "candidate2.pdf"
    assert candidates[0]["score"] == 90.0
    assert candidates[0]["rank"] == 1
    assert candidates[1]["rank"] == 2
    assert list(ranking_df["score"]) == [90.0, 60.0]
    assert len(comparison_df) == 2


def test_process_resumes_matches_and_missing_skills(mock_dependencies):
    deps = mock_dependencies

    deps["extract_text"].side_effect = [
        "job description",
        "resume",
    ]
    deps["extract_skills"].side_effect = [
        ["Python", "SQL", "AWS"],
        ["Python", "SQL"],
    ]
    deps["calculate_final_score"].return_value = 75

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("candidate.pdf")],
        make_file("job.pdf"),
    )

    candidate = candidates[0]

    assert set(candidate["matched_skills"]) == {"Python", "SQL"}
    assert candidate["missing_skills"] == ["AWS"]
    assert comparison_df.iloc[0]["matched_skills"] == 2
    assert comparison_df.iloc[0]["missing_skills"] == 1


def test_process_resumes_no_required_skills_returns_zero(
    mock_dependencies,
):
    deps = mock_dependencies

    deps["extract_text"].side_effect = ["job description", "resume"]
    deps["extract_skills"].side_effect = [[], ["Python"]]

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("candidate.pdf")],
        make_file("job.pdf"),
    )

    assert candidates[0]["score"] == 0.0
    assert deps["calculate_final_score"].call_count == 0


def test_process_resumes_invalid_score_becomes_zero(mock_dependencies):
    deps = mock_dependencies

    deps["extract_text"].side_effect = ["job description", "resume"]
    deps["extract_skills"].side_effect = [["Python"], ["Python"]]
    deps["calculate_final_score"].return_value = "invalid"

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("candidate.pdf")],
        make_file("job.pdf"),
    )

    assert candidates[0]["score"] == 0.0


def test_process_resumes_empty_uploads(mock_dependencies):
    deps = mock_dependencies

    deps["extract_text"].return_value = "job description"
    deps["extract_skills"].return_value = ["Python"]

    ranking_df, comparison_df, candidates = main.process_resumes(
        [],
        make_file("job.pdf"),
    )

    assert ranking_df.empty
    assert comparison_df.empty
    assert candidates == []


def test_process_resumes_preserves_input_candidate_order_for_ties(
    mock_dependencies,
):
    deps = mock_dependencies

    deps["extract_text"].side_effect = [
        "job description",
        "resume one",
        "resume two",
    ]
    deps["extract_skills"].side_effect = [
        ["Python"],
        ["Python"],
        ["Python"],
    ]
    deps["calculate_final_score"].return_value = 80

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("first.pdf"), make_file("second.pdf")],
        make_file("job.pdf"),
    )

    assert [c["name"] for c in candidates] == [
        "first.pdf",
        "second.pdf",
    ]
    assert [c["rank"] for c in candidates] == [1, 2]


def test_process_resumes_rewinds_resume_before_extraction(
    mock_dependencies,
):
    deps = mock_dependencies

    deps["extract_text"].side_effect = ["job description", "resume"]
    deps["extract_skills"].side_effect = [["Python"], ["Python"]]
    deps["calculate_final_score"].return_value = 80

    resume = make_file("candidate.pdf")
    resume.read(5)

    # Confirm the file cursor starts away from zero.
    assert resume.tell() == 5

    main.process_resumes([resume], make_file("job.pdf"))

    # Verify the resume was rewound before extract_text was called.
    assert deps["extract_text"].call_args_list[1].args[0] is resume
    assert deps["extract_text"].call_args_list[1].args[0].tell() == 0


def test_process_resumes_creates_expected_dataframe_columns(
    mock_dependencies,
):
    deps = mock_dependencies

    deps["extract_text"].side_effect = ["job description", "resume"]
    deps["extract_skills"].side_effect = [["Python"], ["Python"]]
    deps["calculate_final_score"].return_value = 85

    ranking_df, comparison_df, candidates = main.process_resumes(
        [make_file("candidate.pdf")],
        make_file("job.pdf"),
    )

    assert set(ranking_df.columns) == {
        "name",
        "score",
        "matched_skills",
        "missing_skills",
        "recommendation",
        "rank",
    }
    assert list(comparison_df.columns) == [
        "name",
        "score",
        "matched_skills",
        "missing_skills",
    ]

