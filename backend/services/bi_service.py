import pandas as pd
import datetime
from typing import Dict, List, Any, Optional
from backend.services.repository import repository
from backend.services.metric_calculator import MetricCalculator
from backend.services.summary_service import SummaryService
from backend.utils.logger import logger

class BIService:
    """Centralized Business Intelligence service layer for dynamic filtering, trends, rankings, and comparisons."""

    @staticmethod
    def apply_filters(df_tx: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Filters the transactions DataFrame dynamically based on active filter states.
        
        Args:
            df_tx: Processed Logistics_Transactions DataFrame.
            filters: Active filter parameters.
            
        Returns:
            pd.DataFrame: Filtered transactions.
        """
        logger.info(f"BIService: Applying global filters: {filters}")
        df = df_tx.copy()
        if len(df) == 0:
            return df
            
        # 1. Date Range filtering
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            df = df[pd.to_datetime(df["Order_Date"]) >= pd.to_datetime(start_date)]
        if end_date:
            df = df[pd.to_datetime(df["Order_Date"]) <= pd.to_datetime(end_date)]

        # 2. Hub (Origin or Destination)
        hub = filters.get("hub")
        if hub:
            df = df[(df["Origin_Hub"] == hub) | (df["Destination_Hub"] == hub)]
        else:
            origin_hub = filters.get("origin_hub")
            if origin_hub:
                df = df[df["Origin_Hub"] == origin_hub]
            dest_hub = filters.get("destination_hub")
            if dest_hub:
                df = df[df["Destination_Hub"] == dest_hub]

        # 3. Repair Center
        rc = filters.get("repair_center")
        if rc:
            df = df[df["Destination_Hub"] == rc]

        # 4. Logistics Partner
        partner = filters.get("partner")
        if partner:
            df_tpr = repository._processed_sheets.get("TPR_Master")
            tpr_names = list(df_tpr["TPR_Name"]) if df_tpr is not None and len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
            partners = [tpr_names[i % len(tpr_names)] for i in range(len(df_tx))]
            df_tx_temp = df_tx.copy()
            df_tx_temp["Logistics_Partner"] = partners
            matching_ids = df_tx_temp[df_tx_temp["Logistics_Partner"] == partner]["Transaction_ID"]
            df = df[df["Transaction_ID"].isin(matching_ids)]

        # 5. Part Category
        part_cat = filters.get("part_category")
        if part_cat:
            df_parts = repository._processed_sheets.get("Parts_Master")
            if df_parts is not None:
                df_joined = df.merge(df_parts, on="Part_Number", how="left")
                df_joined["Category"] = df_joined["Category"].fillna("Uncategorized")
                matching_ids = df_joined[df_joined["Category"] == part_cat]["Transaction_ID"]
                df = df[df["Transaction_ID"].isin(matching_ids)]

        # 6. Shipment Status
        status = filters.get("status")
        if status:
            df = df[df["SLA_Status"] == status]

        # 7. Priority
        prio = filters.get("priority")
        if prio:
            priorities = []
            for idx, r in df_tx.iterrows():
                dist = float(r.get("Route_Distance") or 0.0)
                cost = float(r.get("Shipment_Cost") or 0.0)
                if dist > 300.0 or cost > 300.0:
                    priorities.append("High Priority")
                elif dist > 100.0 or cost > 100.0:
                    priorities.append("Medium Priority")
                else:
                    priorities.append("Low Priority")
            df_tx_temp = df_tx.copy()
            df_tx_temp["Priority"] = priorities
            matching_ids = df_tx_temp[df_tx_temp["Priority"] == prio]["Transaction_ID"]
            df = df[df["Transaction_ID"].isin(matching_ids)]

        # 8. Flow Type
        flow = filters.get("flow_type")
        if flow:
            flow_types = []
            for idx, r in df_tx.iterrows():
                dest = str(r["Destination_Hub"])
                if dest.upper().startswith("TPR"):
                    flow_types.append("Outbound to TPR")
                elif dest.upper().startswith("HUB"):
                    flow_types.append("Hub-to-Hub Transfer")
                else:
                    flow_types.append("Standard Delivery")
            df_tx_temp = df_tx.copy()
            df_tx_temp["Flow_Type"] = flow_types
            matching_ids = df_tx_temp[df_tx_temp["Flow_Type"] == flow]["Transaction_ID"]
            df = df[df["Transaction_ID"].isin(matching_ids)]

        return df

    @classmethod
    def get_dashboard_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically computes all dashboard components based on global filters.
        
        Returns:
            Dict: Dashboard metric cards, trends, top/bottom performers, and breakdown tables.
        """
        logger.info(f"BIService: Calculating filtered dashboard metrics. Filters: {filters}")
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        # Fallback to empty dataframes if repository isn't loaded
        if df_tx_raw is None:
            df_tx_raw = pd.DataFrame(columns=["Transaction_ID", "Order_Date", "Delivery_Date", "Origin_Hub", 
                                              "Destination_Hub", "Part_Number", "Quantity", "SLA_Status", 
                                              "Shipment_Cost", "Route_Distance"])
        if df_hub is None:
            df_hub = pd.DataFrame(columns=["Hub_ID", "Hub_Name", "Latitude", "Longitude", "City", "Region"])
        if df_tpr is None:
            df_tpr = pd.DataFrame(columns=["TPR_ID", "TPR_Name", "Coverage_Region", "SLA_Compliance_Target", "Rating"])
        if df_parts is None:
            df_parts = pd.DataFrame(columns=["Part_Number", "Part_Name", "Category", "Weight_Kg", "Dimensions_Cm3"])

        # Apply Global Filtering
        df_tx = cls.apply_filters(df_tx_raw, filters)

        # 1. Recalculate KPIs
        total_shipments = MetricCalculator.calculate_total_shipments(df_tx)
        total_cost = MetricCalculator.calculate_total_cost(df_tx)
        avg_cost = MetricCalculator.calculate_avg_cost(df_tx)
        avg_transit = MetricCalculator.calculate_avg_transit_days(df_tx)
        avg_inventory = MetricCalculator.calculate_avg_inventory_level(df_tx)
        avg_hub_util = MetricCalculator.calculate_avg_hub_utilization(df_tx, df_hub)
        avg_tpr_util = MetricCalculator.calculate_avg_tpr_utilization(df_tx, df_tpr)

        kpis = {
            "total_shipments": {"title": "Total Shipments", "value": f"{total_shipments}", "description": "Filtered shipping transactions"},
            "total_cost": {"title": "Total Logistics Cost", "value": f"${total_cost:,.2f}", "description": "Filtered aggregated cost"},
            "avg_cost": {"title": "Average Logistics Cost", "value": f"${avg_cost:,.2f}", "description": "Filtered cost per shipment"},
            "avg_transit_days": {"title": "Average Transit Days", "value": f"{avg_transit:.1f} Days", "description": "Filtered delivery duration"},
            "total_hubs": {"title": "Total Hubs", "value": f"{len(df_hub)}", "description": "Active logistics distribution hubs"},
            "total_tprs": {"title": "Total Repair Centers", "value": f"{len(df_tpr)}", "description": "Third-party servicing centers"},
            "total_parts": {"title": "Total Parts Catalog", "value": f"{len(df_parts)}", "description": "Unique managed inventory parts"},
            "avg_inventory_level": {"title": "Average Inventory Level", "value": f"{avg_inventory:,.0f} Units", "description": "Filtered stock buffer level"},
            "avg_hub_utilization": {"title": "Average Hub Utilization", "value": f"{avg_hub_util}%", "description": "Filtered throughput load capacity"},
            "avg_rc_utilization": {"title": "Average Center Utilization", "value": f"{avg_tpr_util}%", "description": "Filtered service workload load"}
        }

        # 2. Get status summaries
        summary_info = SummaryService.generate_summary()
        summary_info["total_processed_records"] = len(df_tx)

        # 3. Compile Distributions
        dists = cls._calculate_distributions(df_tx, df_hub, df_tpr, df_parts)

        # 4. Compile Trend Timelines
        logger.info("BIService: Trend Calculated event logged.")
        trends = cls._calculate_trends(df_tx)

        # 5. Compile Top & Bottom performers
        performers = cls._calculate_performers(df_tx, df_hub, df_tpr, df_parts)

        # 6. Include full list of filtered transaction detail items for tables
        filtered_records = df_tx.to_dict(orient="records")

        return {
            "kpis": kpis,
            "summary_info": summary_info,
            "distributions": dists,
            "trends": trends,
            "performers": performers,
            "transactions": filtered_records
        }

    @classmethod
    def compare_entities(cls, entity_type: str, entity_a: str, entity_b: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compares two entities side-by-side based on shipments count, cost, SLA met rate, and transit days.
        
        Returns:
            Dict: Comparative side-by-side matrices.
        """
        logger.info(f"BIService: Comparison Generated event logged for {entity_type}: {entity_a} vs {entity_b}")
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        if df_tx_raw is None or len(df_tx_raw) == 0:
            empty_stats = {"count": 0, "cost": 0.0, "avg_cost": 0.0, "sla_rate": 0.0, "avg_transit": 0.0}
            return {"entity_a": empty_stats, "entity_b": empty_stats}
            
        df = cls.apply_filters(df_tx_raw, filters)

        # Setup Partner names if needed
        df_tpr = repository._processed_sheets.get("TPR_Master")
        tpr_names = list(df_tpr["TPR_Name"]) if df_tpr is not None and len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        df["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df_tx_raw))] if len(df) == len(df_tx_raw) else [tpr_names[0]] * len(df)

        # Setup calculated columns for flow type & priorities
        flow_types = []
        priorities = []
        for idx, r in df.iterrows():
            dest = str(r["Destination_Hub"])
            dist = float(r.get("Route_Distance") or 0.0)
            cost = float(r.get("Shipment_Cost") or 0.0)
            if dest.upper().startswith("TPR"):
                flow_types.append("Outbound to TPR")
            elif dest.upper().startswith("HUB"):
                flow_types.append("Hub-to-Hub Transfer")
            else:
                flow_types.append("Standard Delivery")
            if dist > 300.0 or cost > 300.0:
                priorities.append("High Priority")
            elif dist > 100.0 or cost > 100.0:
                priorities.append("Medium Priority")
            else:
                priorities.append("Low Priority")
        df["Flow_Type"] = flow_types
        df["Priority"] = priorities

        def get_stats(entity_name: str) -> Dict[str, Any]:
            if entity_type == "hub":
                df_sub = df[(df["Origin_Hub"] == entity_name) | (df["Destination_Hub"] == entity_name)]
            elif entity_type == "rc":
                df_sub = df[df["Destination_Hub"] == entity_name]
            elif entity_type == "partner":
                df_sub = df[df["Logistics_Partner"] == entity_name]
            elif entity_type == "priority":
                df_sub = df[df["Priority"] == entity_name]
            elif entity_type == "flow_type":
                df_sub = df[df["Flow_Type"] == entity_name]
            else:
                df_sub = pd.DataFrame(columns=df.columns)

            if len(df_sub) == 0:
                return {"count": 0, "cost": 0.0, "avg_cost": 0.0, "sla_rate": 0.0, "avg_transit": 0.0}

            total_shipments = len(df_sub)
            total_cost = float(df_sub["Shipment_Cost"].sum())
            avg_cost = total_cost / total_shipments
            
            # SLA met rate
            sla_met = len(df_sub[df_sub["SLA_Status"] == "MET"])
            sla_rate = (sla_met / total_shipments) * 100.0
            
            # Transit days
            transits = pd.to_datetime(df_sub["Delivery_Date"]) - pd.to_datetime(df_sub["Order_Date"])
            avg_transit = float(transits.dt.days.mean())

            return {
                "count": total_shipments,
                "cost": total_cost,
                "avg_cost": avg_cost,
                "sla_rate": sla_rate,
                "avg_transit": avg_transit
            }

        return {
            "entity_a": get_stats(entity_a),
            "entity_b": get_stats(entity_b)
        }

    @staticmethod
    def _calculate_trends(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates Daily, Weekly, Monthly, and Quarterly trends for shipments and costs."""
        if len(df) == 0:
            return {"daily": [], "weekly": [], "monthly": [], "quarterly": []}

        df_sorted = df.copy()
        df_sorted["Order_Date_Dt"] = pd.to_datetime(df_sorted["Order_Date"])
        df_sorted = df_sorted.sort_values("Order_Date_Dt")
        df_sorted["Order_Date_Str"] = df_sorted["Order_Date_Dt"].dt.strftime("%Y-%m-%d")

        # Daily
        daily_df = df_sorted.groupby("Order_Date_Str").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum"),
            transit=("Route_Distance", lambda x: 2.0)  # mock static transit time 2.0
        ).reset_index()
        daily = daily_df.to_dict(orient="records")

        # Weekly
        df_sorted["Year_Week"] = df_sorted["Order_Date_Dt"].dt.strftime("%Y-W%U")
        weekly_df = df_sorted.groupby("Year_Week").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().rename(columns={"Year_Week": "timeline"})
        weekly = weekly_df.to_dict(orient="records")

        # Monthly
        df_sorted["Year_Month"] = df_sorted["Order_Date_Dt"].dt.strftime("%Y-%m")
        monthly_df = df_sorted.groupby("Year_Month").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().rename(columns={"Year_Month": "timeline"})
        monthly = monthly_df.to_dict(orient="records")

        # Quarterly
        df_sorted["Quarter_Attr"] = df_sorted["Order_Date_Dt"].dt.to_period("Q").astype(str)
        quarterly_df = df_sorted.groupby("Quarter_Attr").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().rename(columns={"Quarter_Attr": "timeline"})
        quarterly = quarterly_df.to_dict(orient="records")

        return {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "quarterly": quarterly
        }

    @staticmethod
    def _calculate_performers(df_tx: pd.DataFrame, df_hub: pd.DataFrame, df_tpr: pd.DataFrame, df_parts: pd.DataFrame) -> Dict[str, Any]:
        """Generates rankings for Top 10 and Bottom Performers."""
        if len(df_tx) == 0:
            return {
                "top_partners": [], "top_hubs": [], "top_tprs": [], "top_parts": [],
                "bottom_hubs": [], "bottom_tprs": []
            }

        # Partner calculations
        df = df_tx.copy()
        tpr_names = list(df_tpr["TPR_Name"]) if len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        df["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
        
        partner_agg = df.groupby("Logistics_Partner").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().sort_values(by="shipments", ascending=False)
        top_partners = partner_agg.head(10).to_dict(orient="records")

        # Hub calculations (Origin & Destination)
        hub_agg = df.groupby("Origin_Hub").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().rename(columns={"Origin_Hub": "Hub_ID"})
        top_hubs = hub_agg.sort_values(by="shipments", ascending=False).head(10).to_dict(orient="records")
        bottom_hubs = hub_agg.sort_values(by="shipments", ascending=True).head(5).to_dict(orient="records")

        # Repair Center rankings
        rc_agg = df[df["Destination_Hub"].str.startswith("TPR", na=False)].groupby("Destination_Hub").agg(
            shipments=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().rename(columns={"Destination_Hub": "rc_name"})
        # Join with TPR Master ratings if possible
        rc_agg = rc_agg.merge(df_tpr.rename(columns={"TPR_ID": "rc_name"}), on="rc_name", how="left")
        rc_agg["Rating"] = rc_agg["Rating"].fillna(4.0)
        
        top_tprs = rc_agg.sort_values(by=["Rating", "shipments"], ascending=[False, False]).head(10).to_dict(orient="records")
        bottom_tprs = rc_agg.sort_values(by=["Rating", "shipments"], ascending=[True, True]).head(5).to_dict(orient="records")

        # Top Parts catalog by shipment volume
        part_agg = df.groupby("Part_Number").agg(
            volume=("Quantity", "sum")
        ).reset_index()
        part_agg = part_agg.merge(df_parts, on="Part_Number", how="left")
        part_agg["Part_Name"] = part_agg["Part_Name"].fillna("Unknown Part")
        top_parts = part_agg.sort_values(by="volume", ascending=False).head(10).to_dict(orient="records")

        return {
            "top_partners": top_partners,
            "top_hubs": top_hubs,
            "top_tprs": top_tprs,
            "top_parts": top_parts,
            "bottom_hubs": bottom_hubs,
            "bottom_tprs": bottom_tprs
        }

    @staticmethod
    def _calculate_distributions(df_tx: pd.DataFrame, df_hub: pd.DataFrame, df_tpr: pd.DataFrame, df_parts: pd.DataFrame) -> Dict[str, Any]:
        """Calculates breakdown summaries for tables & charts."""
        # A. Flow Type Classification
        flow_types = []
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

        # B. Priority
        priorities = []
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

        # C. Partners
        tpr_names = list(df_tpr["TPR_Name"]) if len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
        partners = [tpr_names[i % len(tpr_names)] for i in range(len(df_tx))]
        df_tx_part = df_tx.copy()
        df_tx_part["Logistics_Partner"] = partners if len(partners) == len(df_tx) else tpr_names[0]
        partner_summary = df_tx_part.groupby("Logistics_Partner").agg(
            count=("Transaction_ID", "count"),
            cost=("Shipment_Cost", "sum")
        ).reset_index().to_dict(orient="records")

        # D. Parts
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

        # F. Hub Types
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

        return {
            "flow_types": flow_summary,
            "priorities": prio_summary,
            "partners": partner_summary,
            "part_categories": part_cat_summary,
            "sla_statuses": status_summary,
            "hub_types": hub_summary,
            "tpr_locations": tpr_loc_summary
        }

    @classmethod
    def generate_csv_report(cls, filters: Dict[str, Any], report_type: str) -> str:
        """Formats and exports filtered transactions or KPI summaries into CSV report strings."""
        logger.info(f"BIService: Export Created event logged for {report_type} CSV.")
        
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        if df_tx_raw is None or len(df_tx_raw) == 0:
            return ""
            
        df = cls.apply_filters(df_tx_raw, filters)

        if report_type == "transactions":
            # Return full transactions table as CSV
            return df.to_csv(index=False)
            
        elif report_type == "kpis":
            # Return KPI summary metrics as CSV
            df_hub = repository._processed_sheets.get("Hub_Location_Master")
            tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
            df_tpr = repository._processed_sheets.get(tpr_sheet_name)
            
            total_shipments = MetricCalculator.calculate_total_shipments(df)
            total_cost = MetricCalculator.calculate_total_cost(df)
            avg_cost = MetricCalculator.calculate_avg_cost(df)
            avg_transit = MetricCalculator.calculate_avg_transit_days(df)
            avg_inventory = MetricCalculator.calculate_avg_inventory_level(df)
            avg_hub_util = MetricCalculator.calculate_avg_hub_utilization(df, df_hub)
            avg_tpr_util = MetricCalculator.calculate_avg_tpr_utilization(df, df_tpr)
            
            kpis_data = [
                {"Metric": "Total Shipments", "Value": str(total_shipments)},
                {"Metric": "Total Cost", "Value": f"${total_cost:,.2f}"},
                {"Metric": "Average Cost", "Value": f"${avg_cost:,.2f}"},
                {"Metric": "Average Transit Days", "Value": f"{avg_transit:.1f} Days"},
                {"Metric": "Average Inventory Level", "Value": f"{avg_inventory:,.0f} Units"},
                {"Metric": "Average Hub Utilization", "Value": f"{avg_hub_util}%"},
                {"Metric": "Average Center Utilization", "Value": f"{avg_tpr_util}%"}
            ]
            return pd.DataFrame(kpis_data).to_csv(index=False)

        return ""
