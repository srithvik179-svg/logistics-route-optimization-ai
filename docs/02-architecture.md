# RoutePilot AI – System Architecture

## 1. Overall System Architecture

```mermaid
flowchart TD
    subgraph CLIENT["🖥️ Client Browser"]
        UI["Vanilla JS SPA\n(index.html)\n14 Enterprise Modules"]
    end

    subgraph INFRA["🐳 Docker Compose Stack"]
        NGINX["Nginx Reverse Proxy\n:80 → :8000"]
        
        subgraph APP["FastAPI Application"]
            GW["API Gateway\nJWT · Rate Limit · CORS"]
            MW["Middleware Layer\nLogging · Auth · Request ID"]
            ROUTER["API Router\n14 endpoint groups"]
            
            subgraph ENGINES["AI Engine Layer"]
                RDE["RouteDecisionEngine"]
                COE["CostOptimizationEngine"]
                SPE["SLAPredictionEngine"]
                RLE["ReverseLogisticsEngine"]
                CSC["CircularSupplyChainService"]
                IRE["IntelligentRoutingEngine"]
                CCS["CommandCenterService"]
            end
            
            subgraph DATA["Data Layer"]
                REPO["DataRepository\n(In-Memory)"]
                PIPE["DataProcessingPipeline"]
                VAL["DatasetValidator\n96.64 Quality Score"]
            end
            
            subgraph SEC["Security"]
                RBAC["RBAC Engine\n8 Permission Scopes"]
                AUDIT["AuditTrailEngine"]
                HEALTH["HealthMonitoringEngine"]
            end
        end
    end

    subgraph STORAGE["📊 Data Storage"]
        EXCEL["Dell Logistics Dataset\n.xlsx · 5 sheets · 1,800 rows"]
    end

    subgraph CICD["⚙️ CI/CD"]
        GHA["GitHub Actions\nTest → Build → Deploy"]
    end

    UI -->|"HTTPS / API calls"| NGINX
    NGINX -->|"Proxy"| GW
    GW --> MW
    MW --> ROUTER
    ROUTER --> ENGINES
    ROUTER --> SEC
    ENGINES --> REPO
    REPO --> PIPE
    PIPE --> VAL
    VAL -->|"openpyxl"| EXCEL
    GHA -->|"on push to main"| APP
```

---

## 2. Backend Architecture

```mermaid
flowchart LR
    subgraph ENTRY["Entrypoint"]
        MAIN["main.py\n(FastAPI app)"]
    end

    subgraph API["API Layer"]
        MW["Middleware\n• Auth\n• Logging\n• Request ID\n• Rate Limit"]
        ROUTES["Router Groups\n• /api/route-*\n• /api/cost-*\n• /api/reverse-*\n• /api/sla-*\n• /api/circular-*\n• /api/command-*\n• /api/v1/*"]
    end

    subgraph SVC["Services (104 modules)"]
        AI["AI Engines\n• RouteDecisionEngine\n• CostOptimizationEngine\n• SLAPredictionEngine\n• ReverseLogisticsEngine\n• CircularSupplyChainService\n• IntelligentRoutingEngine"]
        SUPPORT["Support Services\n• GeospatialService\n• AnalyticsService\n• BiService\n• PerformanceService\n• ExplorerService"]
        ML["ML Pipeline\n• FeatureEngineering\n• ModelTraining\n• ShapExplainer\n• PredictionService"]
    end

    subgraph INFRA["Infrastructure"]
        REPO["DataRepository\n(Singleton)"]
        PIPE["DataProcessingPipeline"]
        CFG["config.py\n(Environment)"]
        MON["HealthMonitor\n• CPU · Memory\n• Latency · Errors"]
    end

    MAIN --> MW
    MW --> ROUTES
    ROUTES --> SVC
    SVC --> REPO
    REPO --> PIPE
    MAIN --> CFG
    MAIN --> MON
```

---

## 3. Frontend Architecture

```mermaid
flowchart TD
    subgraph HTML["index.html"]
        STYLE["CSS Layer\n• style.css\n• auth.css\n• demo_mode.css\n• design-system/"]
        NAV["Sidebar Navigation\n14 nav-link items"]
        SECTIONS["14 Workspace Sections\n(viewport-section)"]
    end

    subgraph JS["JavaScript Layer"]
        APP["app.js\nSPA Router + API Client"]
        WORKSPACE["workspace.js\nModule Initialiser"]
        
        subgraph MODULES["Enterprise Modules"]
            DASH["executive_dashboard.js"]
            CIRC["circular_supply_chain.js"]
            CMD3D["command_center_3d.js\n(Three.js WebGL)"]
            DEMO["demo_mode.js\n(Judge Mode)"]
            APIGW["api_gateway_integration.js"]
        end

        subgraph PAGES["Page Controllers\n(frontend/pages/)"]
            P1["route-recommendation/"]
            P2["cost-optimization/"]
            P3["reverse-logistics/"]
            P4["sla-prediction/"]
            P5["executive-reports/"]
        end

        subgraph COMPONENTS["Reusable Components\n(frontend/components/)"]
            C1["ScenarioBuilder"]
            C2["TPRDrillDownModal"]
            C3["FinancialCharts"]
            C4["RoutePlayback"]
            C5["NetworkExplorer"]
        end
    end

    NAV -->|"click → show/hide"| SECTIONS
    SECTIONS --> MODULES
    APP -->|"apiFetch()"| APIGW
    APIGW -->|"JWT · retry · cache"| BACKEND["FastAPI Backend\n:8000"]
    MODULES --> PAGES
    MODULES --> COMPONENTS
```

---

## 4. AI Engine Architecture

```mermaid
flowchart LR
    subgraph INPUT["Data Input"]
        REPO["DataRepository\n1,800 transactions\n12 hubs · 8 TPRs\n178 parts"]
        FILTERS["Global Filters\nDate · Hub · Region\nPriority · SLA Status"]
    end

    subgraph ENGINES["AI Processing Layer"]
        RDE["🛣️ RouteDecisionEngine\n14-parameter scoring\nTop-5 recommendations\nSHAP attribution"]
        COE["💰 CostOptimizationEngine\n10-lever What-If\n$523K savings identified\nAnnual ROI calculation"]
        SPE["📊 SLAPredictionEngine\nRandom Forest Ensemble\n94.8% accuracy · 0.968 AUC\n7-vector risk · 12-month forecast"]
        RLE["↩️ ReverseLogisticsEngine\nAI triage classification\nTPR capacity ranking\nBatch consolidation"]
        CSC["♻️ CircularSupplyChainService\n8-stage lifecycle engine\nCarbon accounting\nSustainability scoring"]
        IRE["🔀 IntelligentRoutingEngine\nDijkstra · A* · GA · ACO\nMulti-algorithm selection\nOptimal path finding"]
        CCS["🌐 CommandCenterService\nReal-time KPI aggregation\nAlert generation\n3D scene data feed"]
    end

    subgraph OUTPUT["Output Layer"]
        REC["Route Recommendations\n+ SHAP explanations"]
        SAV["Savings Report\n+ Scenario Results"]
        PRED["SLA Risk Scores\n+ Attribution"]
        TRIAGE["TPR Rankings\n+ Batch Plans"]
        CIRC["Lifecycle Report\n+ Sustainability"]
        PATH["Optimal Paths\n+ Tradeoffs"]
        KPI["Live KPIs\n+ Alerts"]
    end

    REPO --> ENGINES
    FILTERS --> ENGINES
    RDE --> REC
    COE --> SAV
    SPE --> PRED
    RLE --> TRIAGE
    CSC --> CIRC
    IRE --> PATH
    CCS --> KPI
```

---

## 5. Request-Response Data Flow

```mermaid
sequenceDiagram
    actor User as 👤 User
    participant UI as Vanilla JS SPA
    participant NGINX as Nginx Proxy
    participant MW as FastAPI Middleware
    participant EP as API Endpoint
    participant SVC as AI Service
    participant REPO as DataRepository
    participant DATA as Excel Dataset

    User->>UI: Selects module / applies filter
    UI->>UI: apiFetch() with JWT + filter payload
    UI->>NGINX: POST /api/[module]/payload
    NGINX->>MW: Forward request
    MW->>MW: Validate JWT · Assign Request ID · Log
    MW->>EP: Route to endpoint handler
    EP->>SVC: Call AI engine with filter params
    SVC->>REPO: get_processed_data(sheet)
    Note over REPO: In-memory DataFrame (no disk I/O)
    REPO-->>SVC: Filtered DataFrame
    SVC->>SVC: AI processing / ML inference
    SVC-->>EP: Structured result payload
    EP-->>MW: JSON response
    MW->>MW: Log response · Record latency
    MW-->>NGINX: HTTP 200 + payload
    NGINX-->>UI: JSON payload
    UI->>UI: Render charts / tables / 3D scene
    UI-->>User: Updated visualisation
```

---

## 6. Deployment Architecture

```mermaid
flowchart TD
    subgraph GITHUB["GitHub Repository"]
        CODE["Source Code\nmain branch"]
        GHA["GitHub Actions\nCI/CD Workflow"]
    end

    subgraph BUILD["Build Stage"]
        TEST["Test Job\n• test_route_analysis\n• test_command_center_3d\n• test_circular_supply_chain"]
        DOCKER["Docker Build Job\n• Multi-stage build\n• routepilot-ai:latest"]
    end

    subgraph RUNTIME["Docker Compose Runtime"]
        NGINX_C["nginx container\nPort: 80\nnginx/nginx.conf"]
        APP_C["routepilot-app container\nPort: 8000\nFastAPI + Uvicorn"]
        VOL["data/ volume\nDell_Logistics_Dataset.xlsx"]
    end

    subgraph ACCESS["Access Points"]
        WEB["http://localhost\n(via Nginx)"]
        API_D["http://localhost:8000/docs\n(Swagger UI — dev only)"]
    end

    CODE -->|"git push to main"| GHA
    GHA --> TEST
    TEST -->|"passes"| DOCKER
    DOCKER --> RUNTIME
    NGINX_C -->|"proxy_pass :8000"| APP_C
    APP_C --> VOL
    NGINX_C --> WEB
    APP_C --> API_D
```

---

## Module Relationships

| Module | Depends On | Used By |
|:---|:---|:---|
| `DataRepository` | `DataProcessingPipeline`, `DatasetValidator` | All 104 service modules |
| `DataProcessingPipeline` | `DateProcessor`, `DuplicateProcessor`, `QualityScorer` | `DataRepository` |
| `GeospatialService` | `DataRepository` | All payload endpoints |
| `RouteDecisionEngine` | `GeospatialService`, `GraphBuilder`, `ShortestPathEngine` | `/api/route-recommendation` |
| `CostOptimizationEngine` | `DataRepository`, `CostEngine`, `CostTrends` | `/api/cost-optimization` |
| `SLAPredictionEngine` | `FeatureEngineering`, `MLModelManager`, `ShapExplainer` | `/api/sla-prediction` |
| `ReverseLogisticsEngine` | `DataRepository`, `TPRScoring`, `BatchOptimiser` | `/api/reverse-logistics` |
| `CircularSupplyChainService` | `DataRepository`, `GeospatialService` | `/api/circular-supply-chain` |
| `CommandCenterService` | `DataRepository`, `SLAPredictionEngine` | `/api/command-center`, 3D frontend |
| `IntelligentRoutingEngine` | `GraphBuilder`, `DijkstraService`, `AStarEngine`, `GeneticAlgorithmEngine`, `AntColonyEngine` | `/api/route-recommendation/recommend` |
| `AuditTrailEngine` | `DataRepository` | Security middleware |
| `HealthMonitoringEngine` | System resources | `/api/v1/monitoring/*` |
