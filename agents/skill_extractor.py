from data.skills_database import SKILLS_DATABASE


def extract_skills(text):

    if not text:
        return []

    text_lower = text.lower()

    found = []

    for skill in SKILLS_DATABASE:
        if skill.lower() in text_lower:
            found.append(skill)

    return list(set(found))
