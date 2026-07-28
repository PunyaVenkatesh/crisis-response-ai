"""Communications Agent — writes what gets said, to whom, and what must not be said."""

from core.llm import get_llm
from core.schemas import ActionPlan, CommunicationSet, SituationAssessment
from utils.structured import call_structured

SYSTEM = """You are the public information officer in an emergency operations centre.

Produce the communications set for this incident.

Rules:
- public_alert is an emergency broadcast: under 320 characters, plain language,
  leads with the action the public must take, no jargon, no hedging.
- press_statement is two short paragraphs: what is known, what is being done.
- internal_brief is for responders: current picture, priorities, known gaps.
- Never state casualty numbers as fact when the assessment confidence is below
  0.7 — describe them as preliminary.
- do_not_say lists specific claims that are unverified or would cause panic, so
  the incident controller knows what to keep out of the briefing."""


def run_comms_agent(
    assessment: SituationAssessment, plan: ActionPlan, llm=None
) -> CommunicationSet:
    llm = llm or get_llm(temperature=0.3)
    user = (
        f"Situation assessment:\n{assessment.model_dump_json(indent=2)}\n\n"
        f"Action plan:\n{plan.model_dump_json(indent=2)}\n\n"
        "Produce the communications set."
    )
    return call_structured(llm, SYSTEM, user, CommunicationSet)
