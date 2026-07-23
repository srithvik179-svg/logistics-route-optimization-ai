# RoutePilot AI – Frontend Module Reference

## Overview

RoutePilot AI is built as a single-page application (SPA) featuring **14 independent enterprise modules**. Each module operates in its own isolated viewport section within `frontend/index.html` and is managed by dedicated JavaScript controllers under `frontend/js/`, `frontend/pages/`, and `frontend/components/`.

---

## Module Directory

```
frontend/
├── index.html                  # Main SPA Viewport (contains 14 <section class="viewport-section">)
├── css/                        # Global and module-specific styling
├── js/
│   ├── app.js                  # Main SPA Navigation Router & Event Bus
│   ├── workspace.js            # Workspace Filter & State Coordinator
│   ├── executive_dashboard.js  # Module 6: Executive Dashboard Controller
│   ├── circular_supply_chain.js# Module 11: Circular Supply Chain Controller
│   ├── command_center_3d.js    # Module 3: 3D AI Command Center (Three.js WebGL)
│   └── demo_mode.js            # Module 14: 🎯 Demo Mode Presentation Engine
├── pages/                      # Feature-specific page logic
│   ├── route-recommendation/   # Module 13: Route Recommendation Engine
│   ├── cost-optimization/      # Module 9: Cost Optimization & What-If Simulator
│   ├── reverse-logistics/      # Module 10: Reverse Logistics & TPR Optimizer
│   ├── sla-prediction/         # Module 12: ML SLA Breach Risk Predictor
│   └── executive-reports/      # Report Exporter Component
└── components/                 # Reusable UI widgets and dialogs
```

---

## 1. Overview / Home

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🏠 Overview |
| **Section ID** | `#overview-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `GET /api/v1/monitoring/health-status` |
| **Purpose** | Executive landing page displaying system status, core metrics, dataset validation summary, and quick launch links. |

### Key Features
- Active Data Layer health status indicator (96.64 Quality Score)
- Enterprise Command Twin welcome overview card
- Quick navigation shortcuts to key modules (Analytics, Network Map, Route Optimization, AI Insights)
- Operations log feed showing live pipeline events

---

## 2. Operations Command Center

| Property | Detail |
|:---|:---|
| **Sidebar Label** | ⚡ Command Center |
| **Section ID** | `#command-center-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `POST /api/command-center/payload` |
| **Purpose** | Real-time operational situational awareness dashboard displaying active network alerts, bottleneck warnings, and live KPI feeds. |

### Key Features
- Real-time alert cards classified by severity (Critical, Warning, Info)
- Network health status cards (Active Hubs, Delayed Shipments, SLA Compliance, TPR Utilization)
- Quick command triggers (Dispatch Order, Reload Data, System Diagnostics)

---

## 3. 3D AI Command Center

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🌐 3D AI Command Center |
| **Section ID** | `#command-3d-section` |
| **Primary JS** | `frontend/js/command_center_3d.js` |
| **API Endpoint** | `POST /api/geospatial-network/payload` |
| **Purpose** | Immersive WebGL Digital Twin of Dell's global logistics topology built with Three.js. |

### Key Features
- 3D sphere representations of 12 distribution hubs with status-based glowing materials
- Animated particle streams moving along corridor arcs representing active shipment velocity
- Interactive Three.js OrbitControls (pan, zoom, rotate, reset camera)
- Filter integration: live dataset updates respond to Global Workspace Filters
- 3D Raycasting node inspector displaying hub metrics on click

---

## 4. Geospatial Intelligence

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🗺️ Geospatial Intel |
| **Section ID** | `#geospatial-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `POST /api/geospatial-network/payload` |
| **Purpose** | Geographic map visualization of hubs, corridors, and regional clusters powered by Leaflet.js. |

### Key Features
- Interactive Leaflet map with custom marker clusters for distribution hubs
- Direct polyline corridor overlays indicating flow volume and SLA health
- Spatial radius search and interactive location filtering

---

## 5. AI Logistics Copilot

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🤖 AI Copilot |
| **Section ID** | `#copilot-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `POST /api/copilot/query` |
| **Purpose** | Conversational AI assistant enabling natural language queries against Dell's logistics dataset. |

### Key Features
- Rich response formatting (tables, key metrics, actionable recommendations)
- Suggested prompt chips for instant execution
- Conversation history tracking and export capabilities

---

## 6. Executive Dashboard

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 📊 Executive Dashboard |
| **Section ID** | `#dashboard-section` |
| **Primary JS** | `frontend/js/executive_dashboard.js` |
| **API Endpoint** | `POST /api/executive-dashboard/payload` |
| **Purpose** | High-level business performance metrics, cost breakdowns, and strategic logistics KPIs. |

### Key Features
- 4 primary KPI scorecards (Cost Savings, On-Time SLA, Asset Recovery, Carbon Offset)
- Interactive trend charts comparing historical vs optimized performance
- Regional distribution charts and logistics partner benchmark tables

---

## 7. Logistics Network Map

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🕸️ Network Topology |
| **Section ID** | `#network-map-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `POST /api/geospatial-network/payload` |
| **Purpose** | Dedicated topological node-edge graph view focused on hub interconnectivity and throughput bottlenecks. |

### Key Features
- Node degree centrality visualizer
- Inbound vs outbound flow imbalance indicators per hub
- Bottleneck highlighting (e.g., TPR-BLR-01 capacity overload)

---

## 8. Route Intelligence

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🛣️ Route Intelligence |
| **Section ID** | `#routes-section` |
| **Primary JS** | `frontend/js/app.js` |
| **API Endpoint** | `POST /api/route-analysis/payload` |
| **Purpose** | In-depth corridor analytics, transit time distribution, and delay root cause identification. |

### Key Features
- Route delay heatmap by day-of-week and carrier
- Corridor throughput vs capacity variance analysis
- Carrier performance ranking matrix

---

## 9. Cost Optimization

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 💰 Cost Optimization |
| **Section ID** | `#cost-section` |
| **Primary JS** | `frontend/pages/cost-optimization/cost_optimization.js` |
| **API Endpoint** | `POST /api/cost-optimization/simulate` |
| **Purpose** | Financial optimization engine and 10-lever What-If scenario simulator. |

### Key Features
- Suboptimal dispatch audit table identifying $523K in annual waste
- Interactive 10-lever slider simulator (carrier rates, fuel surcharge, load factor, etc.)
- Real-time ROI and payback timeline calculator

---

## 10. Reverse Logistics

| Property | Detail |
|:---|:---|
| **Sidebar Label** | ↩️ Reverse Logistics |
| **Section ID** | `#reverse-section` |
| **Primary JS** | `frontend/pages/reverse-logistics/reverse_logistics.js` |
| **API Endpoint** | `POST /api/reverse-logistics/recommend-tpr` |
| **Purpose** | Return shipment management, AI triage classification, and TPR repair center load balancing. |

### Key Features
- AI return classification (Repair, Refurbish, Redeploy, Recycle)
- 8 TPR center capacity ranking & queue depth monitor
- Shipment consolidation batch planner (saved $9,700 freight cost)

---

## 11. AI Circular Supply Chain

| Property | Detail |
|:---|:---|
| **Sidebar Label** | ♻️ Circular Supply Chain |
| **Section ID** | `#circular-section` |
| **Primary JS** | `frontend/js/circular_supply_chain.js` |
| **API Endpoint** | `POST /api/circular-supply-chain/payload` |
| **Purpose** | 8-stage circular economy lifecycle engine for part reuse, component harvesting, and carbon reduction. |

### Key Features
- 8-stage lifecycle tracker (Collection to Carbon Accounting)
- Category breakdown for component harvesting and direct redeployment
- Sustainability impact metrics (2,847t CO₂e avoided, $612K procurement saved)

---

## 12. SLA Prediction

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🔮 SLA Prediction |
| **Section ID** | `#sla-section` |
| **Primary JS** | `frontend/pages/sla-prediction/sla_prediction.js` |
| **API Endpoint** | `POST /api/sla-prediction/predict` |
| **Purpose** | Machine learning risk predictor evaluating SLA breach risk with SHAP explainability. |

### Key Features
- Random Forest Ensemble ML breach probability calculator (94.8% accuracy)
- 7-vector risk radar chart
- 12-month predictive SLA trend forecast

---

## 13. AI Recommendation Engine

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🤖 AI Recommendations |
| **Section ID** | `#recommendation-section` |
| **Primary JS** | `frontend/pages/route-recommendation/recommendation.js` |
| **API Endpoint** | `POST /api/route-recommendation/recommend` |
| **Purpose** | Autonomous shipment routing recommendation engine with animated playback. |

### Key Features
- Top-5 ranked route recommendations with composite 14-parameter confidence scores
- Animated route playback controller on Leaflet map (play, pause, speed control)
- Side-by-side scenario comparison matrix & CSV export

---

## 14. 🎯 Demo Mode

| Property | Detail |
|:---|:---|
| **Sidebar Label** | 🎯 Demo Mode |
| **Section ID** | `#demo-section` |
| **Primary JS** | `frontend/js/demo_mode.js` |
| **API Endpoint** | `POST /api/v1/demo/reset` |
| **Purpose** | Dedicated judge presentation mode with automated guided tour across all modules. |

### Key Features
- Auto-guided 8-step presentation walkthrough
- Floating story overlays explaining Problem → AI Solution → Business Impact
- Keyboard shortcuts (`Space`, `→`, `←`, `R`, `Esc`), Fullscreen mode, and Live/Demo data toggle
- Pre-rendered Executive Impact Summary screen
