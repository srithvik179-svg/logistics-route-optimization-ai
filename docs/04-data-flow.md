# RoutePilot AI – Data Flow Architecture

## 1. Data Sources

RoutePilot AI consumes a single Microsoft Excel workbook provided by Dell containing 5 interconnected sheets:

| Sheet | Rows | Columns | Key Fields |
|:---|:---|:---|:---|
| `Logistics_Transactions` | 1,800 | 49 | Shipment_ID, Dispatch_Date, Hub1_ID, Hub2_ID, TPR_ID, Part_No, Priority, SLA_Status, Carrier, Logistics_Cost, Transit_Duration, Actual_Delivery_Date, Expected_Delivery_Date, Flow_Type, Region |
| `Hub_Location_Master` | 12 | 11 | Hub_ID, Hub_Name, City, Country, Latitude, Longitude, Capacity, Hub_Type, Region, Contact, Status |
| `TPR_Master` | 8 | 11 | TPR_ID, TPR_Name, Location, Capacity, Repair_Types, Throughput_Rate, Queue_Depth, Status, Lat, Long, Region |
| `Parts_Master` | 178 | 11 | Part_No, Part_Category, Criticality, Lead_Time_Days, Unit_Value, Weight, Supplier, MOQ, Reorder_Point, Description, Status |
| `Summary_Dashboard` | 40 | 2 | KPI_Metric, KPI_Value (aggregated summary statistics) |

---

## 2. Data Processing Pipeline

```mermaid
flowchart TD
    EXCEL["📊 Dell_Logistics_Route_Optimization.xlsx\n5 sheets · 2,038 total rows"]
    
    EXCEL --> LOADER["DatasetLoader\n• Detects file presence\n• Validates sheet names\n• Opens with openpyxl"]
    
    LOADER --> VALIDATOR["DatasetValidator\n• Schema validation (49 expected columns)\n• Type checking\n• Required field presence\n• Value range checks\n• Output: Overall Validity = True · 96.64 Quality Score"]
    
    VALIDATOR --> PIPE["DataProcessingPipeline\n• Orchestrates all processors\n• Per-sheet processing\n• Records processing time"]
    
    PIPE --> DATE["DateProcessor\n• Parses 8 date columns\n• Normalises to datetime64\n• Enriches with year/month/quarter/weekday"]
    PIPE --> DUP["DuplicateProcessor\n• Detects duplicate rows\n• Removes 2 from Summary_Dashboard\n• Logs removed count"]
    PIPE --> QUAL["QualityScorer\n• Calculates completeness %\n• Scores each sheet\n• Aggregate: 96.64/100"]
    
    DATE & DUP & QUAL --> REPO["DataRepository\n(Singleton, In-Memory)\n• Holds 5 processed DataFrames\n• Zero disk I/O after init\n• Thread-safe read access"]
    
    REPO --> SVC["104 Service Modules\n(read-only access)"]
```

### Processing Times (Benchmarked)

| Sheet | Processing Time | Status |
|:---|:---|:---|
| Logistics_Transactions | ~145 ms | ✅ SUCCESS |
| Hub_Location_Master | ~3 ms | ✅ SUCCESS |
| TPR_Master | ~3 ms | ✅ SUCCESS |
| Parts_Master | ~14 ms | ✅ SUCCESS |
| Summary_Dashboard | ~1 ms | ✅ SUCCESS |
| **Total** | **~165 ms** | **Quality: 96.64** |

---

## 3. API Request Data Flow

```mermaid
sequenceDiagram
    actor U as 👤 User
    participant SPA as Vanilla JS SPA
    participant GW as api_gateway_integration.js
    participant NGINX as Nginx :80
    participant MW as FastAPI Middleware
    participant EP as Endpoint Handler
    participant GEO as GeospatialService
    participant SVC as AI Service
    participant REPO as DataRepository

    U->>SPA: Interacts with module / applies filters
    SPA->>GW: apiFetch(endpoint, filterPayload)
    GW->>GW: Attach JWT Bearer token
    GW->>NGINX: POST /api/[module]/payload
    NGINX->>MW: Proxy forward
    MW->>MW: Validate JWT · Generate Request ID · Log
    MW->>EP: Route to endpoint handler
    EP->>GEO: apply_filters(filter_payload)
    GEO->>REPO: get_processed_data('Logistics_Transactions')
    REPO-->>GEO: Full DataFrame (1,800 rows)
    GEO->>GEO: Boolean mask filtering (Pandas vectorised)
    Note over GEO: 0.04 ms for 1,800 rows · NO Python loops
    GEO-->>EP: Filtered DataFrame (N rows)
    EP->>SVC: analyse(filtered_df)
    SVC->>SVC: AI processing / calculations
    SVC-->>EP: Structured result dict
    EP-->>MW: JSON response payload
    MW->>MW: Log response time · Record metrics
    MW-->>NGINX: HTTP 200
    NGINX-->>GW: JSON payload
    GW->>GW: Cache payload (30s TTL)
    GW-->>SPA: Resolved promise
    SPA->>SPA: Render charts / tables / 3D scene
    SPA-->>U: Updated visualisation
```

---

## 4. End-to-End Data Journey

```mermaid
flowchart TD
    A["📂 Raw Excel File\nDell_Logistics_Route_Optimization.xlsx"] -->|"openpyxl"| B["📋 Raw DataFrames\n5 sheets loaded"]
    B -->|"DatasetValidator"| C["✅ Validated Dataset\n96.64 Quality Score"]
    C -->|"DataProcessingPipeline"| D["🔄 Processed DataFrames\nDates parsed · Dupes removed · Enriched"]
    D -->|"In-memory store"| E["🗄️ DataRepository\nSingleton · Zero disk I/O per request"]
    E -->|"GeospatialService\napply_filters()"| F["🔍 Filtered DataFrame\nApplies user's global workspace filters"]
    F -->|"AI Engine"| G["🤖 AI Analysis\nScoring · ML · Optimisation · Lifecycle"]
    G -->|"FastAPI endpoint"| H["📦 JSON Payload\nStructured response"]
    H -->|"apiFetch() → Renderer"| I["📊 Frontend Visualisation\nCharts · Tables · 3D Scene · Maps"]
    I -->|"Export action"| J["📄 Executive Report\nPDF · Excel · CSV"]
```

---

## 5. Global Workspace Filter Flow

All 14 frontend modules share a single **Global Workspace Filter** bar. When filters change, every module re-queries with the new filter state.

```mermaid
flowchart LR
    USER["User sets\nglobal filters\n(Date · Hub · Region\nPriority · SLA · Partner)"] --> UI["app.js\ncollects filterPayload object"]
    UI --> EACH["Each active module\ncalls its API endpoint\nwith filterPayload"]
    EACH --> GEO["GeospatialService\n.apply_filters(filterPayload)"]
    GEO --> MASK["Pandas boolean mask\n• date range filter\n• hub location filter\n• region filter\n• priority filter\n• SLA status filter\n• flow type filter\n• partner filter"]
    MASK --> FILTERED["Filtered DataFrame\n(N rows ≤ 1,800)"]
    FILTERED --> AI["AI Engine processes\nonly filtered data"]
    AI --> PAYLOAD["Module-specific\nJSON payload"]
    PAYLOAD --> RENDER["Module re-renders\nwith filtered results"]
```

### Filter Schema

```json
{
    "start_date":         "YYYY-MM-DD",
    "end_date":           "YYYY-MM-DD",
    "hub_location":       "HUB-DEL",
    "region":             "North India",
    "route_od":           "HUB-DEL→HUB-BLR",
    "flow_type":          "Forward",
    "logistics_partner":  "BlueDart",
    "priority":           "High",
    "sla_status":         "Breached"
}
```
All fields are optional. Omitting a field means "no filter on that dimension."

---

## 6. Data Quality Report

| Metric | Value |
|:---|:---|
| Overall Quality Score | **96.64 / 100** |
| Logistics_Transactions completeness | **98.21%** |
| Hub_Location_Master completeness | **100%** |
| TPR_Master completeness | **100%** |
| Parts_Master completeness | **100%** |
| Summary_Dashboard completeness | **85%** (after dedup) |
| Duplicate rows removed | **2** (Summary_Dashboard) |
| Date columns enriched | **8** (Logistics_Transactions) |
| Schema validation | **PASSED** |
| Overall validity | **TRUE** |

---

## 7. Database / Dataset Design

> RoutePilot AI uses Excel as its data store (as provided by Dell). The data model follows a relational structure across the 5 sheets.

```mermaid
erDiagram
    LOGISTICS_TRANSACTIONS {
        string Shipment_ID PK
        date Dispatch_Date
        string Hub1_ID FK
        string Hub2_ID FK
        string TPR_ID FK
        string Part_No FK
        string Carrier
        float Logistics_Cost
        int Transit_Duration
        string Priority
        string SLA_Status
        string Flow_Type
        string Region
        date Expected_Delivery_Date
        date Actual_Delivery_Date
    }

    HUB_LOCATION_MASTER {
        string Hub_ID PK
        string Hub_Name
        string City
        string Country
        float Latitude
        float Longitude
        int Capacity
        string Hub_Type
        string Region
    }

    TPR_MASTER {
        string TPR_ID PK
        string TPR_Name
        string Location
        int Capacity
        string Repair_Types
        float Throughput_Rate
        int Queue_Depth
        float Latitude
        float Longitude
    }

    PARTS_MASTER {
        string Part_No PK
        string Part_Category
        string Criticality
        int Lead_Time_Days
        float Unit_Value
        float Weight
        string Supplier
    }

    SUMMARY_DASHBOARD {
        string KPI_Metric PK
        string KPI_Value
    }

    LOGISTICS_TRANSACTIONS }|--|| HUB_LOCATION_MASTER : "Hub1_ID"
    LOGISTICS_TRANSACTIONS }|--|| HUB_LOCATION_MASTER : "Hub2_ID"
    LOGISTICS_TRANSACTIONS }|--o| TPR_MASTER : "TPR_ID"
    LOGISTICS_TRANSACTIONS }|--|| PARTS_MASTER : "Part_No"
```
