def get_recommendation(score):
    """
    Evaluates the candidate's score and returns the exact string 
    required by the Streamlit metrics.
    """
    if score >= 70:
        return "Hire"
    elif score >= 50:
        return "Second Round"
    else:
        return "Reject"