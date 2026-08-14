def calculate_final_score(candidate_skills, required_skills):

    if not required_skills:
        return 0

    matched = len(set(candidate_skills) & set(required_skills))
    total = len(set(required_skills))

    return round((matched / total) * 100, 2)