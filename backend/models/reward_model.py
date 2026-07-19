"""Pydantic model representing Reinforcement Learning reward and penalty configuration weights."""

from pydantic import BaseModel, Field


class RewardConfig(BaseModel):
    """Stores the reward system coefficients and penalty thresholds."""
    reward_cost_weight: float = Field(default=0.4, description="Weight reward multiplier for lower transport cost")
    reward_time_weight: float = Field(default=0.4, description="Weight reward multiplier for lower transit duration")
    reward_sla_weight: float = Field(default=0.2, description="Weight reward multiplier for higher SLA compliance")
    reward_capacity_weight: float = Field(default=0.2, description="Weight reward multiplier for higher capacity utilization")
    reward_efficiency_weight: float = Field(default=0.2, description="Weight reward multiplier for operational efficiency")
    
    penalty_invalid_route: float = Field(default=-100.0, description="Penalty for disconnected path transitions")
    penalty_capacity_overflow: float = Field(default=-50.0, description="Penalty for capacity threshold breaches")
    penalty_sla_breach: float = Field(default=-30.0, description="Penalty for breaching delivery SLA targets")
