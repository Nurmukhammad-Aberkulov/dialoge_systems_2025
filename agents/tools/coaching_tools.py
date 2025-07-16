# agents/tools/coaching_tools.py
from typing import List
from pydantic import BaseModel, Field
from langchain.tools import Tool, DuckDuckGoSearchRun


# ── helper funcs ─────────────────────────────────────────────
def keyword_gap_finder(resume_tokens: List[str],
                       target_keywords: List[str]) -> List[str]:
    """Keywords present in the role but missing from the résumé."""
    resume_set = {t.lower() for t in resume_tokens}
    return [kw for kw in target_keywords if kw.lower() not in resume_set]


def improve_bullet(bullet: str) -> str:
    """Quick wording upgrade for a résumé bullet."""
    replacements = {"responsible for": "led", "worked on": "delivered"}
    for bad, good in replacements.items():
        bullet = bullet.replace(bad, good)
    return bullet


def lookup_salary(title: str, region: str = "US") -> str:
    """Dummy salary lookup (swap for real API)."""
    data = {("software engineer", "US"): "$185 k",
            ("product manager",  "US"): "$210 k"}
    return data.get((title.lower(), region.upper()), "N/A")


# ── input schemas (tiny) ─────────────────────────────────────
class GapInput(BaseModel):
    resume_tokens: List[str] = Field(..., description="Tokenised résumé text")
    target_keywords: List[str] = Field(..., description="Role keywords")


class BulletInput(BaseModel):
    bullet: str = Field(..., description="Single résumé bullet")


class SalaryInput(BaseModel):
    title: str  = Field(..., description="Job title e.g. 'Software Engineer'")
    region: str = Field("US", description="ISO region code, default US")


# ── LangChain-ready tools ───────────────────────────────────
keyword_gap_tool = Tool.from_function(
    name="keyword_gap_finder",
    func=keyword_gap_finder,
    description="Find keywords missing from a résumé.",
    args_schema=GapInput,
    return_direct=True,
)

bullet_improver_tool = Tool.from_function(
    name="bullet_improver",
    func=improve_bullet,
    description="Rewrite a weak résumé bullet to show impact.",
    args_schema=BulletInput,
    return_direct=True,
)

salary_lookup_tool = Tool.from_function(
    name="salary_lookup",
    func=lookup_salary,
    description="Return typical total compensation for a role in a region.",
    args_schema=SalaryInput,
    return_direct=True,
)

web_search_tool = DuckDuckGoSearchRun(name="web_search")
