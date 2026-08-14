import pandas as pd
import os

os.makedirs("reports", exist_ok=True)

from agents.scoring_agent import calculate_final_score
from agents.skill_extractor import extract_skills
from agents.parser_agent import extract_text
from agents.recommendation_agent import get_recommendation

# ==============================
# MAIN FUNCTION (FIXED VERSION)
# ==============================

def process_resumes(uploaded_resumes, jd_file):

    # =========================
    # JD EXTRACTION
    # =========================
    jd_text = extract_text(jd_file)
    required_skills = extract_skills(jd_text)

    ranked_candidates = []

    # =========================
    # LOOP RESUMES
    # =========================
    for idx, file in enumerate(uploaded_resumes):
        file.seek(0)
        resume_text = extract_text(file)
        candidate_skills = extract_skills(resume_text)

        # =========================
        # SCORE CALCULATION (SAFE)
        # =========================
        if not required_skills:
            score = 0.0
        else:
            score = calculate_final_score(candidate_skills, required_skills)

        # Force numeric safety
        try:
            score = float(score)
        except Exception:
            score = 0.0

        # =========================
        # MATCH / MISSING SKILLS
        # =========================
        matched = list(set(candidate_skills).intersection(set(required_skills)))
        missing = list(set(required_skills).difference(set(candidate_skills)))

        # =========================
        # RECOMMENDATION (FIXED LOGIC)
        # =========================
        recommendation = get_recommendation(score)

        ranked_candidates.append({
            "name": file.name,
            "score": score,
            "matched_skills": matched,
            "missing_skills": missing,
            "recommendation": recommendation
        })

    # =========================
    # SORT BY SCORE
    # =========================
    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    # =========================
    # ADD RANK
    # =========================
    for i, c in enumerate(ranked_candidates):
        c["rank"] = i + 1

    # =========================
    # DATAFRAME (FIXED SAFE KEYS)
    # =========================
    ranking_df = pd.DataFrame(ranked_candidates)

    # Ensure score column exists properly
    if not ranking_df.empty and "score" not in ranking_df.columns:
        ranking_df["score"] = 0.0

    comparison_df = pd.DataFrame([
        {
            "name": c["name"],
            "score": c.get("score", 0.0),
            "matched_skills": len(c.get("matched_skills", [])),
            "missing_skills": len(c.get("missing_skills", []))
        }
        for c in ranked_candidates
    ])

    return ranking_df, comparison_df, ranked_candidates