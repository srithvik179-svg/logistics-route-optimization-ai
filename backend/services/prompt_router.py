# prompt_router.py
# Advanced Intent & Entity Extraction Engine for RoutePilot AI Assistant.
import re
from typing import Dict, Any, Tuple, Optional

HUBS_MASTER = {
    "HUB-DEL": ["delhi", "delhi hub", "delhi ncr", "hub-del", "delhi ncr hub"],
    "HUB-BLR": ["bangalore", "bengaluru", "bangalore hub", "hub-blr", "bangalore tech hub"],
    "HUB-MUM": ["mumbai", "mumbai hub", "hub-mum", "mumbai logistics center"],
    "HUB-CHE": ["chennai", "chennai hub", "hub-che", "chennai port terminal"],
    "HUB-HYD": ["hyderabad", "hyderabad hub", "hub-hyd", "hyderabad gateway"],
    "HUB-PUN": ["pune", "pune satellite", "pune hub", "hub-pun", "pune industrial hub"],
    "HUB-KOL": ["kolkata", "kolkata satellite", "kolkata hub", "hub-kol", "kolkata eastern hub"],
    "HUB-AHM": ["ahmedabad", "ahmedabad satellite", "ahmedabad hub", "hub-ahm"],
    "HUB-SIN": ["singapore", "singapore hub", "hub-sin"],
    "HUB-KUL": ["kuala lumpur", "kuala lumpur hub", "hub-kul"],
    "HUB-DXB": ["dubai", "dubai hub", "hub-dxb", "dubai middle east hub"],
    "HUB-AMS": ["amsterdam", "amsterdam hub", "hub-ams", "amsterdam euro hub"]
}

class PromptRouter:
    @classmethod
    def resolve_hub(cls, text: Optional[str]) -> Optional[str]:
        """Resolves raw text token to valid Hub_ID."""
        if not text:
            return None
        t = text.lower().strip()
        for hid, aliases in HUBS_MASTER.items():
            if hid.lower() == t:
                return hid
            for a in aliases:
                if a in t:
                    return hid
        return None

    @classmethod
    def extract_locations(cls, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts origin and destination hubs from prompt string."""
        p = prompt.lower().strip()

        # 1. Explicit pattern "from X to Y" or "from X bound for Y"
        m1 = re.search(r"\bfrom\s+(.+?)\s+(?:to|towards|destined for|bound for)\s+(.+?)(?:\s+(?:for|with|via|using|by|in|\?|$)|$)", p)
        if m1:
            orig = cls.resolve_hub(m1.group(1))
            dest = cls.resolve_hub(m1.group(2))
            if orig and dest and orig != dest:
                return orig, dest

        # 2. Pattern "between X and Y"
        m2 = re.search(r"\bbetween\s+(.+?)\s+and\s+(.+?)(?:\s+(?:for|with|via|in|\?|$)|$)", p)
        if m2:
            orig = cls.resolve_hub(m2.group(1))
            dest = cls.resolve_hub(m2.group(2))
            if orig and dest and orig != dest:
                return orig, dest

        # 3. Direct positional scan for all hub mentions
        found = []
        for hid, aliases in HUBS_MASTER.items():
            for a in aliases:
                idx = p.find(a)
                if idx != -1:
                    found.append((idx, hid, len(a)))

        found.sort(key=lambda x: (x[0], -x[2]))
        unique_hubs = []
        seen = set()
        for _, hid, _ in found:
            if hid not in seen:
                unique_hubs.append(hid)
                seen.add(hid)

        if len(unique_hubs) >= 2:
            return unique_hubs[0], unique_hubs[1]
        elif len(unique_hubs) == 1:
            return unique_hubs[0], None

        return None, None

    @classmethod
    def route_and_extract(cls, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Classifies prompt intent and extracts entities."""
        p = prompt.lower().strip()
        orig, dest = cls.extract_locations(prompt)

        # Priority Intent Detection
        if any(w in p for w in ["cheapest", "lowest cost", "cheap route", "least cost", "min cost", "best price"]):
            intent = "cheapest_route"
        elif any(w in p for w in ["fastest", "quickest", "express route", "shortest time", "lowest time", "min time"]):
            intent = "fastest_route"
        elif any(w in p for w in ["scenario", "scenarios", "side-by-side", "side by side", "6 comparison"]):
            intent = "scenario_comparison"
        elif any(w in p for w in ["compare", "comparison", "alternative routes", "options"]):
            intent = "route_comparison"
        elif any(w in p for w in ["route", "corridor", "shipment", "shipping", "deliver", "transit"]) and (orig or dest):
            intent = "route_recommendation"
        elif any(w in p for w in ["carbon", "co2", "sustainability", "emission", "green", "circular score", "circular"]):
            intent = "sustainability"
        elif "sla" in p and any(w in p for w in ["breach", "delay", "late", "worst", "most", "highest"]):
            intent = "hub_sla_breach"
        elif any(w in p for w in ["expensive corridor", "highest logistics cost", "costly route", "costly corridor"]):
            intent = "expensive_corridors"
        elif any(w in p for w in ["reduce logistics cost", "cost saving", "savings opportunity", "reduce cost", "where can we save"]):
            intent = "cost_savings"
        elif any(w in p for w in ["repair center", "tpr", "overloaded", "repair bottleneck", "refurbish queue"]):
            intent = "tpr_overload"
        elif any(w in p for w in ["part", "parts", "component"]) and any(w in p for w in ["delay", "shortage", "critical"]):
            intent = "part_delays"
        elif any(w in p for w in ["warehouse", "inventory", "underutilized", "hub capacity", "stock", "utilization"]):
            intent = "hub_inventory"
        elif any(w in p for w in ["reverse logistics", "return", "recycle", "harvesting", "redeployment"]):
            intent = "reverse_logistics"
        elif any(w in p for w in ["report", "export"]):
            intent = "executive_report"
        elif any(w in p for w in ["map", "topology", "geospatial", "3d"]):
            intent = "geospatial"
        elif any(w in p for w in ["business summary", "executive summary", "executive insights", "platform status", "overview"]):
            intent = "executive_summary"
        else:
            if any(w in p for w in ["sla", "breach", "late"]):
                intent = "hub_sla_breach"
            elif any(w in p for w in ["cost", "price", "savings"]):
                intent = "cost_savings"
            elif any(w in p for w in ["route", "transit", "distance"]):
                intent = "route_recommendation" if (orig and dest) else "expensive_corridors"
            else:
                intent = "executive_summary"

        priority = "High Priority" if "high" in p else ("Low Priority" if "low" in p else "Medium Priority")
        qty_match = re.search(r"\b(\d+)\s*(?:units|pcs|items|parts|quantity|qty)?\b", p)
        quantity = int(qty_match.group(1)) if qty_match else 5

        entities = {
            "origin": orig,
            "destination": dest,
            "priority": priority,
            "quantity": quantity,
            "hub": orig or dest
        }

        return intent, entities

    @classmethod
    def route_query(cls, prompt: str) -> str:
        intent, _ = cls.route_and_extract(prompt)
        return intent
