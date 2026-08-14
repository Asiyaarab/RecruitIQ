import os
import json
import streamlit as st
import pandas as pd

# ==================================
# PAGE CONFIG (Must be first)
# ==================================
st.set_page_config(
    page_title="RecruitIQ Resume Screening Agent",
    page_icon="🤖",
    layout="wide"
)

# ==================================
# INITIALIZE SESSION STATE
# ==================================
if "uploaded_resumes" not in st.session_state:
    st.session_state.uploaded_resumes = []
if "jd_file" not in st.session_state:
    st.session_state.jd_file = None
if "ranking_df" not in st.session_state:
    st.session_state.ranking_df = pd.DataFrame()
if "comparison_df" not in st.session_state:
    st.session_state.comparison_df = pd.DataFrame()
if "ranked_candidates" not in st.session_state:
    st.session_state.ranked_candidates = []
if "data_ready" not in st.session_state:
    st.session_state.data_ready = False
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "processed" not in st.session_state:
    st.session_state.processed = False

os.makedirs("reports", exist_ok=True)

from main import process_resumes
from agents.interview_agent import generate_questions
from agents.report_agent import (
    generate_csv,
    generate_excel,
    generate_pdf
)
from agents.scorecard_agent import save_scorecard

# ==================================
# LIGHT THEME CSS
# ==================================
st.markdown(
"""
<style>
.stApp { background: #EEF2F7; }
h1, h2, h3, h4, h5, h6, p, label { color: #1E293B !important; }

div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #8B5CF6, #06B6D4);
    padding: 20px;
    border-radius: 20px;
    color: white;
}
div[data-testid="metric-container"] label,
div[data-testid="metric-container"] div { color: white !important; }

.card {
    background: #FFFFFF;
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(15, 23, 42, 0.1);
    box-shadow: 0px 8px 25px rgba(15, 23, 42, 0.08);
}

div[data-testid="stDataFrame"] { background: #FFFFFF; border-radius: 20px; }

.stProgress > div > div > div > div { background: linear-gradient(90deg, #8B5CF6, #06B6D4); }

.stButton > button, .stDownloadButton > button {
    width: 100%;
    border: none;
    border-radius: 15px;
    padding: 15px;
    font-size: 18px;
    font-weight: bold;
    color: white;
    background: linear-gradient(90deg, #8B5CF6, #06B6D4);
}

.stDownloadButton > button,
.stDownloadButton > button:hover,
.stDownloadButton > button:focus,
.stDownloadButton > button:active,
.stDownloadButton > button:focus:not(:active) {
    background: #1B3A5C;
    border: none;
    color: white !important;
}
.stDownloadButton > button p {
    color: white !important;
}

section[data-testid="stSidebar"] { background: #E2E8F0; }
</style>
""",
unsafe_allow_html=True
)

# ==================================
# TITLE
# ==================================
st.title("🤖 RecruitIQ Resume Screening Agent")
st.markdown("### AI-Powered Candidate Ranking and Resume Analysis Dashboard")
st.markdown("---")

# ==================================
# UPLOAD SECTION
# ==================================
left, right = st.columns(2)

with left:
    st.markdown("""
    <div class="card">
    <h3>📂 Upload Multiple Resumes</h3>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Choose Resume Files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="resume_upload"
    )

    st.session_state.uploaded_resumes = uploaded_files if uploaded_files is not None else []
    
    if st.session_state.uploaded_resumes:
        st.write("📄 Resume Files Received:")
        for f in st.session_state.uploaded_resumes:
            st.write(f"• {f.name} ({f.size} bytes)")

with right:
    st.markdown("""
    <div class="card">
    <h3>📄 Upload Job Description</h3>
    </div>
    """, unsafe_allow_html=True)

    jd_file_upload = st.file_uploader(
        "Choose Job Description",
        type=["txt", "docx", "pdf"],
        key="jd_upload"
    )

    if jd_file_upload is not None:
        if st.session_state.jd_file is None or st.session_state.jd_file.name != jd_file_upload.name:
            st.session_state.jd_file = jd_file_upload
            st.session_state.processed = False   
    elif jd_file_upload is None and st.session_state.jd_file is not None:
        st.session_state.jd_file = None

    if st.session_state.jd_file:
        st.write("📄 JD File Received:")
        st.write(f"• {st.session_state.jd_file.name} ({st.session_state.jd_file.size} bytes)")

st.markdown("---")

# ==================================
# METRICS CALCULATION
# ==================================
ranked = st.session_state.ranked_candidates
df = st.session_state.ranking_df
current_resumes = st.session_state.uploaded_resumes

total_resumes_count = len(current_resumes)
top_candidate_name = ranked[0]["name"] if len(ranked) > 0 else "—"

average_score_val = 0.0
hire_count_val = 0
second_round_count_val = 0
reject_count_val = 0

if not df.empty and "score" in df.columns and "recommendation" in df.columns:
    average_score_val = round(df["score"].mean(), 2)
    hire_count_val = len(df[df["recommendation"] == "Hire"])
    second_round_count_val = len(df[df["recommendation"] == "Second Round"])
    reject_count_val = len(df[df["recommendation"] == "Reject"])

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Resumes", total_resumes_count)
with col2:
    st.metric("Top Candidate", top_candidate_name)
with col3:
    st.metric("Average Score", f"{average_score_val}%")
with col4:
    st.metric("Hires", hire_count_val)
with col5:
    st.metric("Second Round", second_round_count_val)
with col6:
    st.metric("Rejects", reject_count_val)

st.markdown("---")

# ==================================
# PROCESSING (Triggers Rerun)
# ==================================
resumes_ready = len(st.session_state.uploaded_resumes) > 0
jd_ready = st.session_state.jd_file is not None

if resumes_ready and jd_ready and not st.session_state.processed:
    with st.spinner("Analyzing resumes against the Job Description..."):
        ranking_df, comparison_df, ranked_candidates = process_resumes(
            st.session_state.uploaded_resumes,
            st.session_state.jd_file
        )

        st.session_state.ranked_candidates = ranked_candidates
        st.session_state.ranking_df = ranking_df
        st.session_state.comparison_df = comparison_df
        st.session_state.processed = True
        st.session_state.data_ready = True
        st.session_state.report_generated = False 

        st.success("Analysis completed successfully!")
        
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

# ==================================
# CANDIDATE RANKINGS & OVERVIEW
# ==================================
if len(st.session_state.ranked_candidates) > 0:
    st.subheader("🏆 Candidate Rankings & Overview")
    
    table_data = []
    for c in st.session_state.ranked_candidates:
        table_data.append({
            "Rank": c.get("rank", "-"),
            "Candidate Name": c.get("name", "Unknown"),
            "Score": f"{c.get('score', 0)}%",
            "Recommendation": c.get("recommendation", "-"),
            "Matched Skills": ", ".join(c.get("matched_skills", [])) if c.get("matched_skills") else "None",
            "Missing Skills": ", ".join(c.get("missing_skills", [])) if c.get("missing_skills") else "None"
        })
    
    overview_df = pd.DataFrame(table_data)
    st.table(overview_df)

# ==================================
# RAW DATA VIEW (JSON)
# ==================================
if len(st.session_state.ranked_candidates) > 0:
    st.markdown("## 📦Candidate Data")
    
    raw_json_data = []
    for c in st.session_state.ranked_candidates:
        raw_json_data.append({
            "Rank": c.get("rank", 0),
            "Candidate Name": c.get("name", "Unknown"),
            "Score": f"{c.get('score', 0)}%",
            "Recommendation": c.get("recommendation", "-"),
            "Matched Skills": c.get("matched_skills", []), 
            "Missing Skills": c.get("missing_skills", [])  
        })
    
    st.json(raw_json_data)

# ==================================
# CANDIDATE DETAILS
# ==================================
if len(st.session_state.ranked_candidates) > 0:
    st.markdown("## ⭐ Candidate Details")

    for candidate in st.session_state.ranked_candidates:
        st.markdown("<div class='card'></div>", unsafe_allow_html=True)
        st.subheader(candidate["name"])

        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            st.metric("Rank", candidate["rank"])
        with d_col2:
            st.metric("Score", f"{candidate['score']}%")
        with d_col3:
            st.metric("Recommendation", candidate["recommendation"])

        st.progress(candidate["score"] / 100)

        st.write("### ✅ Matched Skills")
        if len(candidate["matched_skills"]) > 0:
            st.success(", ".join(candidate["matched_skills"]))
        else:
            st.warning("No matched skills")

        st.write("### ❌ Missing Skills")
        if len(candidate["missing_skills"]) > 0:
            st.error(", ".join(candidate["missing_skills"]))
        else:
            st.success("No missing skills")

        st.markdown("---")

# ==================================
# INTERVIEW QUESTIONS
# ==================================
if len(st.session_state.ranked_candidates) > 0:
    top_cand = st.session_state.ranked_candidates[0]

    st.markdown(f"## 💡 Interview Questions — Top Candidate: {top_cand['name']}")

    skills_for_questions = list(set(
        top_cand.get("matched_skills", []) +
        top_cand.get("missing_skills", [])
    ))

    questions = generate_questions(skills_for_questions)

    if questions and len(questions) > 0:
        for i, question in enumerate(questions, start=1):
            st.info(f"Q{i}. {question}")
    else:
        st.warning("No interview questions available.")

    st.markdown("---")

# ==================================
# GENERATE REPORTS AUTOMATICALLY
# ==================================
if (
    st.session_state.data_ready
    and st.session_state.ranked_candidates
    and not st.session_state.report_generated
):
    try:
        generate_csv(st.session_state.ranked_candidates)
        generate_excel(st.session_state.ranked_candidates)
        generate_pdf(st.session_state.ranked_candidates)

        for candidate in st.session_state.ranked_candidates:
            save_scorecard(candidate)

        st.session_state.report_generated = True
    except Exception as e:
        st.error(f"Report generation failed: {e}")

# ==================================
# DOWNLOAD REPORTS
# ==================================
if st.session_state.report_generated:
    st.markdown("## 📑 Reports")

    r_col1, r_col2, r_col3 = st.columns(3)

    with r_col1:
        if os.path.exists("reports/report.csv"):
            with open("reports/report.csv", "rb") as file:
                st.download_button("⬇ Download CSV", data=file, file_name="report.csv", mime="text/csv")

    with r_col2:
        if os.path.exists("reports/report.xlsx"):
            with open("reports/report.xlsx", "rb") as file:
                st.download_button("⬇ Download Excel", data=file, file_name="report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with r_col3:
        if os.path.exists("reports/report.pdf"):
            with open("reports/report.pdf", "rb") as file:
                st.download_button("⬇ Download PDF", data=file, file_name="report.pdf", mime="application/pdf")

    st.markdown("---")

# ==================================
# FOOTER
# ==================================
st.markdown(
    """
    <center>
    <h3 style='color:#06B6D4;'>🤖 RecruitIQ Resume Screening Agent</h3>
    <p style='color:#475569;'>AI Powered Candidate Ranking • Comparison • Reports • Interview Questions</p>
    </center>
    """,
    unsafe_allow_html=True
)