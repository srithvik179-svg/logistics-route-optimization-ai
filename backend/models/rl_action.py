"""Pydantic model representing the logistics network Reinforcement Learning action space."""

from pydantic import BaseModel, Field
from typing import Optional


class RLAction(BaseModel):
    """Represents a single available decision action in the RL environment."""
    action_type: str = Field(description="Type of action: MOVE_TO_ADJACENT, SELECT_ALTERNATE_ROUTE, CHOOSE_PARTNER, ALLOCATE_CAPACITY, TERMINATE_ROUTE")
    target_hub: Optional[str] = Field(default=None, description="Next Node ID target of the action if moving")
    partner_id: Optional[str] = Field(default=None, description="Transportation partner selected")
    capacity_allocation: Optional[float] = Field(default=None, description="Volume capacity load allocated")
