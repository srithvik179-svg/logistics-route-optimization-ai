# prompt_router.py
# Routes natural language prompts to matching logistics domains based on keyword patterns.
import re
from typing import Dict, Any

class PromptRouter:
    @staticmethod
    def route_query(prompt: str) -> str:
        """Classifies the prompt into a specific logistics analytical domain.
        
        Args:
            prompt: Raw user input text.
            
        Returns:
            String domain category label.
        """
        p = prompt.lower()
        
        if any(w in p for w in ["breach", "sla", "predict", "late", "delay"]):
            return "sla_prediction"
        elif any(w in p for w in ["cheapest", "cost", "price", "optimize", "saving", "financial"]):
            return "cost_optimization"
        elif any(w in p for w in ["corridor", "route", "transit", "distance", "bottleneck"]):
            return "corridor_intelligence"
        elif any(w in p for w in ["reverse", "return", "refurb", "recycle", "defect"]):
            return "reverse_logistics"
        elif any(w in p for w in ["agent", "orchestrat", "workflow", "decision"]):
            return "ai_orchestrator"
        elif any(w in p for w in ["report", "executive", "summary", "generator"]):
            return "executive_report"
        else:
            # Default to unified network health / command center overview
            return "network_health"
