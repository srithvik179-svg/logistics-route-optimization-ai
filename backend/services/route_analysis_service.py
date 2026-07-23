import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.services.repository import repository
from backend.utils.logger import logger
from backend.services.geospatial_service import GeospatialService

class RouteAnalysisService:
    """Service to analyze routes, compute bottleneck flags, and prepare network graph datasets."""

    @classmethod
    def get_route_analysis_payload(cls, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the logistics network analysis and prepares the routes payload.
        
        Args:
            filters: Global filters dict.
            
        Returns:
            Dict containing overview, routes list, bottlenecks, flow analysis, and graph data.
        """
        logger.info(f"RouteAnalysisService: Analyzing network. Filters: {filters}")

        if not repository.is_initialized():
            repository.initialize()

        # Load sheets from repository
        df_tx_raw = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet_name = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet_name)
        df_parts = repository._processed_sheets.get("Parts_Master")

        # Fallbacks for safety
        if df_tx_raw is None:
            df_tx_raw = pd.DataFrame()
        if df_hub is None:
            df_hub = pd.DataFrame()
        if df_tpr is None:
            df_tpr = pd.DataFrame()
        if df_parts is None:
            df_parts = pd.DataFrame()

        # Enrich fields (partners, priorities, flow types)
        df = df_tx_raw.copy()
        if len(df) > 0:
            tpr_names = list(df_tpr["TPR_Name"]) if len(df_tpr) > 0 else ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"]
            df["Logistics_Partner"] = [tpr_names[i % len(tpr_names)] for i in range(len(df))]
            df["TPR_ID"] = df["Logistics_Partner"].map(GeospatialService.TPR_NAME_TO_ID).fillna("TPR-001")

            priorities = []
            flow_types = []
            for idx, r in df.iterrows():
                dest = str(r["Destination_Hub"])
                dist = float(r.get("Route_Distance") or 0.0)
                cost = float(r.get("Shipment_Cost") or 0.0)
                
                if dest.upper().startswith("TPR"):
                    flow_types.append("Outbound to TPR")
                elif dest.upper().startswith("HUB"):
                    flow_types.append("Hub-to-Hub Transfer")
                else:
                    flow_types.append("Outbound to TPR")
                
                if dist > 300.0 or cost > 300.0:
                    priorities.append("High Priority")
                elif dist > 100.0 or cost > 100.0:
                    priorities.append("Medium Priority")
                else:
                    priorities.append("Low Priority")
            df["Priority"] = priorities
            df["Flow_Type"] = flow_types

        # Apply global filters to transactions
        df_filtered = GeospatialService._apply_geospatial_filters(df, df_parts, filters)
        if len(df_filtered) == 0:
            logger.warning(f"RouteAnalysisService: No rows matched filters {filters}. Falling back to full dataset.")
            df_filtered = df.copy()

        # 1. Compile Route-Level Statistics
        routes_map = {}
        for idx, r in df_filtered.iterrows():
            orig = str(r["Origin_Hub"])
            dest = str(r["Destination_Hub"])
            
            # Note: We classify TPR flow based on destination starts with TPR or flow classification
            flow_type = str(r["Flow_Type"])
            if flow_type == "Outbound to TPR":
                dest_node = str(r["TPR_ID"])
            else:
                dest_node = dest
                
            route_key = (orig, dest_node)
            
            cost = float(r["Shipment_Cost"])
            dist = float(r.get("Route_Distance") or 0.0)
            transit_days = float((pd.to_datetime(r["Delivery_Date"]) - pd.to_datetime(r["Order_Date"])).days)
            prio = str(r["Priority"])
            
            # Standardize SLA detection
            raw_sla = str(r.get("SLA_Status") or r.get("SLA_Breach") or "NO").strip().upper()
            if raw_sla in ["ON TIME", "ON-TIME", "MET", "EARLY", "NO", "FALSE", "0"]:
                sla = "MET"
            else:
                sla = "MISSED"
                
            part_no = str(r["Part_Number"])
            partner = str(r["Logistics_Partner"])

            if route_key not in routes_map:
                routes_map[route_key] = {
                    "origin": orig,
                    "destination": dest_node,
                    "route_type": flow_type,
                    "costs": [],
                    "distances": [],
                    "transits": [],
                    "priorities": {},
                    "statuses": {},
                    "parts": set(),
                    "partners": set(),
                    "txn_ids": []
                }
            
            routes_map[route_key]["costs"].append(cost)
            routes_map[route_key]["distances"].append(dist)
            routes_map[route_key]["transits"].append(transit_days)
            routes_map[route_key]["priorities"][prio] = routes_map[route_key]["priorities"].get(prio, 0) + 1
            routes_map[route_key]["statuses"][sla] = routes_map[route_key]["statuses"].get(sla, 0) + 1
            routes_map[route_key]["parts"].add(part_no)
            routes_map[route_key]["partners"].add(partner)
            routes_map[route_key]["txn_ids"].append(str(r["Transaction_ID"]))

        # Convert to list and compute averages/flags
        routes_list = []
        bottlenecks_list = []
        
        # Collect values to find dynamic percentiles for bottlenecks
        all_avg_costs = []
        all_avg_transits = []
        all_volumes = []
        
        for k, v in routes_map.items():
            all_avg_costs.append(sum(v["costs"]) / len(v["costs"]))
            all_avg_transits.append(sum(v["transits"]) / len(v["transits"]))
            all_volumes.append(len(v["txn_ids"]))
            
        cost_cutoff = pd.Series(all_avg_costs).quantile(0.85) if all_avg_costs else 1500.0
        transit_cutoff = pd.Series(all_avg_transits).quantile(0.85) if all_avg_transits else 8.0

        for route_key, r_data in routes_map.items():
            shipment_count = len(r_data["txn_ids"])
            avg_cost = sum(r_data["costs"]) / shipment_count
            avg_transit = sum(r_data["transits"]) / shipment_count
            avg_distance = sum(r_data["distances"]) / shipment_count
            
            on_time_count = r_data["statuses"].get("MET", 0)
            delay_count = r_data["statuses"].get("MISSED", 0)
            delay_rate = (delay_count / shipment_count) * 100.0 if shipment_count > 0 else 0.0
            sla_compliance_pct = round((on_time_count / shipment_count) * 100.0, 1) if shipment_count > 0 else 0.0
            
            # Intelligent Bottleneck Classification: only flag true problem routes
            reasons = []
            if sla_compliance_pct < 25.0:
                reasons.append("Frequent SLA Delays")
            if avg_transit >= transit_cutoff and delay_rate >= 70.0:
                reasons.append("High Transit Duration")
            if avg_cost >= cost_cutoff and delay_rate >= 70.0:
                reasons.append("High Logistics Cost")
                
            is_bottleneck = len(reasons) > 0
            bottleneck_reason = ", ".join(reasons) if is_bottleneck else ""
            
            route_item = {
                "origin": r_data["origin"],
                "destination": r_data["destination"],
                "route_type": r_data["route_type"],
                "distance": round(avg_distance, 1),
                "transit_time": round(avg_transit, 1),
                "shipment_count": shipment_count,
                "avg_cost": round(avg_cost, 2),
                "priority_dist": r_data["priorities"],
                "status_dist": r_data["statuses"],
                "on_time_count": on_time_count,
                "delay_count": delay_count,
                "delay_rate": round(delay_rate, 1),
                "sla_compliance_pct": sla_compliance_pct,
                "parts": list(r_data["parts"]),
                "partners": list(r_data["partners"]),
                "transaction_ids": r_data["txn_ids"],
                "is_bottleneck": is_bottleneck,
                "bottleneck_reason": bottleneck_reason
            }
            
            routes_list.append(route_item)
            if is_bottleneck:
                bottlenecks_list.append(route_item)

        logger.info(f"RouteAnalysisService: Routes Loaded event logged. Mapped {len(routes_list)} routes.")

        # 2. Network Overview Metrics
        total_routes = len(routes_list)
        hub_connections = sum(1 for r in routes_list if r["route_type"] == "Hub-to-Hub Transfer")
        rc_connections = sum(1 for r in routes_list if r["route_type"] == "Outbound to TPR")
        
        network_avg_distance = df_filtered["Route_Distance"].mean() if len(df_filtered) > 0 and "Route_Distance" in df_filtered.columns else 0.0
        network_avg_cost = df_filtered["Shipment_Cost"].mean() if len(df_filtered) > 0 and "Shipment_Cost" in df_filtered.columns else 0.0
        network_avg_transit = 0.0
        if len(df_filtered) > 0 and "Delivery_Date" in df_filtered.columns and "Order_Date" in df_filtered.columns:
            ts = pd.to_datetime(df_filtered["Delivery_Date"]) - pd.to_datetime(df_filtered["Order_Date"])
            network_avg_transit = ts.dt.days.mean()
            
        avg_shipments = sum(r["shipment_count"] for r in routes_list) / total_routes if total_routes > 0 else 0.0

        overview = {
            "total_active_routes": total_routes,
            "total_hub_connections": hub_connections,
            "total_rc_connections": rc_connections,
            "avg_route_distance": round(network_avg_distance, 1),
            "avg_transit_time": round(network_avg_transit, 1),
            "avg_logistics_cost": round(network_avg_cost, 2),
            "avg_shipments_per_route": round(avg_shipments, 1),
            "bottlenecks_count": len(bottlenecks_list)
        }

        # 3. Flow Analysis Breakdowns
        # Outbound vs Inbound volume per hub
        hubs_set = set(df_hub["Hub_ID"]) if len(df_hub) > 0 and "Hub_ID" in df_hub.columns else (set(df_tx_raw["Origin_Hub"].dropna().unique()).union(set(df_tx_raw["Destination_Hub"].dropna().unique())) if len(df_tx_raw) > 0 else set())
        hub_flows = {}
        for h in hubs_set:
            outbound_qty = df_filtered[df_filtered["Origin_Hub"] == h]["Quantity"].sum() if "Quantity" in df_filtered.columns else 0
            inbound_qty = df_filtered[df_filtered["Destination_Hub"] == h]["Quantity"].sum() if "Quantity" in df_filtered.columns else 0
            
            outbound_cnt = len(df_filtered[df_filtered["Origin_Hub"] == h])
            inbound_cnt = len(df_filtered[df_filtered["Destination_Hub"] == h])

            outbound = int(outbound_qty) if outbound_qty > 0 else outbound_cnt
            inbound = int(inbound_qty) if inbound_qty > 0 else inbound_cnt
            net = outbound - inbound

            total_vol = outbound + inbound
            outbound_pct = round((outbound / total_vol) * 100.0, 1) if total_vol > 0 else 50.0
            inbound_pct = round((inbound / total_vol) * 100.0, 1) if total_vol > 0 else 50.0

            imbalance_label = "Outbound Heavy" if net > 50 else ("Inbound Heavy" if net < -50 else "Balanced")

            hub_flows[h] = {
                "inbound": inbound,
                "outbound": outbound,
                "net": net,
                "inbound_pct": inbound_pct,
                "outbound_pct": outbound_pct,
                "imbalance_label": imbalance_label
            }
            
        hub_to_hub_val = int(df_filtered[df_filtered["Flow_Type"] == "Hub-to-Hub Transfer"]["Quantity"].sum()) if len(df_filtered) > 0 and "Flow_Type" in df_filtered.columns and "Quantity" in df_filtered.columns else 0
        hub_to_repair_val = int(df_filtered[df_filtered["Flow_Type"] == "Outbound to TPR"]["Quantity"].sum()) if len(df_filtered) > 0 and "Flow_Type" in df_filtered.columns and "Quantity" in df_filtered.columns else 0

        # Flow type summary segment counts
        flow_segments = {
            "hub_to_hub": hub_to_hub_val,
            "hub_to_repair": hub_to_repair_val,
            "repair_to_hub": 0 # Default placeholder for future loopback flow
        }

        # 4. Network Graph nodes & edges structure
        nodes_list = []
        edges_list = []
        
        # Add Hub Nodes
        for idx, r in df_hub.iterrows():
            hub_id = str(r["Hub_ID"])
            fb = GeospatialService.COORDINATES_FALLBACK.get(hub_id, {"lat": 30.0, "lon": -100.0})
            
            # Node shipment volume counts
            node_txs = df_filtered[(df_filtered["Origin_Hub"] == hub_id) | (df_filtered["Destination_Hub"] == hub_id)]
            total_vol = len(node_txs)
            
            nodes_list.append({
                "id": hub_id,
                "name": str(r["Hub_Name"]),
                "type": fb.get("type", "Distribution Hub"),
                "lat": float(r.get("Latitude") or fb["lat"]),
                "lon": float(r.get("Longitude") or fb["lon"]),
                "volume": total_vol
            })

        # Add Repair Center Nodes
        for idx, r in df_tpr.iterrows():
            rc_id = str(r["TPR_ID"])
            fb = GeospatialService.COORDINATES_FALLBACK.get(rc_id, {"lat": 31.0, "lon": -99.0})
            
            node_txs = df_filtered[df_filtered["TPR_ID"] == rc_id]
            total_vol = len(node_txs)
            
            nodes_list.append({
                "id": rc_id,
                "name": str(r["TPR_Name"]),
                "type": "Repair Center",
                "lat": float(r.get("Latitude") or fb["lat"]),
                "lon": float(r.get("Longitude") or fb["lon"]),
                "volume": total_vol
            })

        # Edges (flows) list
        for r in routes_list:
            edges_list.append({
                "source": r["origin"],
                "target": r["destination"],
                "volume": r["shipment_count"],
                "avg_cost": r["avg_cost"],
                "avg_transit": r["transit_time"],
                "flow_type": r["route_type"],
                "is_bottleneck": r["is_bottleneck"]
            })
        logger.info("RouteAnalysisService: Network Graph Built event logged.")

        # 5. Heatmap matrix data
        # Sort routes by volume, cost, and transit to serve direct heatmap feeds
        heatmap = {
            "by_volume": sorted(routes_list, key=lambda x: x["shipment_count"], reverse=True)[:10],
            "by_transit": sorted(routes_list, key=lambda x: x["transit_time"], reverse=True)[:10],
            "by_cost": sorted(routes_list, key=lambda x: x["avg_cost"], reverse=True)[:10]
        }
        logger.info("RouteAnalysisService: Heatmap Generated event logged.")

        return {
            "overview": overview,
            "routes": routes_list,
            "bottlenecks": bottlenecks_list,
            "flows": {
                "hubs": hub_flows,
                "segments": flow_segments
            },
            "graph": {
                "nodes": nodes_list,
                "edges": edges_list
            },
            "heatmap": heatmap
        }
