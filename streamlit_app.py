import json, tempfile, os, io
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

# ----- import your agents -------------------------------------------------
from agents.evaluator.evaluator_agent import EvaluatorAgent
from agents.coach.coach import CoachAgent
from ingestion.resume_reviewer.parser import parse_resume
from streamlit_pdf_viewer import pdf_viewer

# path to role-keyword file
KW_PATH = Path(__file__).parent / "agents" / "coach" / "role_keywords.yaml"

# -------------------------------------------------------------------------
st.set_page_config(page_title="LLM CV Evaluator", layout="wide")
st.title("📄 CV Evaluation & Feedback Demo")

# -------- sidebar: configuration ----------------------------------------
with st.sidebar:
    st.header("🔑 API settings")
    st.text_input("OpenAI API key", type="password", key="openai_api_key")
    st.radio("Model provider", ["openai", "google"], key="model_provider")
    st.divider()
    role = st.selectbox("Target role", ["Software Engineer", "Product Manager"])

# -------------------------------------------------------------------------
# 1. Upload PDF
pdf_file = st.file_uploader("Upload your PDF résumé", type=["pdf"])

if pdf_file:
    # keep a temp file for agents that expect a path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        pdf_path = tmp.name

    st.success("PDF received")

    # ---------------------------------------------------------------------
    # 2. (Placeholder) Parser call
    # ---------------------------------------------------------------------
    # 🔧 Replace the block below with your colleague’s actual parser
    #     that returns `resume_structured` (dict).

    # inside the placeholder block
    parsed = parse_resume(pdf_path, convert_to_md=False)
    resume_text = parsed.text
    resume_structured = parsed.structured     # new attribute
    cleaned_markdown = parsed.text            # still available if you need it
    # 🔧 END placeholder
    # ---------------------------------------------------------------------

    # Persist parsed JSON so reruns don’t repeat work
    st.session_state["resume_structured"] = resume_structured
    st.session_state["pdf_path"] = pdf_path
    st.session_state["resume_text"] = resume_text
    st.session_state["role"] = role
    st.subheader("📄 Résumé preview")
    pdf_viewer(st.session_state["pdf_path"], height=700)

if "resume_structured" in st.session_state:
    col_eval, col_fb = st.columns([2, 3], gap="large")

    # ---------------------------------------------------------------------
    # 3. EvaluatorAgent
    # ---------------------------------------------------------------------
    with col_eval:
        st.subheader("Rubric scores")
        evaluator = EvaluatorAgent(model_provider=st.session_state["model_provider"])

        with st.spinner("Scoring résumé…"):
            report = evaluator(
                raw_text = st.session_state["resume_text"],
                structured_json=st.session_state["resume_structured"],
                role=st.session_state["role"],
            )

        st.json(report, expanded=False)

        # Radar chart
        df = pd.DataFrame({
            "dimension": [k.capitalize() for k in report["scores"] if k != "overall"],
            "score": [v for k, v in report["scores"].items() if k != "overall"],
        })
        fig = px.line_polar(df, r="score", theta="dimension",
                            line_close=True, range_r=[0, 5])
        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------------------
    # 4. CoachAgent
    # ---------------------------------------------------------------------
    with col_fb:
        st.subheader("Actionable feedback")
        coach = CoachAgent(keyword_path=KW_PATH,
                           model_provider=st.session_state["model_provider"])
        with st.spinner("Generating advice…"):
            feedback = coach(
                target_role=st.session_state["role"],
                evaluation_json=report,
                resume_structured=st.session_state["resume_structured"],
            )

        # Critical → Important → Nice-to-have
        for bucket in ["critical", "important", "nice_to_have"]:
            tips = feedback["advice"].get(bucket, [])
            if not tips:
                continue
            st.markdown(f"### {bucket.title()} ({len(tips)})")
            for tip in tips:
                st.markdown(f"- {tip}")

        # Rewrites
        if feedback.get("rewrites"):
            st.markdown("### ✍️ Example rewrites")
            for rw in feedback["rewrites"]:
                st.markdown(f"**Before**: {rw['before']}")
                st.markdown(f"**After**:  {rw['after']}")
                st.markdown("---")

# # after you finish parsing & store pdf_path / report / feedback …

# col_left, col_mid, col_right = st.columns([2.5, 2, 3], gap="large")

# # ---- PDF preview ---------------------------------------------------
# with col_left:
#     st.subheader("📄 Résumé preview")
#     pdf_viewer(st.session_state["pdf_path"], height=700)

# # ---- Scores radar --------------------------------------------------
# with col_mid:
#     st.subheader("Rubric scores")
#     # (existing radar-chart code)

# # ---- Feedback ------------------------------------------------------
# with col_right:
#     st.subheader("Actionable feedback")
#     # (existing advice / rewrites rendering)


# house-keeping: remove temp file on app reload
if tmp_path := st.session_state.get("pdf_path"):
    if not st.sidebar.checkbox("Keep uploaded temp file", value=False):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
