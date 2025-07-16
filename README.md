# dialoge_systems_2025

## CV Evaluator: Multi-Agent Resume Feedback App 📄🤖

This app analyzes your CV using multiple LangGraph-based agents to generate targeted evaluation, actionable feedback, and live market insights tailored to your chosen role and country.

---

## 🚀 Quickstart

### 1. Clone and Install

#### On Linux/Mac:

```bash
git clone https://github.com/Nurmukhammad-Aberkulov/dialoge_systems_2025.git
cd dialogue_systems_2025
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### On Windows (PowerShell):

```powershell
git clone https://github.com/Nurmukhammad-Aberkulov/dialoge_systems_2025.git
cd dialogue_systems_2025
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the App

#### On Linux/Mac:

```bash
streamlit run streamlit_app.py
```

#### On Windows (PowerShell):

```powershell
python -m streamlit run streamlit_app.py
```

### What It Does

📄 Resume Parsing
Uses a parser to extract structured information and raw text from the uploaded PDF.

🧪 EvaluatorAgent
Scores the CV across multiple rubric dimensions for a specific job role.

🧭 CoachAgent
Offers structured, bucketed advice (Critical / Important / Nice-to-have) and example rewrites.

🌐 MarketInsightsAgent
Searches live job postings for recruiter expectations: top keywords, soft skills, and salary hints.

🔁 LangGraph DAG
Orchestrates the full pipeline: parsing → evaluation → coaching + market insights (in parallel).

### Example Usage

Upload your CV (PDF)

Select your target role and country

Get:

Score breakdown

Actionable feedback with rewrites

Recruiter keyword expectations and salary ranges

### Project Structure

```bash
agents/
  ├── evaluator/
  ├── coach/
  ├── insights/
  └── pipeline.py          # LangGraph DAG definition

ingestion/
  └── resume_reviewer/
streamlit_app.py           # Streamlit UI
requirements.txt
README.md

```
