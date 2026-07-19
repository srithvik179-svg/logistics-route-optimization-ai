"""Pydantic model representing the logistics network Reinforcement Learning state space."""

from pydantic import BaseModel, Field


class RLState(BaseModel):
    """Represents a single state in the Reinforcement Learning environment."""
    current_hub: str = Field(description="Current Node ID of the agent")
    destination_hub: str = Field(description="Destination Node ID target")
    accumulated_cost: float = Field(default=0.0, description="Total transportation cost accumulated so far")
    accumulated_time: float = Field(default=0.0, description="Total transit duration in days accumulated so far")
    remaining_capacity: float = Field(default=100.0, description="Remaining link capacity in volume units")
    sla_status: str = Field(default="within_sla", description="SLA compliance status: within_sla or breached")
    partner_availability: float = Field(default=1.0, description="Fraction of active partners available (0.0 to 1.0)")
    network_congestion: float = Field(default=0.0, description="Average utilization rate of current link/hub")
    route_score: float = Field(default=50.0, description="Composite route score of the current location edge")
