"""Resource Agent — commits available resources against the assessed threats."""

from core.llm import get_llm
from core.schemas import ResourcePlan, SituationAssessment
from utils.structured import call_structured

SYSTEM = """You are the resource coordination officer in an emergency operations centre.

You are given a situation assessment and an inventory of what is actually
available. Allocate only from that inventory.

Rules:
- Never allocate a resource that is not in the inventory, and never allocate more
  units than exist.
- Every allocation needs a rationale tied to a specific threat or hazard.
- If the assessed need exceeds what is available, say so in shortfalls rather
  than quietly under-serving a threat.
- escalation_required is true when shortfalls would cost lives or when severity
  is 4 or higher."""


def run_resource_agent(
    assessment: SituationAssessment, inventory: str, llm=None
) -> ResourcePlan:
    llm = llm or get_llm(temperature=0.1)
    user = (
        f"Situation assessment:\n{assessment.model_dump_json(indent=2)}\n\n"
        f"Available resources:\n{inventory}\n\n"
        "Produce the resource plan."
    )
    return call_structured(llm, SYSTEM, user, ResourcePlan)
