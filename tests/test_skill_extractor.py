from agents.skill_extractor import extract_skills


def test_empty_text_returns_empty_list():
    assert extract_skills("") == []
    assert extract_skills(None) == []


def test_finds_known_skills_case_insensitively():
    text = "Experienced with PYTHON, sql, and Docker deployments."
    found = extract_skills(text)
    assert "Python" in found
    assert "SQL" in found
    assert "Docker" in found


def test_ignores_unknown_words():
    found = extract_skills("Loves hiking and painting on weekends.")
    assert found == []


def test_no_duplicate_skills_returned():
    text = "python python PYTHON Python"
    found = extract_skills(text)
    assert found.count("Python") == 1
