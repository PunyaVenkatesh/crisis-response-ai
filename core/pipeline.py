"""Orchestration — runs the four agents in sequence with progress callbacks."""

from typing import Callable, Optional

from agents.comms_agent import run_comms_agent
from agents.planner_agent import run_planner_agent
from agents.resource_agent import run_resource_agent
from agents.situation_agent import run_situation_agent
from core.llm import get_llm
from core.schemas import IncidentResponse

DEFAULT_INVENTORY = """- 4 fire appliances (pumpers)
- 2 ambulances, 1 mobile triage unit
- 1 police unit (6 officers)
- 1 rescue helicopter (30 min availability window)
- 200 evacuation centre beds at the regional showgrounds
- 1 hazmat team (45 min transit)"""

AGENT_ORDER = [
    ("Situation Agent", "Assessing the incident"),
    ("Resource Agent", "Allocating available resources"),
    ("Planner Agent", "Sequencing the response"),
    ("Communications Agent", "Drafting public and internal messaging"),
]


def run_pipeline(
    report: str,
    inventory: str = DEFAULT_INVENTORY,
    on_step: Optional[Callable[[int, str], None]] = None,
    llm=None,
) -> IncidentResponse:
    """Run the full four-agent response pipeline.

    ``on_step(index, label)`` is called before each agent runs so the UI can
    show which agent is currently working.
    """
    llm = llm or get_llm()

    def step(i: int):
        if on_step:
            on_step(i, AGENT_ORDER[i][1])

    step(0)
    assessment = run_situation_agent(report, llm=llm)

    step(1)
    resources = run_resource_agent(assessment, inventory, llm=llm)

    step(2)
    plan = run_planner_agent(assessment, resources, llm=llm)

    step(3)
    comms = run_comms_agent(assessment, plan, llm=llm)

    return IncidentResponse(
        assessment=assessment, resources=resources, plan=plan, comms=comms
    )
