import pandas as pd
from typing import Dict, Any, List
from backend.services.repository import repository
from backend.services.metric_calculator import MetricCalculator
from backend.services.summary_service import SummaryService
from backend.utils.logger import logger

class AnalyticsService:
    """Orchestrates descriptive analytics calculations and formats dashboard payloads."""

    @classmethod
    def get_dashboard_payload(cls) -> Dict[str, Any]:
        """Calculates KPIs, summarizes distributions, and compiles Plotly chart resources.
        
        Returns:
            Dict: High-level metrics for dashboard rendering.
        """
        logger.info("AnalyticsService: Calculating descriptive analytics.")
        
        # Safe checks for cached sheets
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        
        # Mapped keys check
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")
        
        # If any sheet is missing, fallback to raw or create empty DataFrame
        if df_tx is None:
            df_tx = pd.DataFrame(columns=["Transaction_ID", "Order_Date", "Delivery_Date", "Origin_Hub", 
                                          "Destination_Hub", "Part_Number", "Quantity", "SLA_Status", 
                                          "Shipment_Cost", "Route_Distance"])
        if df_hub is None:
            df_hub = pd.DataFrame(columns=["Hub_ID", "Hub_Name", "Latitude", "Longitude", "City", "Region"])
        if df_tpr is None:
            df_tpr = pd.DataFrame(columns=["TPR_ID", "TPR_Name", "Coverage_Region", "SLA_Compliance_Target", "Rating"])
        if df_parts is None:
            df_parts = pd.DataFrame(columns=["Part_Number", "Part_Name", "Category", "Weight_Kg", "Dimensions_Cm3"])

        # 1. Generate Platform Summary Details
        summary_info = SummaryService.generate_summary()

        # 2. Calculate KPI Cards
        total_shipments = MetricCalculator.calculate_total_shipments(df_tx)
        total_cost = MetricCalculator.calculate_total_cost(df_tx)
        avg_cost = MetricCalculator.calculate_avg_cost(df_tx)
        avg_transit = MetricCalculator.calculate_avg_transit_days(df_tx)
        avg_inventory = MetricCalculator.calculate_avg_inventory_level(df_tx)
        avg_hub_util = MetricCalculator.calculate_avg_hub_utilization(df_tx, df_hub)
        avg_tpr_util = MetricCalculator.calculate_avg_tpr_utilization(df_tx, df_tpr)

        kpis = {
            "total_shipments": {
                "title": "Total Shipments",
                "value": f"{total_shipments}",
                "description": "Total completed shipping transactions"
            },
            "total_cost": {
                "title": "Total Logistics Cost",
                "value": f"${total_cost:,.2f}",
                "description": "Aggregated freight shipping costs"
            },
            "avg_cost": {
                "title": "Average Logistics Cost",
                "value": f"${avg_cost:,.2f}",
                "description": "Mean cost incurred per transaction"
            },
            "avg_transit_days": {
                "title": "Average Transit Days",
                "value": f"{avg_transit:.1f} Days",
                "description": "Mean elapsed delivery duration"
            },
            "total_hubs": {
                "title": "Total Hubs",
                "value": f"{len(df_hub)}",
                "description": "Active logistics distribution hubs"
            },
            "total_tprs": {
                "title": "Total Repair Centers",
                "value": f"{len(df_tpr)}",
                "description": "Third-party servicing centers"
            },
            "total_parts": {
                "title": "Total Parts Catalog",
                "value": f"{len(df_parts)}",
                "description": "Unique managed inventory parts"
            },
            "avg_inventory_level": {
                "title": "Average Inventory Level",
                "value": f"{avg_inventory:,.0f} Units",
                "description": "Average stock quantities held at hubs"
            },
            "avg_hub_utilization": {
                "title": "Average Hub Utilization",
                "value": f"{avg_hub_util}%",
                "description": "Mean hub throughput load capacity"
            },
            "avg_rc_utilization": {
                "title": "Average Center Utilization",
                "value": f"{avg_tpr_util}%",
                "description": "Mean service bay workload load"
            }
        }

        # 3. Compile Distributions for Tables & Charts
        # A. Flow Type Classification
        flow_types = []
        if len(df_tx) > 0:
            for idx, r in df_tx.iterrows():
                dest = str(r["Destination_Hub"])
                if dest.upper().startswith("TPR"):
                    flow_types.append("Outbound to TPR")
                elif dest.upper().startswith("HUB"):
                    flow_types.append("Hub-to-Hub Transfer")
                else:
                    flow_types.append("Standard Delivery")
        df_tx_flow = df_tx.copy()
        df_tx_flow["Flow_Type"] = flow_types if len(flow_types) == len(df_tx) else "Standard Delivery"

        flow_summary = df_tx_flow.groupby("Flow_Type").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # B. Priority Categorization
        priorities = []
        if len(df_tx) > 0:
            for idx, r in df_tx.iterrows():
                dist = float(r.get("Route_Distance") or 0.0)
                cost = float(r.get("Shipment_Cost") or 0.0)
                if dist > 300.0 or cost > 300.0:
                    priorities.append("High Priority")
                elif dist > 100.0 or cost > 100.0:
                    priorities.append("Medium Priority")
                else:
                    priorities.append("Low Priority")
        df_tx_prio = df_tx.copy()
        df_tx_prio["Priority"] = priorities if len(priorities) == len(df_tx) else "Medium Priority"

        prio_summary = df_tx_prio.groupby("Priority").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # C. Logistics Partner Allocation
        partners = []
        tpr_names = list(df_tpr["TPR_Name"]) if len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        if len(df_tx) > 0:
            for i in range(len(df_tx)):
                partners.append(tpr_names[i % len(tpr_names)])
        df_tx_part = df_tx.copy()
        df_tx_part["Logistics_Partner"] = partners if len(partners) == len(df_tx) else tpr_names[0]

        partner_summary = df_tx_part.groupby("Logistics_Partner").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # D. Part Category (Join with Parts Master)
        df_joined = df_tx.merge(df_parts, on="Part_Number", how="left")
        df_joined["Category"] = df_joined["Category"].fillna("Uncategorized")
        part_cat_summary = df_joined.groupby("Category").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # E. SLA Status
        status_summary = df_tx.groupby("SLA_Status").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # F. Hub Types classification
        hub_types = []
        for idx, r in df_hub.iterrows():
            hub_id = str(r["Hub_ID"])
            if hub_id == "HUB-A":
                hub_types.append("Primary Gateway")
            elif hub_id in ["HUB-B", "HUB-C"]:
                hub_types.append("Regional Distribution Center")
            else:
                hub_types.append("Local Forwarding Hub")
        df_hub_typed = df_hub.copy()
        df_hub_typed["Hub_Type"] = hub_types if len(hub_types) == len(df_hub) else "Regional Distribution Center"
        
        hub_summary = df_hub_typed.groupby("Hub_Type").size().reset_index(name="count").to_dict(orient="records")

        # G. Repair Center Locations
        tpr_loc_summary = df_tpr.groupby("Coverage_Region").size().reset_index(name="count").to_dict(orient="records")

        # 4. Generate Plotly Data Series
        # Cost distribution time series (by Order_Date)
        cost_time_series = []
        if len(df_tx) > 0 and "Order_Date" in df_tx.columns:
            # Sort by date
            df_sorted = df_tx.copy()
            df_sorted["Order_Date_Str"] = pd.to_datetime(df_sorted["Order_Date"]).dt.strftime("%Y-%m-%d")
            df_time = df_sorted.groupby("Order_Date_Str").agg(
                cost=("Shipment_Cost", "sum"),
                shipments=("Transaction_ID", "count")
            ).reset_index()
            cost_time_series = df_time.to_dict(orient="records")

        logger.info("AnalyticsService: Metrics calculated and payload constructed.")

        return {
            "kpis": kpis,
            "summary_info": summary_info,
            "distributions": {
                "flow_types": flow_summary,
                "priorities": prio_summary,
                "partners": partner_summary,
                "part_categories": part_cat_summary,
                "sla_statuses": status_summary,
                "hub_types": hub_summary,
                "tpr_locations": tpr_loc_summary
            },
            "time_series": cost_time_series
        }
