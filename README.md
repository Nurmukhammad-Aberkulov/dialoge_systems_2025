# dialoge_systems_2025

## CV Evaluator: Multi-Agent Resume Feedback App 📄🤖

This app analyzes your CV using multiple LangGraph-based agents to generate targeted evaluation, actionable feedback, and live market insights tailored to your chosen role and country.
slides:
https://docs.google.com/presentation/d/1ey0MPfkkJC2pLusqfVlbmG5RLaU3whQT/edit?usp=sharing&ouid=104202224460510555998&rtpof=true&sd=true    


demo:
https://drive.google.com/file/d/1Iu-MO-zWno7A78Bcv4zElU_pn71jPFyk/view?usp=sharing
---

## 🚀 Quickstart

### 1. Clone and Install

#### On Linux/Mac:

```bash
git clone https://github.com/Nurmukhammad-Aberkulov/dialoge_systems_2025.git
cd dialoge_systems_2025
```
⚠️ IMPORTANT: Make sure you are using Python 3.12. If it's not installed, install it first via pyenv, conda, or your system's package manager.

Recommended to use conda 
```bash
conda create -n test python=3.12
conda activate test
```
Or alternatively
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```
##### Requirements to be installed next
```bash
pip install -r requirements.txt
```

#### On Windows (PowerShell):

```powershell
git clone https://github.com/Nurmukhammad-Aberkulov/dialoge_systems_2025.git
cd dialogue_systems_2025
py -3.12 -m venv .venv
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
Enter Your OPENAI-API-KEY

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
