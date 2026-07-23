# RoutePilot AI – API Reference

## Overview

The RoutePilot AI API Gateway is implemented in Python using **FastAPI** (ASGI). All core endpoints accept standard HTTP requests, enforce rate limiting, log structured audit events, and return standardized JSON payloads.

---

## Authentication & Headers

Protected endpoints require a JWT Bearer token passed in the `Authorization` header:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Global Filter Payload Schema
Most `POST` analytical endpoints accept an optional JSON body containing workspace filters:

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "hub_location": "HUB-DEL",
  "region": "North India",
  "route_od": "HUB-DEL→HUB-BLR",
  "flow_type": "Forward",
  "logistics_partner": "BlueDart",
  "priority": "High",
  "sla_status": "Breached"
}
```

---

## Endpoint Catalog

### 1. Monitoring & System Health

#### `GET /api/v1/monitoring/health-status`
- **Purpose:** System health indicators across API Gateway, Repository, ML Models, and System Resources.
- **Authentication:** Not required
- **Response Example (200 OK):**
```json
{
  "status": "HEALTHY",
  "timestamp": "2026-07-24T01:30:00Z",
  "uptime_seconds": 14205,
  "services": {
    "api_gateway": "UP",
    "repository": "UP",
    "ml_engine": "UP"
  },
  "dataset_quality": 96.64
}
```

#### `GET /api/v1/monitoring/diagnostics`
- **Purpose:** Diagnostic metadata including environment, Python version, loaded dataset path, and active configuration.
- **Authentication:** Required (`ADMIN_CONFIG`)

---

### 2. Autonomous Route Recommendation

#### `POST /api/route-recommendation/recommend`
- **Purpose:** Score and rank candidate routes for a given shipment across 14 AI criteria.
- **Authentication:** Required (`RUN_OPTIMIZATION`)
- **Request Body Example:**
```json
{
  "shipment_id": "SHP-1002",
  "origin_hub": "HUB-DEL",
  "destination_hub": "HUB-BLR",
  "priority": "High",
  "part_no": "PART-409"
}
```
- **Response Example (200 OK):**
```json
{
  "status": "SUCCESS",
  "recommended_routes": [
    {
      "rank": 1,
      "route_id": "HUB-DEL→HUB-BOM→HUB-BLR",
      "composite_score": 92.4,
      "estimated_hours": 14.5,
      "estimated_cost": 410.00,
      "sla_risk_probability": 0.04,
      "shap_attributions": {
        "distance": -2.1,
        "cost": +5.4,
        "hub_capacity": +8.2
      }
    }
  ]
}
```

---

### 3. Cost Optimization & Simulation

#### `POST /api/cost-optimization/simulate`
- **Purpose:** Run What-If financial simulations across 10 operational cost levers.
- **Authentication:** Required (`RUN_OPTIMIZATION`)
- **Request Body Example:**
```json
{
  "carrier_rate_discount": 0.10,
  "load_factor_target": 0.85,
  "tpr_batching_enabled": true
}
```
- **Response Example (200 OK):**
```json
{
  "baseline_annual_cost": 2830400.00,
  "simulated_annual_cost": 2307158.26,
  "annual_savings": 523241.74,
  "savings_percentage": 18.48,
  "roi_percentage": 172.5
}
```

---

### 4. Reverse Logistics & TPR Optimizer

#### `POST /api/reverse-logistics/recommend-tpr`
- **Purpose:** Classify returned parts (Repair/Refurbish/Redeploy/Recycle) and rank optimal TPR repair centers.
- **Authentication:** Required (`RUN_OPTIMIZATION`)
- **Request Body Example:**
```json
{
  "part_no": "PRT-9821",
  "condition_score": 0.65,
  "return_city": "Chennai"
}
```
- **Response Example (200 OK):**
```json
{
  "triage_recommendation": "REPAIR_AND_REDEPLOY",
  "ranked_tprs": [
    {
      "tpr_id": "TPR-HYD-01",
      "capacity_available": 45,
      "geographic_distance_km": 520,
      "rank_score": 94.2
    }
  ]
}
```

---

### 5. ML SLA Breach Risk Prediction

#### `POST /api/sla-prediction/predict`
- **Purpose:** Evaluate SLA breach risk probability for a shipment using Random Forest ML ensemble with SHAP explanations.
- **Authentication:** Required (`RUN_OPTIMIZATION`)
- **Response Example (200 OK):**
```json
{
  "breach_probability": 0.12,
  "risk_category": "LOW_RISK",
  "shap_factors": [
    {"feature": "Carrier_Reliability", "impact": -0.18},
    {"feature": "Friday_Dispatch", "impact": +0.05}
  ]
}
```

---

### 6. AI Circular Supply Chain

#### `POST /api/circular-supply-chain/payload`
- **Purpose:** Retrieve full 8-stage circular economy lifecycle data, redeployment opportunities, and CO₂ savings metrics.
- **Authentication:** Required (`VIEW_DASHBOARD`)
- **Response Example (200 OK):**
```json
{
  "circular_score": 67.0,
  "carbon_avoided_tonnes": 2847.5,
  "procurement_saved_usd": 612000.00,
  "lifecycle_stages": {
    "collection": 1800,
    "triage": 1420,
    "refurbishment": 850,
    "redeployment": 620
  }
}
```

---

### 7. Security Audit Trail

#### `POST /api/v1/security/audit-trail`
- **Purpose:** Search and inspect system audit trail logs.
- **Authentication:** Required (`VIEW_AUDIT`)
- **Response Example (200 OK):**
```json
{
  "total_records": 154,
  "events": [
    {
      "timestamp": "2026-07-24T01:15:22Z",
      "user": "admin@dell.com",
      "action": "RUN_COST_SIMULATION",
      "status": "SUCCESS"
    }
  ]
}
```

---

## Standard Error Response Schema

When an API error occurs, the gateway returns a standard HTTP status code with the following JSON error body:

```json
{
  "status": "ERROR",
  "error_code": "INVALID_FILTER_PARAMETER",
  "message": "The provided start_date format must be YYYY-MM-DD.",
  "request_id": "req-98a2f1c8-31"
}
```
