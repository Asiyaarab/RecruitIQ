import os
import json
import requests
from dotenv import load_dotenv

from data.question_bank import QUESTION_BANK

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def _fallback_questions(skills):
    """Template/question-bank based generation, used when no AI provider is available."""
    if not skills:
        return [
            "Tell me about yourself.",
            "What projects have you worked on?",
            "What is your strongest technical skill?"
        ]

    questions = []
    for skill in skills:
        skill_clean = skill.strip()
        bank_key = next((k for k in QUESTION_BANK if k.lower() == skill_clean.lower()), None)

        if bank_key:
            questions.extend(QUESTION_BANK[bank_key])
        else:
            questions.append(f"Explain your experience with {skill_clean}.")
            questions.append(f"How have you used {skill_clean} in a real project?")
            questions.append(f"What challenges did you face while working with {skill_clean}?")

    return questions[:10]


def _build_prompt(skills):
    return (
        "You are an experienced technical interviewer. Based on the following candidate skills, "
        f"generate exactly 8 concise, specific interview questions to assess the candidate's depth "
        f"in these areas: {', '.join(skills)}. "
        "Return ONLY a JSON array of question strings, with no extra commentary or markdown."
    )


def _parse_question_list(content):
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").replace("json", "", 1).strip()

    questions = json.loads(content)
    if isinstance(questions, list) and len(questions) > 0:
        return [str(q) for q in questions[:10]]
    return None


def _call_groq(prompt):
    if not GROQ_API_KEY:
        return None

    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert technical interviewer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        },
        timeout=20
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    return _parse_question_list(content)


def _call_gemini(prompt):
    if not GEMINI_API_KEY:
        return None

    response = requests.post(
        GEMINI_API_URL,
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}]
        },
        timeout=20
    )
    response.raise_for_status()

    content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_question_list(content)


def generate_questions(skills):
    if not skills:
        return _fallback_questions(skills)

    prompt = _build_prompt(skills)

    for provider_name, call in (("Groq", _call_groq), ("Gemini", _call_gemini)):
        try:
            questions = call(prompt)
            if questions:
                return questions
        except Exception as e:
            print(f"DEBUG {provider_name} API error:", e)

    return _fallback_questions(skills)
