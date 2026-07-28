"""Typed contracts between agents.

Every agent hands the next one a validated object, not free text. This is what
stops one agent's malformed output from silently corrupting the whole chain.
"""

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class Hazard(BaseModel):
    name: str = Field(description="Short hazard name, e.g. 'structural collapse'")
    likelihood: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]


class SituationAssessment(BaseModel):
    """Output of the Situation Agent."""

    incident_type: str
    severity: int = Field(ge=1, le=5, description="1 = minor, 5 = catastrophic")
    confidence: float = Field(ge=0.0, le=1.0)
    location: str
    people_at_risk: int = Field(ge=0)
    immediate_threats: List[str]
    hazards: List[Hazard]
    information_gaps: List[str] = Field(
        default_factory=list,
        description="What responders still do not know.",
    )

    @field_validator("immediate_threats", "hazards")
    @classmethod
    def not_empty(cls, v):
        if not v:
            raise ValueError("must contain at least one entry")
        return v


class ResourceAllocation(BaseModel):
    resource: str
    quantity: int = Field(ge=0)
    assigned_to: str = Field(description="Task or zone this resource is committed to")
    rationale: str


class ResourcePlan(BaseModel):
    """Output of the Resource Agent."""

    allocations: List[ResourceAllocation]
    shortfalls: List[str] = Field(
        default_factory=list,
        description="Needs that available resources cannot cover",
    )
    escalation_required: bool


class ActionItem(BaseModel):
    phase: Literal["0-1h", "1-6h", "6-24h"]
    priority: int = Field(ge=1, le=3, description="1 = highest")
    owner: str
    task: str
    success_criteria: str


class ActionPlan(BaseModel):
    """Output of the Planner Agent."""

    objective: str
    actions: List[ActionItem]
    key_risks: List[str] = Field(default_factory=list)

    @field_validator("actions")
    @classmethod
    def has_immediate_action(cls, v):
        if not any(a.phase == "0-1h" for a in v):
            raise ValueError("plan must contain at least one 0-1h action")
        return v


class CommunicationSet(BaseModel):
    """Output of the Communications Agent."""

    public_alert: str = Field(
        max_length=320, description="Emergency broadcast / SMS text"
    )
    press_statement: str
    internal_brief: str
    do_not_say: List[str] = Field(
        default_factory=list,
        description="Claims that would be unsafe or unverified to make publicly",
    )


class IncidentResponse(BaseModel):
    """The full assembled response — one object the UI renders and exports."""

    assessment: SituationAssessment
    resources: ResourcePlan
    plan: ActionPlan
    comms: CommunicationSet
