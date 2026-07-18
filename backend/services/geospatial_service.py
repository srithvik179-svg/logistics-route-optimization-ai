import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.services.repository import repository
from backend.utils.logger import logger
from backend.services.metric_calculator import MetricCalculator

class GeospatialService:
    """Service to compute geospatial locations, flows, and summary metrics for mapping."""

    # Fallback coordinate registry for known assets
    COORDINATES_FALLBACK = {
        "HUB-A": {"lat": 30.2672, "lon": -97.7431, "city": "Austin", "state": "TX", "type": "Distribution Hub", "capacity": 5000},
        "HUB-B": {"lat": 29.7604, "lon": -95.3698, "city": "Houston", "state": "TX", "type": "Regional Hub", "capacity": 4000},
        "HUB-C": {"lat": 32.7767, "lon": -96.7970, "city": "Dallas", "state": "TX", "type": "Distribution Hub", "capacity": 6000},
        "HUB-D": {"lat": 29.4241, "lon": -98.4936, "city": "San Antonio", "state": "TX", "type": "Regional Hub", "capacity": 3000},
        "HUB-E": {"lat": 31.7619, "lon": -106.4850, "city": "El Paso", "state": "TX", "type": "Distribution Hub", "capacity": 3500},
        "TPR-001": {"lat": 30.4000, "lon": -97.6000, "city": "Austin", "state": "TX", "type": "Repair Center", "capacity": 1500},
        "TPR-002": {"lat": 32.9000, "lon": -96.9000, "city": "Dallas", "state": "TX", "type": "Repair Center", "capacity": 2000},
        "TPR-003": {"lat": 31.8000, "lon": -106.3000, "city": "El Paso", "state": "TX", "type": "Repair Center", "capacity": 1200}
    }

    # Map TPR Names to IDs for joining
    TPR_NAME_TO_ID = {
        "Swift LogiCo": "TPR-001",
        "Swift Logico": "TPR-001",
        "Apex Freight": "TPR-002",
        "LoneStar Delivery": "TPR-003",
        "Lonestar Delivery": "TPR-003"
    }

    @classmethod
    def get_network_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates and filters hubs, repair centers, active flows, and map KPIs.
        
        Args:
            filters: Global filters dict.
            
        Returns:
            Dict containing hubs, repair_centers, flows, and summary.
        """
        logger.info(f"GeospatialService: Generating network map data. Filters: {filters}")
        
        # Load sheets from repository
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        # Set up safe fallbacks
        if df_tx_raw is None:
            df_tx_raw = pd.DataFrame()
        if df_hub is None:
            df_hub = pd.DataFrame()
        if df_tpr is None:
            df_tpr = pd.DataFrame()
        if df_parts is None:
            df_parts = pd.DataFrame()

        # Enrich dynamic partners, priorities, and flow types just like BI service
        df = df_tx_raw.copy()
        if len(df) > 0:
            tpr_names = list(df_tpr["TPR_Name"]) if len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
            df["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
            
            # Map partner names to TPR IDs
            df["TPR_ID"] = df["Logistics_Partner"].map(cls.TPR_NAME_TO_ID).fillna("TPR-001")

            priorities = []
            flow_types = []
            for idx, r in df.iterrows():
                dest = str(r["Destination_Hub"])
                dist = float(r.get("Route_Distance") or 0.0)
                cost = float(r.get("Shipment_Cost") or 0.0)
                
                # Check for explicit TPR destinations in database
                if dest.upper().startswith("TPR"):
                    flow_types.append("Outbound to TPR")
                elif dest.upper().startswith("HUB"):
                    flow_types.append("Hub-to-Hub Transfer")
                else:
                    # If partner maps to TPR, classify as outbound to TPR
                    flow_types.append("Outbound to TPR")
                
                if dist > 300.0 or cost > 300.0:
                    priorities.append("High Priority")
                elif dist > 100.0 or cost > 100.0:
                    priorities.append("Medium Priority")
                else:
                    priorities.append("Low Priority")
            df["Priority"] = priorities
            df["Flow_Type"] = flow_types

        # Apply Filters to transactions
        df_filtered = cls._apply_geospatial_filters(df, df_parts, filters)

        # 1. Resolve Hub Locations
        hubs_list = []
        for idx, r in df_hub.iterrows():
            hub_id = str(r["Hub_ID"])
            # Resolve coordinates from file columns
            lat = r.get("Latitude")
            lon = r.get("Longitude")
            
            # Warn if missing and use fallback registry
            if pd.isna(lat) or pd.isna(lon):
                logger.warning(f"Geospatial Warning: Missing coordinates for Hub '{hub_id}'. Using fallback registry.")
                fb = cls.COORDINATES_FALLBACK.get(hub_id, {"lat": 30.0, "lon": -100.0})
                lat = fb["lat"]
                lon = fb["lon"]
            
            # Inventory summary: average inventory load for this hub
            hub_txs = df_filtered[(df_filtered["Origin_Hub"] == hub_id) | (df_filtered["Destination_Hub"] == hub_id)]
            total_qty = int(hub_txs["Quantity"].sum()) if len(hub_txs) > 0 else 0
            
            # Hub utilization
            fb_hub = cls.COORDINATES_FALLBACK.get(hub_id, {})
            capacity = fb_hub.get("capacity", 5000)
            util = round((total_qty / capacity) * 100.0, 1) if capacity > 0 else 0.0
            
            hubs_list.append({
                "id": hub_id,
                "name": str(r["Hub_Name"]),
                "type": fb_hub.get("type", "Distribution Hub"),
                "lat": float(lat),
                "lon": float(lon),
                "city": str(r.get("City", "Unknown")),
                "state": str(r.get("Region", "TX")),
                "capacity": capacity,
                "utilization": min(util, 100.0),
                "inventory_summary": f"{total_qty} units handled"
            })
        logger.info(f"GeospatialService: Markers Generated - {len(hubs_list)} Hubs mapped.")

        # 2. Resolve Repair Center Locations
        rcs_list = []
        for idx, r in df_tpr.iterrows():
            rc_id = str(r["TPR_ID"])
            rc_name = str(r["TPR_Name"])
            
            # Resolving coordinates
            lat = r.get("Latitude")
            lon = r.get("Longitude")
            
            if pd.isna(lat) or pd.isna(lon):
                # Use registry fallback
                fb = cls.COORDINATES_FALLBACK.get(rc_id, {"lat": 31.0, "lon": -99.0})
                lat = fb["lat"]
                lon = fb["lon"]
            
            # Calculate utilization: based on matching transactions
            rc_txs = df_filtered[df_filtered["TPR_ID"] == rc_id]
            rc_qty = int(rc_txs["Quantity"].sum()) if len(rc_txs) > 0 else 0
            
            capacity = 2000 # default
            util = round((rc_qty / capacity) * 100.0, 1)
            
            # Get supported part categories handled by this TPR
            rc_parts = list(rc_txs["Part_Number"].unique()) if len(rc_txs) > 0 else ["PART-001", "PART-002", "PART-003"]
            
            rcs_list.append({
                "id": rc_id,
                "name": rc_name,
                "type": "Repair Center",
                "lat": float(lat),
                "lon": float(lon),
                "city": "Dallas" if rc_id == "TPR-002" else ("El Paso" if rc_id == "TPR-003" else "Austin"),
                "state": "TX",
                "capacity": capacity,
                "utilization": min(util, 100.0),
                "supported_parts": rc_parts[:3]
            })
        logger.info(f"GeospatialService: Markers Generated - {len(rcs_list)} Repair Centers mapped.")

        # 3. Generate Flow Lines
        flows_list = []
        path_groups = {}
        
        # Group filtered transactions to compile aggregated path statistics
        for idx, r in df_filtered.iterrows():
            orig = str(r["Origin_Hub"])
            dest = str(r["Destination_Hub"])
            tpr_id = str(r["TPR_ID"])
            flow_type = str(r["Flow_Type"])
            
            # Determine path segment endpoints
            if flow_type == "Outbound to TPR":
                # Draw Hub -> Repair Center segment
                path_key = (orig, tpr_id, "Outbound to TPR")
            else:
                # Draw Hub -> Hub segment
                path_key = (orig, dest, "Hub-to-Hub Transfer")
                
            cost = float(r["Shipment_Cost"])
            transit_days = float((pd.to_datetime(r["Delivery_Date"]) - pd.to_datetime(r["Order_Date"])).days)
            
            if path_key not in path_groups:
                path_groups[path_key] = {"costs": [], "transits": [], "shipment_count": 0}
                
            path_groups[path_key]["costs"].append(cost)
            path_groups[path_key]["transits"].append(transit_days)
            path_groups[path_key]["shipment_count"] += 1

        # Build flow dictionary objects
        for path_key, stats in path_groups.items():
            start_node, end_node, flow_type = path_key
            
            # Resolve coordinates for start and end nodes
            fb_start = cls.COORDINATES_FALLBACK.get(start_node, {"lat": 30.0, "lon": -100.0})
            fb_end = cls.COORDINATES_FALLBACK.get(end_node, {"lat": 30.0, "lon": -100.0})
            
            # Check if start/end nodes exist in active lists to override coordinates if needed
            for h in hubs_list:
                if h["id"] == start_node:
                    fb_start = h
                if h["id"] == end_node:
                    fb_end = h
            for rc in rcs_list:
                if rc["id"] == start_node:
                    fb_start = rc
                if rc["id"] == end_node:
                    fb_end = rc
                    
            flows_list.append({
                "origin_id": start_node,
                "destination_id": end_node,
                "origin_lat": fb_start["lat"],
                "origin_lon": fb_start["lon"],
                "dest_lat": fb_end["lat"],
                "dest_lon": fb_end["lon"],
                "shipment_count": stats["shipment_count"],
                "flow_type": flow_type,
                "avg_transit_time": round(sum(stats["transits"]) / len(stats["transits"]), 1),
                "avg_cost": round(sum(stats["costs"]) / len(stats["costs"]), 2)
            })

        logger.info(f"GeospatialService: Flows Rendered - {len(flows_list)} route paths compiled.")

        # 4. Generate Summary Metrics Panel
        visible_shipments = len(df_filtered)
        avg_transit = 0.0
        avg_cost = 0.0
        if visible_shipments > 0:
            avg_cost = float(df_filtered["Shipment_Cost"].mean())
            transits = pd.to_datetime(df_filtered["Delivery_Date"]) - pd.to_datetime(df_filtered["Order_Date"])
            avg_transit = float(transits.dt.days.mean())

        # Determine count of active hubs & repair centers matching filter
        active_hubs = set(df_filtered["Origin_Hub"].unique()).union(set(df_filtered["Destination_Hub"].unique()))
        active_hubs = {h for h in active_hubs if h in cls.COORDINATES_FALLBACK and not h.startswith("TPR")}
        active_rcs = set(df_filtered["TPR_ID"].unique())
        
        summary = {
            "total_hubs": len(active_hubs) if len(active_hubs) > 0 else len(df_hub),
            "total_rcs": len(active_rcs) if len(active_rcs) > 0 else len(df_tpr),
            "visible_shipments": visible_shipments,
            "visible_connections": len(flows_list),
            "avg_transit_time": round(avg_transit, 1),
            "avg_cost": round(avg_cost, 2)
        }

        return {
            "hubs": hubs_list,
            "repair_centers": rcs_list,
            "flows": flows_list,
            "summary": summary
        }

    @classmethod
    def _apply_geospatial_filters(cls, df: pd.DataFrame, df_parts: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Filters transactions based on provided filters."""
        if len(df) == 0:
            return df
            
        df_filtered = df.copy()

        # Date Range
        start_date = filters.get("start_date")
        if start_date:
            df_filtered = df_filtered[pd.to_datetime(df_filtered["Order_Date"]) >= pd.to_datetime(start_date)]
            
        end_date = filters.get("end_date")
        if end_date:
            df_filtered = df_filtered[pd.to_datetime(df_filtered["Order_Date"]) <= pd.to_datetime(end_date)]

        # Hub (Origin or Destination)
        hub = filters.get("hub")
        if hub:
            df_filtered = df_filtered[(df_filtered["Origin_Hub"] == hub) | (df_filtered["Destination_Hub"] == hub)]

        # Repair Center
        rc = filters.get("repair_center")
        if rc:
            df_filtered = df_filtered[df_filtered["TPR_ID"] == rc]

        # Part Category
        category = filters.get("part_category")
        if category and len(df_parts) > 0:
            matching_parts = df_parts[df_parts["Category"] == category]["Part_Number"]
            df_filtered = df_filtered[df_filtered["Part_Number"].isin(matching_parts)]

        # Logistics Partner
        partner = filters.get("partner")
        if partner:
            df_filtered = df_filtered[df_filtered["Logistics_Partner"] == partner]

        # Priority
        priority = filters.get("priority")
        if priority:
            df_filtered = df_filtered[df_filtered["Priority"] == priority]

        # Shipment Status
        status = filters.get("status")
        if status:
            df_filtered = df_filtered[df_filtered["SLA_Status"] == status]

        return df_filtered
