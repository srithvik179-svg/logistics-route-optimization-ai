"""Cost Simulation Engine — Computes simulated logistics costs, transit times, and carbon metrics."""

import pandas as pd
from typing import Dict, Any, List

class CostSimulation:
    """Applies What-If parameter changes to logistics transactions and computes projected outcomes."""

    @classmethod
    def run_simulation(cls, df_raw: pd.DataFrame, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Runs What-If parameter transformations on transactions and returns summary analytics.
        
        Args:
            df_raw: Original baseline transactions DataFrame.
            scenarios: Dictionary of what-if parameters:
                - fuel_multiplier (float)
                - driver_multiplier (float)
                - maintenance_multiplier (float)
                - volume_multiplier (float)
                - transport_mode (str: 'Air Freight', 'Ground Transport', or 'Keep Current')
                - close_routes (List[str]: list of "Origin -> Destination" strings to disable)
                - emergency_disruption (bool)
                - sla_target_days (float)
                
        Returns:
            Dict containing simulated metrics:
                total_cost, transportation_cost, fuel_cost, avg_transit, success_rate,
                carbon, network_efficiency, etc.
        """
        if df_raw.empty:
            return cls._empty_metrics()

        df = df_raw.copy()

        # 1. Parse scenario parameters
        fuel_mult = float(scenarios.get("fuel_multiplier", 1.0))
        driver_mult = float(scenarios.get("driver_multiplier", 1.0))
        maint_mult = float(scenarios.get("maintenance_multiplier", 1.0))
        vol_mult = float(scenarios.get("volume_multiplier", 1.0))
        transport_mode = scenarios.get("transport_mode", "Keep Current")
        closed_routes = scenarios.get("close_routes", [])
        emergency_disruption = scenarios.get("emergency_disruption", False)
        sla_target = float(scenarios.get("sla_target_days", 3.0))

        # 2. Simulate Closed Routes (disable transactions on closed lanes)
        if closed_routes:
            # Format: "HUB-001 -> HUB-002"
            for cr in closed_routes:
                parts = cr.split("->")
                if len(parts) == 2:
                    orig = parts[0].strip()
                    dest = parts[1].strip()
                    # Reroute filter (drop matching lanes)
                    df = df[~((df["Origin_Hub"] == orig) & (df["Destination_Hub"] == dest))]

        # 3. Simulate Volume Changes (rescale dataset size)
        if vol_mult != 1.0 and not df.empty:
            if vol_mult > 1.0:
                # Replicate transactions
                extra_sample = df.sample(frac=vol_mult - 1.0, replace=True, random_state=42)
                df = pd.concat([df, extra_sample], ignore_index=True)
            else:
                # Subsample transactions
                df = df.sample(frac=vol_mult, random_state=42)

        if df.empty:
            return cls._empty_metrics()

        # 4. Calculate baseline transit days
        df["Transit_Days"] = (pd.to_datetime(df["Delivery_Date"]) - pd.to_datetime(df["Order_Date"])).dt.days.fillna(1.0)

        # 5. Apply Parameter Changes
        simulated_costs = []
        simulated_transits = []
        simulated_carbons = []

        for idx, r in df.iterrows():
            cost = float(r["Shipment_Cost"])
            dist = float(r.get("Route_Distance") or 0.0)
            transit = float(r["Transit_Days"])

            # Fuel factor, driver factor, maintenance factor distributions in standard shipping cost:
            # - Fuel Cost represents ~30% of total shipment cost.
            # - Driver Labor represents ~40% of total shipment cost.
            # - Maintenance/Tariff represents ~20% of total shipment cost.
            # - Unaffected Base cost represents ~10%.
            cost_scale = (0.30 * fuel_mult) + (0.40 * driver_mult) + (0.20 * maint_mult) + 0.10
            cost = cost * cost_scale

            # Transportation Mode override
            fuel_factor = 0.15 # Ground diesel gal/mile
            if transport_mode == "Air Freight":
                cost *= 2.2 # Air is much more expensive
                transit = max(1.0, transit * 0.4) # Fast delivery
                fuel_factor = 0.85 # Air cargo fuel usage
            elif transport_mode == "Ground Transport":
                cost *= 0.8 # Ground is cheaper
                transit = transit * 1.3 # Slower delivery
                fuel_factor = 0.15

            # Emergency disruption penalty
            if emergency_disruption:
                cost *= 1.35 # Spot rates spike
                transit += 1.5 # Congestion delays

            # Calculate Carbon
            fuel_usage = dist * fuel_factor
            carbon_co2 = fuel_usage * 10.15 # 10.15 kg CO2/gal

            simulated_costs.append(cost)
            simulated_transits.append(transit)
            simulated_carbons.append(carbon_co2)

        df["Simulated_Cost"] = simulated_costs
        df["Simulated_Transit"] = simulated_transits
        df["Simulated_Carbon"] = simulated_carbons

        # 6. Evaluate SLA success rate
        sla_success_count = sum(df["Simulated_Transit"] <= sla_target)
        success_rate = (sla_success_count / len(df)) * 100.0 if len(df) > 0 else 100.0

        # Calculate final metrics
        total_cost = sum(df["Simulated_Cost"])
        avg_transit = df["Simulated_Transit"].mean()
        total_carbon = sum(df["Simulated_Carbon"])

        # Cost Breakdown splits
        trans_cost = total_cost * 0.70
        fuel_cost = total_cost * 0.30

        # Network Efficiency Score (0-100)
        # Higher score means: high SLA compliance, lower avg transit, lower overall cost per shipment
        avg_shipment_cost = total_cost / len(df) if len(df) > 0 else 1.0
        sla_weight = success_rate * 0.5
        cost_weight = max(0.0, 50.0 - (avg_shipment_cost / 15.0)) # normalizes cost to ~50 points max
        efficiency_score = min(100.0, max(10.0, sla_weight + cost_weight))

        return {
            "total_cost": round(total_cost, 2),
            "transportation_cost": round(trans_cost, 2),
            "fuel_cost": round(fuel_cost, 2),
            "avg_transit_time": round(avg_transit, 2),
            "delivery_success_rate": round(success_rate, 1),
            "carbon_emissions": round(total_carbon, 1),
            "network_efficiency_score": round(efficiency_score, 1),
            "shipment_count": len(df)
        }

    @classmethod
    def _empty_metrics(cls) -> Dict[str, Any]:
        return {
            "total_cost": 0.0,
            "transportation_cost": 0.0,
            "fuel_cost": 0.0,
            "avg_transit_time": 0.0,
            "delivery_success_rate": 100.0,
            "carbon_emissions": 0.0,
            "network_efficiency_score": 100.0,
            "shipment_count": 0
        }
