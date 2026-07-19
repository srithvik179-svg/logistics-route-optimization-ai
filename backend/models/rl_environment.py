"""Pydantic models representing the generated Reinforcement Learning MDP environment and transitions."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from backend.models.rl_state import RLState
from backend.models.rl_action import RLAction
from backend.models.reward_model import RewardConfig
from backend.models.aco_result import BenchmarkEntry


class RLEpisodeStep(BaseModel):
    """Represents a single state transition step within a simulated RL training episode."""
    step_index: int = Field(description="Step counter")
    state: RLState = Field(description="Pre-transition environment state")
    action: RLAction = Field(description="Action selected by agent")
    next_state: RLState = Field(description="Resulting state post-transition")
    reward: float = Field(description="Numerical reward or penalty feedback received")
    is_terminal: bool = Field(description="Whether transition triggers episode termination")


class RLEpisode(BaseModel):
    """Represents a sequence of transitions from start to target node."""
    episode_id: str = Field(description="Unique ID for this episode simulation")
    steps: List[RLEpisodeStep] = Field(default_factory=list, description="Sequence of steps taken")
    total_reward: float = Field(description="Sum of all reward/penalty feedback received")
    is_success: bool = Field(description="Whether the agent successfully reached target destination without breach")


class RLEnvironment(BaseModel):
    """Full Reinforcement Learning MDP preparation envelope."""
    environment_id: str = Field(description="Unique identifier for this network config environment")
    state_space_size: int = Field(description="Total count of state structures defined")
    action_space_size: int = Field(description="Total count of available action structures defined")
    reward_config: RewardConfig = Field(description="Configured reward/penalty coefficients")
    sample_episodes: List[RLEpisode] = Field(default_factory=list, description="Demonstration episodes for initial agent seeding")
    benchmarks: List[BenchmarkEntry] = Field(default_factory=list, description="Routing benchmark solutions comparison table")
    environment_statistics: Dict[str, Any] = Field(default_factory=dict, description="Topological summary stats")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Served from cache flag")
