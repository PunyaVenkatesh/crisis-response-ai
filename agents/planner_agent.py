"""Planner Agent — sequences the response into time-phased, owned actions."""

from core.llm import get_llm
from core.schemas import ActionPlan, ResourcePlan, SituationAssessment
from utils.structured import call_structured

SYSTEM = """You are the operations planner in an emergency operations centre.

Turn the assessment and resource plan into a time-phased action plan.

Rules:
- Phases are 0-1h (immediate life safety), 1-6h (stabilisation), 6-24h (recovery
  and handover). There must be at least one 0-1h action.
- Every action needs a named owner role (e.g. "Fire Ground Commander"), not a
  person's name, and a success criterion that someone could actually verify.
- Do not plan actions that depend on resources listed as shortfalls unless the
  action is to obtain them.
- Priority 1 actions are those where delay costs lives."""


def run_planner_agent(
    assessment: SituationAssessment, resources: ResourcePlan, llm=None
) -> ActionPlan:
    llm = llm or get_llm(temperature=0.2)
    user = (
        f"Situation assessment:\n{assessment.model_dump_json(indent=2)}\n\n"
        f"Resource plan:\n{resources.model_dump_json(indent=2)}\n\n"
        "Produce the action plan."
    )
    return call_structured(llm, SYSTEM, user, ActionPlan)
