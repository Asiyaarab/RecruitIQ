import json
import os


def create_scorecard(candidate):

    scorecard = {

        "name": candidate["name"],

        "score": candidate["score"],

        "matched_skills": candidate["matched_skills"],

        "missing_skills": candidate["missing_skills"],

        "recommendation": candidate["recommendation"]
    }

    return scorecard


def save_scorecard(candidate):

    os.makedirs(
        "scorecards",
        exist_ok=True
    )

    filename = candidate["name"].split(".")[0]

    filepath = f"scorecards/{filename}.json"

    with open(
            filepath,
            "w"
    ) as file:

        json.dump(
            create_scorecard(candidate),
            file,
            indent=4
        )