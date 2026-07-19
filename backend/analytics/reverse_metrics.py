"""Reverse Logistics Metrics Engine — Computes returns, recycling, and asset recovery parameters."""

from typing import Dict, Any, List
import pandas as pd
import datetime

class ReverseMetrics:
    """Simulates return transactions and computes asset recovery/reverse network analytics."""

    @classmethod
    def compile_returns(cls, df_tx: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generates deterministic return transactions based on delivery data.
        
        Args:
            df_tx: Processed Logistics Transactions DataFrame.
            
        Returns:
            List of returns records.
        """
        returns = []
        if df_tx.empty:
            return []

        reasons = [
            "Customer Return", "Rejected Delivery", "Cancelled Shipment",
            "Damaged Goods", "Supplier Return", "Warehouse Return", "Expired Inventory"
        ]

        statuses = ["Pending", "In Transit", "Processing", "Refurbished", "Recycled"]

        for idx, r in df_tx.iterrows():
            txn_id = str(r["Transaction_ID"])
            orig = str(r["Origin_Hub"])
            dest = str(r["Destination_Hub"])
            cost = float(r["Shipment_Cost"])
            dist = float(r.get("Route_Distance") or 100.0)
            
            # Deterministic criteria for creating returns:
            # Missed SLAs or specific transaction IDs will simulate returns
            is_missed = r["SLA_Status"] == "MISSED"
            is_even = hash(txn_id) % 2 == 0
            
            if is_missed or is_even:
                ret_idx = len(returns)
                reason = reasons[ret_idx % len(reasons)]
                status = statuses[ret_idx % len(statuses)]
                
                # Reverse flows: origin of return is dest of original
                ret_orig = dest
                ret_dest = orig
                
                # Estimated completion dates
                order_date = pd.to_datetime(r["Order_Date"])
                completion_est = (order_date + datetime.timedelta(days=int(dist/80.0) + 2)).strftime("%Y-%m-%d")
                
                returns.append({
                    "return_id": f"RET-{txn_id}",
                    "shipment_id": txn_id,
                    "origin": ret_orig,
                    "destination": ret_dest,
                    "reason": reason,
                    "status": status,
                    "current_hub": ret_orig if status in ["Pending", "In Transit"] else ret_dest,
                    "transport_mode": "Ground Transport" if dist < 300.0 else "Air Freight",
                    "days_in_transit": round(dist / 120.0, 1),
                    "estimated_completion": completion_est,
                    "return_cost": round(cost * 0.75, 2), # returns cost ~75% of forward shipping
                    "part_number": str(r["Part_Number"]),
                    "quantity": int(r.get("Quantity") or 1),
                    "part_value": int(r.get("Quantity") or 1) * 85.0 # approximate value per part
                })

        return returns

    @classmethod
    def calculate_analytics(cls, returns: List[Dict[str, Any]], total_shipments: int) -> Dict[str, Any]:
        """Computes return rates, recovery rates, and values.
        
        Args:
            returns: List of return records.
            total_shipments: Total count of forward shipments in database.
            
        Returns:
            Dict containing return metrics and summaries.
        """
        if not returns:
            return {
                "return_rate": 0.0,
                "recovery_rate": 0.0,
                "avg_return_time": 0.0,
                "avg_return_cost": 0.0,
                "recovered_value": 0.0,
                "scrap_value": 0.0,
                "refurbishment_success_rate": 100.0,
                "recycling_percentage": 0.0,
                "reverse_network_utilization": 0.0
            }

        total_returns = len(returns)
        return_rate = (total_returns / max(1, total_shipments)) * 100.0

        refurbished_count = sum(1 for r in returns if r["status"] == "Refurbished")
        recycled_count = sum(1 for r in returns if r["status"] == "Recycled")
        recovery_rate = ((refurbished_count + recycled_count) / total_returns) * 100.0

        avg_time = sum(r["days_in_transit"] for r in returns) / total_returns
        avg_cost = sum(r["return_cost"] for r in returns) / total_returns

        # Recovered and Scrap value estimates
        recovered_val = sum(r["part_value"] * 0.85 for r in returns if r["status"] == "Refurbished")
        scrap_val = sum(r["part_value"] * 0.15 for r in returns if r["status"] == "Recycled")

        refurb_rate = (refurbished_count / max(1, refurbished_count + recycled_count)) * 100.0
        recycled_pct = (recycled_count / total_returns) * 100.0

        return {
            "return_rate": round(return_rate, 1),
            "recovery_rate": round(recovery_rate, 1),
            "avg_return_time": round(avg_time, 1),
            "avg_return_cost": round(avg_cost, 2),
            "recovered_value": round(recovered_val, 2),
            "scrap_value": round(scrap_val, 2),
            "refurbishment_success_rate": round(refurb_rate, 1),
            "recycling_percentage": round(recycled_pct, 1),
            "reverse_network_utilization": round(total_returns * 3.5, 1) # utilization factor
        }
