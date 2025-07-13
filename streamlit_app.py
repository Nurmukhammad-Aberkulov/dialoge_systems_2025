import json, tempfile, os, io
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

# ----- import your agents -------------------------------------------------
from agents.evaluator.evaluator_agent import EvaluatorAgent
from agents.coach.coach import CoachAgent

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
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        plain_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    resume_structured = {
        "meta": {"file_name": pdf_file.name},
        "candidate": {"full_name": "Unknown"},
        "sections": {},
    }
    # 🔧 END placeholder
    # ---------------------------------------------------------------------

    # Persist parsed JSON so reruns don’t repeat work
    st.session_state["resume_structured"] = resume_structured
    st.session_state["pdf_path"] = pdf_path
    st.session_state["role"] = role

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
                pdf_path=st.session_state["pdf_path"],
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

# house-keeping: remove temp file on app reload
if tmp_path := st.session_state.get("pdf_path"):
    if not st.sidebar.checkbox("Keep uploaded temp file", value=False):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
