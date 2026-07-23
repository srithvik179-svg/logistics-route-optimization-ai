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
        # Real Hubs
        "HUB-BLR": {"lat": 12.9716, "lon": 77.5946, "city": "Bangalore", "state": "KA", "type": "Primary Hub", "capacity": 5000},
        "HUB-DEL": {"lat": 28.7041, "lon": 77.1025, "city": "Delhi", "state": "DL", "type": "Distribution Hub", "capacity": 6000},
        "HUB-MUM": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "state": "MH", "type": "Distribution Hub", "capacity": 7000},
        "HUB-CHE": {"lat": 13.0827, "lon": 80.2707, "city": "Chennai", "state": "TN", "type": "Regional Hub", "capacity": 4000},
        "HUB-HYD": {"lat": 17.3850, "lon": 78.4867, "city": "Hyderabad", "state": "TG", "type": "Regional Hub", "capacity": 4500},
        "HUB-PUN": {"lat": 18.5204, "lon": 73.8567, "city": "Pune", "state": "MH", "type": "Regional Hub", "capacity": 3500},
        "HUB-KOL": {"lat": 22.5726, "lon": 88.3639, "city": "Kolkata", "state": "WB", "type": "Distribution Hub", "capacity": 5000},
        "HUB-AHM": {"lat": 23.0225, "lon": 72.5714, "city": "Ahmedabad", "state": "GJ", "type": "Regional Hub", "capacity": 4000},
        "HUB-SIN": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore", "state": "SG", "type": "Gateway Hub", "capacity": 10000},
        "HUB-KUL": {"lat": 3.1390, "lon": 101.6869, "city": "Kuala Lumpur", "state": "MY", "type": "Gateway Hub", "capacity": 8000},
        "HUB-DXB": {"lat": 25.2048, "lon": 55.2708, "city": "Dubai", "state": "AE", "type": "Gateway Hub", "capacity": 9000},
        "HUB-AMS": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "state": "NL", "type": "Gateway Hub", "capacity": 12000},

        # Real TPRs
        "TPR-BLR-01": {"lat": 12.9352, "lon": 77.6245, "city": "Bangalore", "state": "KA", "type": "Repair Center", "capacity": 2000},
        "TPR-BLR-02": {"lat": 12.9791, "lon": 77.5913, "city": "Bangalore", "state": "KA", "type": "Repair Center", "capacity": 2000},
        "TPR-DEL-01": {"lat": 28.6448, "lon": 77.2167, "city": "Delhi", "state": "DL", "type": "Repair Center", "capacity": 2000},
        "TPR-MUM-01": {"lat": 19.1136, "lon": 72.8697, "city": "Mumbai", "state": "MH", "type": "Repair Center", "capacity": 2000},
        "TPR-CHE-01": {"lat": 13.0569, "lon": 80.2425, "city": "Chennai", "state": "TN", "type": "Repair Center", "capacity": 2000},
        "TPR-HYD-01": {"lat": 17.4126, "lon": 78.4071, "city": "Hyderabad", "state": "TG", "type": "Repair Center", "capacity": 2000},
        "TPR-SIN-01": {"lat": 1.2966, "lon": 103.8520, "city": "Singapore", "state": "SG", "type": "Repair Center", "capacity": 2000},
        "TPR-KUL-01": {"lat": 3.1569, "lon": 101.7123, "city": "Kuala Lumpur", "state": "MY", "type": "Repair Center", "capacity": 2000},

        # Customer Destination Cities
        "Nagpur": {"lat": 21.1458, "lon": 79.0882, "city": "Nagpur", "state": "MH", "type": "Customer Destination", "capacity": 0},
        "Lucknow": {"lat": 26.8467, "lon": 80.9462, "city": "Lucknow", "state": "UP", "type": "Customer Destination", "capacity": 0},
        "Surat": {"lat": 21.1702, "lon": 72.8311, "city": "Surat", "state": "GJ", "type": "Customer Destination", "capacity": 0},
        "Jaipur": {"lat": 26.9124, "lon": 75.7873, "city": "Jaipur", "state": "RJ", "type": "Customer Destination", "capacity": 0},
        
        # Legacy hubs / fallbacks
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
        "TechRepair Bangalore": "TPR-BLR-01",
        "QuickFix Solutions Bangalore": "TPR-BLR-02",
        "NorthIndia Repairs Delhi": "TPR-DEL-01",
        "WestCoast Service Mumbai": "TPR-MUM-01",
        "SouthTech Repairs Chennai": "TPR-CHE-01",
        "Deccan Repair Hub Hyderabad": "TPR-HYD-01",
        "AsiaPac ServiceCenter Singapore": "TPR-SIN-01",
        "MalaysiaTech Repairs KL": "TPR-KUL-01",
        # Legacy
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
            
            # Map partner names to TPR IDs dynamically
            partner_to_tpr = {}
            if len(df_tpr) > 0 and "TPR_Name" in df_tpr.columns and "TPR_ID" in df_tpr.columns:
                partner_to_tpr = dict(zip(df_tpr["TPR_Name"], df_tpr["TPR_ID"]))
            
            # Add reverse mapping from COORDINATES_FALLBACK as fallback
            for k, v in cls.COORDINATES_FALLBACK.items():
                if k.startswith("TPR-") and v.get("city"):
                    partner_to_tpr[v.get("city") + " Repair Center"] = k

            default_tpr_id = list(partner_to_tpr.values())[0] if partner_to_tpr else "TPR-001"
            df["TPR_ID"] = df["Logistics_Partner"].map(partner_to_tpr).fillna(default_tpr_id)

            priorities = []
            flow_types = []
            for idx, r in df.iterrows():
                dest = str(r["Destination_Hub"])
                dist = float(r.get("Route_Distance") or 0.0)
                cost = float(r.get("Shipment_Cost") or 0.0)
                
                # Check for explicit TPR destinations in database
                if dest.upper().startswith("TPR") or dest in partner_to_tpr.values():
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
            capacity = float(r.get("Inventory_Capacity") or fb_hub.get("capacity", 5000.0))
            util = round((total_qty / capacity) * 100.0, 1) if capacity > 0 else 0.0
            
            hubs_list.append({
                "id": hub_id,
                "name": str(r["Hub_Name"]),
                "type": r.get("Hub_Type") or fb_hub.get("type", "Distribution Hub"),
                "lat": float(lat),
                "lon": float(lon),
                "city": str(r.get("City", "Unknown")),
                "state": str(r.get("Region", r.get("Primary_Region", "TX"))),
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
            
            fb_rc = cls.COORDINATES_FALLBACK.get(rc_id, {})
            capacity = float(r.get("Repair_Capacity_Per_Day") or fb_rc.get("capacity", 2000.0))
            util = round((rc_qty / capacity) * 100.0, 1) if capacity > 0 else 0.0
            
            # Get supported part categories handled by this TPR
            rc_parts = list(rc_txs["Part_Number"].unique()) if len(rc_txs) > 0 else ["PART-001", "PART-002", "PART-003"]
            
            rcs_list.append({
                "id": rc_id,
                "name": rc_name,
                "type": "Repair Center",
                "lat": float(lat),
                "lon": float(lon),
                "city": str(r.get("City", "Unknown")),
                "state": str(r.get("Coverage_Region", "TX")),
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
        if "Origin_Hub" in df_filtered.columns and "Destination_Hub" in df_filtered.columns and len(df_filtered) > 0:
            active_hubs = set(df_filtered["Origin_Hub"].unique()).union(set(df_filtered["Destination_Hub"].unique()))
            active_hubs = {h for h in active_hubs if h in cls.COORDINATES_FALLBACK and not h.startswith("TPR")}
        else:
            active_hubs = set()
            
        if "TPR_ID" in df_filtered.columns and len(df_filtered) > 0:
            active_rcs = set(df_filtered["TPR_ID"].unique())
        else:
            active_rcs = set()
        
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
        import time
        start_time = time.time()
        
        def is_active_filter(val):
            if val is None:
                return False
            if isinstance(val, str):
                s = val.strip().lower()
                if s in ["", "all", "all hubs", "all regions", "all types", "all modes", "all priorities", "all statuses", "all partners", "all carriers"]:
                    return False
            return True

        # Check if there are no active filters
        active_filters = {k: v for k, v in (filters or {}).items() if is_active_filter(v)}
        logger.info(f"[GeospatialFilter] Received raw filters: {filters}")
        logger.info(f"[GeospatialFilter] Active filters to apply: {active_filters}")

        if not active_filters or len(df) == 0:
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[GeospatialFilter] Query executed: NO_FILTERS_APPLIED. Matching rows: {len(df)}. Execution time: {elapsed:.2f} ms")
            return df.copy()

        df_filtered = df.copy()
        query_ops = []

        # 1. Date Range filtering (Dispatch Date -> Dispatch_Date, Delivery Date -> Actual_Delivery_Date)
        start_date = active_filters.get("start_date")
        end_date = active_filters.get("end_date")
        if start_date:
            df_filtered = df_filtered[pd.to_datetime(df_filtered["Dispatch_Date"], errors='coerce') >= pd.to_datetime(start_date)]
            query_ops.append(f"pd.to_datetime(Dispatch_Date) >= {start_date}")
        if end_date:
            df_filtered = df_filtered[pd.to_datetime(df_filtered["Actual_Delivery_Date"], errors='coerce') <= pd.to_datetime(end_date)]
            query_ops.append(f"pd.to_datetime(Actual_Delivery_Date) <= {end_date}")

        # 2. Hub (Origin or Destination) -> maps to Hub_Location_Master.Hub_Name or Hub_ID
        hub = active_filters.get("hub")
        if hub:
            df_hub = repository._processed_sheets.get("Hub_Location_Master")
            hub_ids = [hub]
            if df_hub is not None:
                # Resolve using Hub_Name as primary or Hub_ID as secondary
                matching_hubs = df_hub[
                    (df_hub["Hub_ID"].astype(str).str.lower() == hub.lower()) |
                    (df_hub["Hub_Name"].astype(str).str.lower() == hub.lower())
                ]
                if not matching_hubs.empty:
                    hub_ids = list(matching_hubs["Hub_ID"].unique())
            df_filtered = df_filtered[df_filtered["Origin_Hub"].isin(hub_ids)]
            query_ops.append(f"Origin_Hub in {hub_ids}")
        else:
            origin_hub = active_filters.get("origin_hub")
            if origin_hub:
                df_filtered = df_filtered[df_filtered["Origin_Hub"] == origin_hub]
                query_ops.append(f"Origin_Hub == {origin_hub}")
            dest_loc = active_filters.get("destination_hub")
            if dest_loc:
                df_filtered = df_filtered[df_filtered["Destination_Location"].astype(str).str.lower().str.contains(dest_loc.lower())]
                query_ops.append(f"Destination_Location contains {dest_loc}")

        # 3. Repair Center
        rc = active_filters.get("repair_center")
        if rc:
            rc_clean = str(rc).strip().upper()
            code_prefix = rc_clean.split()[0] if rc_clean else ""
            df_filtered = df_filtered[
                (df_filtered["TPR_ID"].astype(str).str.upper().str.contains(code_prefix)) |
                (df_filtered["Destination_Hub"].astype(str).str.upper().str.contains(code_prefix)) |
                (df_filtered.get("Logistics_Partner", pd.Series()).astype(str).str.upper().str.contains(code_prefix))
            ]
            query_ops.append(f"Repair Center fuzzy == {rc}")

        # 3b. Route Filter (e.g. "HUB-BLR → TPR-BLR-01")
        route_flt = active_filters.get("route")
        if route_flt and "→" in str(route_flt):
            parts = [p.strip().upper() for p in str(route_flt).split("→")]
            if len(parts) == 2:
                orig_p = parts[0].split()[0]
                dest_p = parts[1].split()[0]
                df_filtered = df_filtered[
                    (df_filtered["Origin_Hub"].astype(str).str.upper().str.contains(orig_p)) &
                    (df_filtered["Destination_Hub"].astype(str).str.upper().str.contains(dest_p))
                ]
                query_ops.append(f"Route corridor == {route_flt}")

        # 4. Part Category
        category = active_filters.get("part_category")
        if category:
            if "Category" in df_filtered.columns:
                df_filtered = df_filtered[df_filtered["Category"] == category]
                query_ops.append(f"Category == {category}")
            elif len(df_parts) > 0:
                matching_parts = df_parts[df_parts["Category"] == category]["Part_Number"]
                df_filtered = df_filtered[df_filtered["Part_Number"].isin(matching_parts)]
                query_ops.append(f"Part Category via Parts_Master == {category}")

        # 5. Logistics Partner
        partner = active_filters.get("partner")
        if partner:
            df_filtered = df_filtered[df_filtered["Logistics_Partner"] == partner]
            query_ops.append(f"Logistics_Partner == {partner}")

        # 6. Priority — dataset values: P1-Critical, P2-High, P3-Medium, P4-Low
        priority = active_filters.get("priority")
        if priority:
            df_priority_direct = df_filtered[df_filtered["Priority"].astype(str) == priority]
            if not df_priority_direct.empty:
                df_filtered = df_priority_direct
                query_ops.append(f"Priority == {priority}")
            else:
                q = priority.lower()
                if "high" in q or "critical" in q or "p1" in q:
                    df_filtered = df_filtered[df_filtered["Priority"].astype(str).str.lower().str.contains("high|critical|p1")]
                elif "medium" in q or "p3" in q:
                    df_filtered = df_filtered[df_filtered["Priority"].astype(str).str.lower().str.contains("medium|p3")]
                elif "low" in q or "p4" in q:
                    df_filtered = df_filtered[df_filtered["Priority"].astype(str).str.lower().str.contains("low|p4")]
                elif "p2" in q:
                    df_filtered = df_filtered[df_filtered["Priority"].astype(str).str.lower().str.contains("p2")]
                query_ops.append(f"Priority fuzzy == {priority}")

        # 7. SLA Status — dataset SLA_Breach values: 'YES' (breached) or 'NO' (met)
        status = active_filters.get("status")
        if status:
            s = status.strip().upper()
            if s in ["YES", "BREACHED", "MISSED", "MISSED SLA", "BREACH"]:
                val = "YES"
            elif s in ["NO", "MET", "MET SLA", "ON TIME", "COMPLIANT"]:
                val = "NO"
            else:
                val = status
            df_filtered = df_filtered[df_filtered["SLA_Breach"] == val]
            query_ops.append(f"SLA_Breach == {val}")

        # 8. Flow Type / Shipment Type
        flow = active_filters.get("flow_type")
        if flow:
            df_filtered = df_filtered[df_filtered["Flow_Type"] == flow]
            query_ops.append(f"Flow_Type == {flow}")
        else:
            shipment_type = active_filters.get("shipment_type")
            if shipment_type:
                q = shipment_type.lower()
                if "parts" in q or "replace" in q or "reverse" in q:
                    flow_val = "reverse"
                elif "standard" in q or "delivery" in q or "forward" in q:
                    flow_val = "forward"
                else:
                    flow_val = q
                # Flow_Type in dataset is 'Forward'/'Reverse' (title case)
                if flow_val in ["forward", "reverse"]:
                    flow_val_title = flow_val.title()
                    df_filtered = df_filtered[df_filtered["Flow_Type"].astype(str).str.lower() == flow_val]
                else:
                    df_filtered = df_filtered[
                        (df_filtered["Flow_Type"].astype(str).str.lower() == flow_val) |
                        (df_filtered["Category"].astype(str).str.lower().str.contains(flow_val))
                    ]
                query_ops.append(f"Flow_Type == {flow_val} or Category contains {flow_val}")

        # 9. Region -> Hub_Location_Master.Primary_Region or Region
        region = active_filters.get("region")
        if region:
            df_hub = repository._processed_sheets.get("Hub_Location_Master")
            if df_hub is not None:
                region_col = "Primary_Region" if "Primary_Region" in df_hub.columns else ("Region" if "Region" in df_hub.columns else df_hub.columns[0])
                matching_hubs = list(df_hub[df_hub[region_col].astype(str).str.lower().str.contains(region.lower())]["Hub_ID"])
                if matching_hubs:
                    df_filtered = df_filtered[df_filtered["Origin_Hub"].isin(matching_hubs) | df_filtered["Destination_Hub"].isin(matching_hubs)]
                    query_ops.append(f"Hub Region ({region_col}) contains {region}")

        # 10. Route -> matches Origin (Origin_Hub) and Destination (Destination_Location)
        route = active_filters.get("route")
        if route:
            norm_route = route.replace("->", "|").replace("-", "|").replace("/", "|").replace(" to ", "|")
            parts = [p.strip() for p in norm_route.split("|") if p.strip()]
            if len(parts) >= 2:
                origin_q = parts[0].lower()
                dest_q = parts[1].lower()
                df_filtered = df_filtered[
                    df_filtered["Origin_Hub"].astype(str).str.lower().str.contains(origin_q) &
                    df_filtered["Destination_Location"].astype(str).str.lower().str.contains(dest_q)
                ]
                query_ops.append(f"Route split: Origin_Hub contains {origin_q} & Destination_Location contains {dest_q}")
            else:
                q = route.lower()
                df_filtered = df_filtered[
                    df_filtered["Origin_Hub"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Destination_Location"].astype(str).str.lower().str.contains(q)
                ]
                query_ops.append(f"Route contains {q} in Origin_Hub or Destination_Location")

        # 11. Transport Mode — direct Logistics_Partner name match (e.g. 'AirFreight Partners')
        transport_mode = active_filters.get("transport_mode")
        if transport_mode:
            df_direct = df_filtered[df_filtered["Logistics_Partner"].astype(str) == transport_mode]
            if not df_direct.empty:
                df_filtered = df_direct
                query_ops.append(f"Logistics_Partner == {transport_mode}")
            else:
                q = transport_mode.lower()
                df_filtered = df_filtered[df_filtered["Logistics_Partner"].astype(str).str.lower().str.contains(q)]
                query_ops.append(f"Logistics_Partner contains {q}")

        # 12. Search Text (check Part_No instead of Part_Number)
        search = active_filters.get("search")
        if search:
            q = search.lower()
            mode_matches = None
            if "air" in q:
                mode_matches = df_filtered["Logistics_Partner"].astype(str).str.lower().str.contains("air|flight|express")
            elif "ground" in q or "truck" in q or "road" in q:
                mode_matches = df_filtered["Logistics_Partner"].astype(str).str.lower().str.contains("ground|cargo|truck|fasttrack|swift|rail|road")
            
            part_col = "Part_No" if "Part_No" in df_filtered.columns else "Part_Number"
            
            if mode_matches is not None:
                df_filtered = df_filtered[
                    df_filtered["Transaction_ID"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Origin_Hub"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Destination_Location"].astype(str).str.lower().str.contains(q) |
                    df_filtered[part_col].astype(str).str.lower().str.contains(q) |
                    df_filtered["Part_Description"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Category"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Logistics_Partner"].astype(str).str.lower().str.contains(q) |
                    mode_matches
                ]
            else:
                df_filtered = df_filtered[
                    df_filtered["Transaction_ID"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Origin_Hub"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Destination_Location"].astype(str).str.lower().str.contains(q) |
                    df_filtered[part_col].astype(str).str.lower().str.contains(q) |
                    df_filtered["Part_Description"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Category"].astype(str).str.lower().str.contains(q) |
                    df_filtered["Logistics_Partner"].astype(str).str.lower().str.contains(q)
                ]
            query_ops.append(f"Global search: {q}")

        elapsed = (time.time() - start_time) * 1000
        query_executed = " & ".join(query_ops) if query_ops else "NO_ACTIVE_FILTERS"
        logger.info(f"[GeospatialFilter] Pandas query executed: {query_executed}")
        logger.info(f"[GeospatialFilter] Matching rows: {len(df_filtered)}. Execution time: {elapsed:.2f} ms")
        return df_filtered
