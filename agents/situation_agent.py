"""Situation Agent — turns a messy incident report into a structured assessment."""

from core.llm import get_llm
from core.schemas import SituationAssessment
from utils.structured import call_structured

SYSTEM = """You are the situation assessment officer in an emergency operations centre.

You receive raw, incomplete and sometimes contradictory field reports. Your job is
to produce a sober, structured assessment that commanders can act on.

Rules:
- Severity is 1 (minor, local response) to 5 (catastrophic, national response).
- Confidence reflects how much the report actually supports your conclusions.
  A vague report should produce low confidence, not confident invention.
- Never invent casualty figures or locations that are not in the report. If a
  number is unknown, estimate conservatively and record it as an information gap.
- information_gaps must list what a commander would need to ask next."""


def run_situation_agent(report: str, llm=None) -> SituationAssessment:
    llm = llm or get_llm(temperature=0.1)
    user = f"Field report:\n\n{report}\n\nProduce the situation assessment."
    return call_structured(llm, SYSTEM, user, SituationAssessment)
