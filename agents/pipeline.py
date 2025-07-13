# agents/pipeline.py  (only the highlighted lines change)
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableParallel

from agents.evaluator.evaluator_agent import EvaluatorAgent
from agents.coach.coach import CoachAgent
from agents.insights.market_insights import MarketInsightsAgent

KW_PATH = "agents/coach/role_keywords.yaml"


class PipelineState(TypedDict):
    pdf_path: str
    resume_text: str        # ➊ NEW
    structured_json: dict
    role: str
    country: str
    evaluation_report: dict
    coach: dict
    market: dict




def run_coach(state: PipelineState) -> dict:
    coach = CoachAgent(keyword_path=KW_PATH)
    fb = coach(
        target_role=state["role"],
        evaluation_json=state["evaluation_report"],
        resume_structured=state["structured_json"],
    )
    return fb                  



def run_market(state: PipelineState) -> dict:
    insights = MarketInsightsAgent()(
        role=state["role"],
        country=state["country"],
        structured_json=state["structured_json"],
    )
    return {"market": insights}


def _build_graph():
    g = StateGraph(PipelineState)

    # —— evaluator wrapper uses raw_text instead of pdf_path ————————
    def _eval_node(state: PipelineState):
        report = EvaluatorAgent()(
            raw_text=state["resume_text"],   # ➋ FIXED
            structured_json=state["structured_json"],
            role=state["role"],
        )
        return {"evaluation_report": report}

    g.add_node("evaluator", _eval_node)
    g.add_node(
        "after_eval",
        RunnableParallel(coach=run_coach, market=run_market),
    )

    g.set_entry_point("evaluator")
    g.add_edge("evaluator", "after_eval")
    g.add_edge("after_eval", END)
    return g.compile()


CV_GRAPH = _build_graph()


# … at the very end …
def run_pipeline(pdf_path, resume_text, structured_json, role, country):
    initial = {
        "pdf_path": pdf_path,
        "resume_text": resume_text,
        "structured_json": structured_json,
        "role": role,
        "country": country,
    }
    state = CV_GRAPH.invoke(initial)
    return {
        "report": state["evaluation_report"],   # <- new key
        "coach":  state["coach"],
        "market": state["market"],
    }

