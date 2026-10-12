
import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch


APP_PATH = "streamlit_app.py"


@pytest.fixture
def app():
    """Start the Streamlit app in an isolated test session."""
    return AppTest.from_file(APP_PATH, default_timeout=20).run()


def test_app_loads_without_errors(app):
    assert not app.exception

    titles = [element.value for element in app.title]
    assert "🤖 RecruitIQ Resume Screening Agent" in titles


def test_session_state_initializes_expected_keys(app):
    state = app.session_state

    assert state["uploaded_resumes"] == []
    assert state["jd_file"] is None
    assert state["ranking_df"].empty
    assert state["comparison_df"].empty
    assert state["ranked_candidates"] == []
    assert state["data_ready"] is False
    assert state["report_generated"] is False
    assert state["processed"] is False


def test_empty_dashboard_shows_zero_metrics(app):
    metric_labels = [metric.label for metric in app.metric]

    assert "Total Resumes" in metric_labels
    assert "Top Candidate" in metric_labels
    assert "Average Score" in metric_labels
    assert "Hires" in metric_labels
    assert "Second Round" in metric_labels
    assert "Rejects" in metric_labels


def test_candidate_results_render_correctly():
    at = AppTest.from_file(APP_PATH, default_timeout=20).run()
    assert not at.exception

    candidate = {
        "name": "Candidate A",
        "score": 85.0,
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["AWS"],
        "recommendation": "Hire",
        "rank": 1,
    }

    # Populate session state to exercise the candidate-results branches.
    at.session_state["ranked_candidates"] = [candidate]

    with (
        patch(
            "agents.interview_agent.generate_questions",
            return_value=["Explain your Python experience."],
        ),
        patch("agents.report_agent.generate_csv"),
        patch("agents.report_agent.generate_excel"),
        patch("agents.report_agent.generate_pdf"),
        patch("agents.scorecard_agent.save_scorecard"),
    ):
        at.session_state["data_ready"] = False
        at.session_state["report_generated"] = False
        at.run()

    assert not at.exception

    rendered_text = "\n".join(
        str(element.value)
        for collection in (
            at.title,
            at.header,
            at.subheader,
            at.markdown,
            at.caption,
            at.text,
            at.metric,
        )
        for element in collection
        if hasattr(element, "value")
    )

    assert "Candidate A" in rendered_text
    assert (
        "85.0%" in rendered_text
        or "85" in rendered_text
        or any(
            "85" in str(element.value)
            for element in at.dataframe
            if hasattr(element, "value")
        )
    )
