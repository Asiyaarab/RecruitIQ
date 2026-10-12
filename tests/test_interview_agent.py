
import json
from unittest.mock import Mock, patch

import pytest

from agents import interview_agent as agent


def test_fallback_questions_without_skills():
    questions = agent._fallback_questions([])

    assert len(questions) == 3
    assert "Tell me about yourself." in questions


def test_fallback_questions_uses_question_bank():
    skill = next(iter(agent.QUESTION_BANK))
    questions = agent._fallback_questions([skill])

    assert questions == agent.QUESTION_BANK[skill]


def test_fallback_questions_unknown_skill():
    questions = agent._fallback_questions(["CustomSkillXYZ"])

    assert len(questions) == 3
    assert all("CustomSkillXYZ" in q for q in questions)


def test_fallback_questions_strips_skill_whitespace():
    questions = agent._fallback_questions(["  CustomSkillXYZ  "])

    assert all("CustomSkillXYZ" in q for q in questions)


def test_fallback_questions_limits_to_ten():
    questions = agent._fallback_questions(
        [f"CustomSkill{i}" for i in range(5)]
    )

    assert len(questions) == 10


def test_build_prompt_includes_skills():
    prompt = agent._build_prompt(["Python", "Machine Learning"])

    assert "Python" in prompt
    assert "Machine Learning" in prompt
    assert "exactly 8" in prompt
    assert "JSON array" in prompt


def test_parse_question_list_valid_json():
    result = agent._parse_question_list(
        '["Question one?", "Question two?"]'
    )

    assert result == ["Question one?", "Question two?"]


def test_parse_question_list_json_code_fence():
    result = agent._parse_question_list(
        '```json\n["Question one?", "Question two?"]\n```'
    )

    assert result == ["Question one?", "Question two?"]


def test_parse_question_list_limits_to_ten():
    content = json.dumps([f"Question {i}?" for i in range(12)])

    result = agent._parse_question_list(content)

    assert len(result) == 10


@pytest.mark.parametrize("content", ["[]", "{}", '""', "null"])
def test_parse_question_list_rejects_non_question_lists(content):
    assert agent._parse_question_list(content) is None


def test_parse_question_list_converts_items_to_strings():
    result = agent._parse_question_list('[1, true, null]')

    assert result == ["1", "True", "None"]


def test_parse_question_list_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        agent._parse_question_list("not valid JSON")


@patch("agents.interview_agent.GROQ_API_KEY", None)
def test_call_groq_without_api_key():
    assert agent._call_groq("prompt") is None


@patch("agents.interview_agent.GEMINI_API_KEY", None)
def test_call_gemini_without_api_key():
    assert agent._call_gemini("prompt") is None


@patch("agents.interview_agent.GROQ_API_KEY", "test-key")
@patch("agents.interview_agent.requests.post")
def test_call_groq_success(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '["Python question?", "ML question?"]'
            }
        }]
    }
    mock_post.return_value = mock_response

    result = agent._call_groq("test prompt")

    assert result == ["Python question?", "ML question?"]
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch("agents.interview_agent.GEMINI_API_KEY", "test-key")
@patch("agents.interview_agent.requests.post")
def test_call_gemini_success(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '["Python question?"]'
                }]
            }
        }]
    }
    mock_post.return_value = mock_response

    result = agent._call_gemini("test prompt")

    assert result == ["Python question?"]
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


def test_generate_questions_empty_skills():
    with patch.object(agent, "_fallback_questions") as fallback:
        fallback.return_value = ["Tell me about yourself."]

        result = agent.generate_questions([])

        assert result == ["Tell me about yourself."]
        fallback.assert_called_once_with([])


def test_generate_questions_groq_success():
    with patch.object(
        agent, "_call_groq", return_value=["Groq question?"]
    ) as groq, patch.object(agent, "_call_gemini") as gemini:
        result = agent.generate_questions(["Python"])

    assert result == ["Groq question?"]
    groq.assert_called_once()
    gemini.assert_not_called()


def test_generate_questions_gemini_fallback_provider():
    with patch.object(
        agent, "_call_groq", return_value=None
    ), patch.object(
        agent, "_call_gemini", return_value=["Gemini question?"]
    ) as gemini:
        result = agent.generate_questions(["Python"])

    assert result == ["Gemini question?"]
    gemini.assert_called_once()


def test_generate_questions_falls_back_when_providers_return_none():
    with patch.object(
        agent, "_call_groq", return_value=None
    ), patch.object(
        agent, "_call_gemini", return_value=None
    ), patch.object(
        agent, "_fallback_questions",
        return_value=["Fallback question?"]
    ) as fallback:
        result = agent.generate_questions(["Python"])

    assert result == ["Fallback question?"]
    fallback.assert_called_once_with(["Python"])


def test_generate_questions_falls_back_when_providers_raise():
    with patch.object(
        agent, "_call_groq", side_effect=RuntimeError("Groq unavailable")
    ), patch.object(
        agent, "_call_gemini", side_effect=RuntimeError("Gemini unavailable")
    ), patch.object(
        agent, "_fallback_questions",
        return_value=["Fallback question?"]
    ):
        result = agent.generate_questions(["Python"])

    assert result == ["Fallback question?"]
