# streamlit_app.py
import os, tempfile, json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_pdf_viewer import pdf_viewer

from ingestion.resume_reviewer.parser import parse_resume
from agents.pipeline import run_pipeline

# ── page & sidebar ───────────────────────────────────────────────────────
st.set_page_config(page_title="LLM CV Evaluator", layout="wide")
st.title("📄 CV Evaluation & Feedback Demo")

with st.sidebar:
    st.header("🔑 API")
    st.text_input("OpenAI API key", type="password", key="openai_api_key")
    st.radio("Model provider", ["openai", "google"], key="model_provider")
    st.divider()
    role    = st.selectbox("Target role", ["Software Engineer", "Product Manager"])
    country = st.text_input("Target country", value="Germany")
    st.session_state.update(role=role, country=country)

# ── upload résumé ────────────────────────────────────────────────────────
resume_file = st.file_uploader("Upload your résumé (PDF, PNG, DOCX)", type=["pdf", "png", "docx"])
if resume_file:
    # Get file extension for proper temporary file naming
    file_extension = resume_file.name.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
        tmp.write(resume_file.read())
        resume_path = tmp.name

    parsed = parse_resume(resume_path, convert_to_md=False)
    st.session_state.update(
        pdf_path=resume_path,
        resume_text=parsed.text,
        resume_structured=parsed.structured,
    )

    st.success("Résumé processed")
    # Only show PDF viewer for PDF files
    if file_extension == 'pdf':
        pdf_viewer(resume_path, height=550)
    else:
        st.info(f"Uploaded {file_extension.upper()} file processed successfully")

    with st.spinner("Running multi-agent analysis …"):
        result = run_pipeline(
            pdf_path        = resume_path,
            resume_text     = parsed.text,
            structured_json = parsed.structured,
            role            = role,
            country         = country,
        )

    # unwrap market dict if double-nested
    market_raw = result["market"]
    insights = market_raw["market"] if isinstance(market_raw, dict) and "market" in market_raw else market_raw

    st.session_state.update(
        report   = result["report"],
        feedback = result["coach"],
        insights = insights,
    )

# ── show tabs if we have results ─────────────────────────────────────────
if "report" in st.session_state:
    tab_scores, tab_feedback, tab_market = st.tabs(
        ["Scores", "Feedback", "Market insights"]
    )

    # # ▸ Scores
    # with tab_scores:
    #     rep = st.session_state["report"]
    #     st.subheader("Rubric scores")
    #     st.json(rep, expanded=False)

    #     # Normalize scores to 0–5 scale for radar chart
    #     radar_df = pd.DataFrame({
    #         "dimension": [k.capitalize() for k in rep["scores"] if k != "overall"],
    #         "score":     [v / 20 for k, v in rep["scores"].items() if k != "overall"],
    #     })

    #     fig = px.line_polar(radar_df, r="score", theta="dimension",
    #                         line_close=True, range_r=[0, 5])
    #     st.plotly_chart(fig, use_container_width=True)

    with tab_scores:
        rep = st.session_state["report"]
        st.subheader("Rubric scores")
        st.json(rep, expanded=False)

        raw_scores = {k: v for k, v in rep["scores"].items() if k != "overall"}

        max_score = max(raw_scores.values())
        normalize = max_score > 5

        # Normalize and scale up for better visualization
        scale = 1 if not normalize else 5 / max_score  # keep max ~5
        radar_df = pd.DataFrame({
            "dimension": [k.capitalize() for k in raw_scores],
            "score":     [v * scale for v in raw_scores.values()],
        })

        fig = px.line_polar(radar_df, r="score", theta="dimension",
                            line_close=True, range_r=[0, 5])
        st.plotly_chart(fig, use_container_width=True)




    # ▸ Feedback
    with tab_feedback:
        fb = st.session_state["feedback"]
        st.subheader("Actionable feedback")
        for bucket in ["critical", "important", "nice_to_have"]:
            tips = fb.get("advice", {}).get(bucket, [])
            if tips:
                with st.expander(f"{bucket.title()} ({len(tips)})", expanded=True):
                    st.markdown("\n".join(f"- {t}" for t in tips))
        if fb.get("rewrites"):
            st.markdown("### ✍️ Example rewrites")
            for rw in fb["rewrites"]:
                st.markdown(f"**Before:** {rw['before']}")
                st.markdown(f"**After:**  {rw['after']}")
                st.markdown("---")

    # ▸ Market insights
    with tab_market:
        mi = st.session_state["insights"]
        st.subheader(f"Recruiter trends for {country}")
        st.json(mi, expanded=False)

        top_kw   = ", ".join(mi.get("top_keywords", [])) or "—"
        soft_kw  = ", ".join(mi.get("soft_skills", []))  or "—"
        salary   = mi.get("salary_hint") or "—"

        st.markdown(f"**Top keywords:** {top_kw}")
        st.markdown(f"**Soft skills:** {soft_kw}")
        st.markdown(f"**Salary range:** {salary}")

        # One-sentence textual summary
        if mi.get("top_keywords") or mi.get("salary_hint"):
            summary = (
                f"For {role}s in {country}, recruiters most often mention "
                f"**{top_kw}**, emphasise soft skills like **{soft_kw}**, "
                f"and advertise salaries around **{salary}**."
            )
            st.markdown("---")
            st.markdown(summary)

# ── cleanup tmp file on reload (unless user keeps it) ────────────────────
if (tmp := st.session_state.get("pdf_path")) and not st.sidebar.checkbox(
    "Keep temp file", value=False
):
    try:
        os.unlink(tmp)
    except OSError:
        pass
