"""Pydantic model representing the compiled AI decision support preparation payload."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any
from backend.models.feature_vector import FeatureVector
from backend.models.recommendation_candidate import RecommendationCandidate


class AIDecisionSupportPayload(BaseModel):
    """Envelope containing decision features matrices, scenarios recommendations, and explainability indices."""
    context_id: str = Field(description="Unique ID identifier for this decision support request")
    source: str = Field(description="Starting origin Node ID")
    destination: str = Field(description="Destination Node ID target")
    feature_matrix: Dict[str, FeatureVector] = Field(default_factory=dict, description="Mapped feature vectors by candidate ID")
    scenarios: Dict[str, RecommendationCandidate] = Field(default_factory=dict, description="Best candidate option assigned by scenario name")
    explainability: Dict[str, Any] = Field(default_factory=dict, description="Feature importances, constraint safety, and comparison metrics")
    filters_applied: Dict[str, Any] = {}
    cached: bool = Field(default=False, description="Served from cache flag")
