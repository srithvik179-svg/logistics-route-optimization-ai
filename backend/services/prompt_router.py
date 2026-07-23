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
        p = prompt.lower().strip()
        
        # 1. Follow-up / Explanation queries
        if p in ["why", "why?", "explain", "explain why", "how so", "tell me more", "details", "reason"]:
            return "followup_explanation"
        
        # 2. Executive & Business Summaries
        if any(w in p for w in ["business summary", "executive summary", "executive insights", "generate insights", "overview summary", "platform status"]):
            return "executive_summary"
            
        # 3. Hub SLA Breaches
        if ("hub" in p and any(w in p for w in ["breach", "delay", "late", "worst", "most"])) or "highest sla breach" in p:
            return "hub_sla_breach"
            
        # 4. Expensive Corridors & Cost
        if any(w in p for w in ["expensive corridor", "highest logistics cost", "costly route", "costly corridor", "expensive route", "highest cost"]):
            return "expensive_corridors"
            
        # 5. Cost Reduction & Savings Opportunities
        if any(w in p for w in ["reduce logistics cost", "cost saving", "savings opportunity", "reduce cost", "where can we save"]):
            return "cost_savings"
            
        # 6. Overloaded Repair Centers (TPR)
        if any(w in p for w in ["repair center", "tpr", "overloaded", "repair bottleneck", "refurbish queue"]):
            return "tpr_overload"
            
        # 7. Part Delays & Inventory Shortages
        if any(w in p for w in ["part", "parts", "component"]) and any(w in p for w in ["delay", "shortage", "critical", "stockout"]):
            return "part_delays"
            
        # 8. Monthly / Current SLA Exceedances
        if any(w in p for w in ["exceeded sla", "sla breach", "sla risk", "breached this month", "shipments delayed"]):
            return "sla_prediction"
            
        # 9. Reverse Logistics Bottlenecks
        if any(w in p for w in ["reverse logistics", "return bottleneck", "recycle backlog", "returns"]):
            return "reverse_logistics"
            
        # 10. Hub Inventory & Underutilization
        if any(w in p for w in ["warehouse", "inventory", "underutilized", "under-utilized", "hub capacity", "highest inventory"]):
            return "hub_inventory"
            
        # 11. Carbon & Sustainability
        if any(w in p for w in ["carbon", "co2", "sustainability", "emission", "green", "environmental"]):
            return "sustainability"
            
        # 12. Route Optimization Priority & AI Recommendation Explanation
        if any(w in p for w in ["optimize first", "optimization priority", "why ai recommended", "explain route", "recommendation reason"]):
            return "route_optimization_priority"
            
        # 13. Redeployment & Component Harvesting
        if any(w in p for w in ["redeployment", "harvesting", "reuse", "component harvest"]):
            return "redeployment"
            
        # 14. Report Requests
        if "report" in p or "export" in p:
            return "executive_report"
            
        # Fallbacks for general keywords
        if any(w in p for w in ["sla", "breach", "late", "delay"]):
            return "sla_prediction"
        elif any(w in p for w in ["cost", "price", "savings", "financial"]):
            return "cost_savings"
        elif any(w in p for w in ["route", "corridor", "transit", "distance"]):
            return "expensive_corridors"
        elif any(w in p for w in ["reverse", "return", "repair", "refurbish"]):
            return "reverse_logistics"
        else:
            return "network_health"
