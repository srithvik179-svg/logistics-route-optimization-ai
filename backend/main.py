import os
import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from backend.config import BASE_DIR
from backend.services.repository import repository
from backend.services.state_manager import state_manager
from backend.utils.logger import logger
from backend.services.dataset_loader import DatasetLoader
from backend.services.explorer_service import ExplorerService
from backend.services.analytics_service import AnalyticsService
from backend.services.bi_service import BIService
from backend.services.geospatial_service import GeospatialService
from backend.services.route_analysis_service import RouteAnalysisService
from backend.services.performance_service import PerformanceService
from backend.services.cost_engine import CostEngine
from backend.services.transit_engine import TransitEngine
from backend.services.inventory_engine import InventoryEngine
from backend.services.capacity_engine import CapacityEngine
from backend.services.sla_engine import SLAEngine
from backend.services.graph_engine import GraphEngine
from backend.services.geospatial_engine import GeospatialEngine
from backend.services.shortest_path_engine import ShortestPathEngine
from backend.services.route_scoring_engine import RouteScoringEngine
from backend.services.optimization_readiness_engine import OptimizationReadinessEngine
from backend.services.astar_engine import AStarEngine
from backend.services.genetic_algorithm_engine import GeneticAlgorithmEngine
from backend.services.ant_colony_engine import AntColonyEngine
from backend.services.rl_preparation_engine import RLPreparationEngine
from backend.services.ai_preparation_engine import AIPreparationEngine
from backend.services.corridor_service import CorridorService
from backend.services.route_decision_engine import RouteDecisionEngine
from backend.services.intelligent_routing_engine import IntelligentRoutingEngine
from backend.services.cost_optimization_engine import CostOptimizationEngine
from backend.services.simulation_service import SimulationService
from backend.services.reverse_logistics_service import ReverseLogisticsService
from backend.services.reverse_logistics_engine import ReverseLogisticsEngine
from backend.services.sla_prediction_service import SLAPredictionService
from backend.services.sla_prediction_engine import SLAPredictionEngine
from backend.services.risk_forecasting_service import RiskForecastingService
from backend.orchestrator.workflow_engine import WorkflowEngine
from backend.services.report_generator import ReportGenerator
from backend.services.executive_reporting_engine import ExecutiveReportingEngine
from backend.services.circular_supply_chain_service import CircularSupplyChainService
from backend.security.audit_trail_engine import AuditTrailEngine
from backend.monitoring.health_monitoring_engine import HealthMonitoringEngine
from backend.monitoring.performance_optimization_engine import PerformanceOptimizationEngine
from backend.services.notification_backup_manager import NotificationBackupManager
from backend.services.system_info_service import SystemInfoService
from backend.ml.ai_model_lifecycle_manager import AIModelLifecycleManager
from backend.services.enterprise_validation_engine import EnterpriseValidationEngine
from backend.services.command_center_service import CommandCenterService
from backend.services.copilot_service import CopilotService
from backend.services.conversation_manager import conversation_manager
from backend.config import DEFAULT_DATASET_PATH
from backend.validators.dataset_validator import DatasetValidator

from backend.api.middleware import APIGatewayMiddleware
from backend.api.router import gateway_router
from backend.api.exception_handler import http_exception_handler, validation_exception_handler, general_exception_handler
from fastapi.exceptions import RequestValidationError
from backend.security.router import security_router
from backend.monitoring.router import monitoring_router

app = FastAPI(
    title="Dell Logistics Route Optimization AI Platform",
    description="Backend API for loading, validating, and managing route optimization datasets.",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Gateway middleware
app.add_middleware(APIGatewayMiddleware)

# Register API Gateway metadata router
app.include_router(gateway_router)

# Register Security router
app.include_router(security_router)

# Register Monitoring router
app.include_router(monitoring_router)

# Register global API exception handlers
from starlette.exceptions import HTTPException as StarletteHTTPException
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Initialize repository on application startup using modern lifespan handler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    logger.info("Application starting up... Initializing repository.")
    repository.initialize()
    yield
    logger.info("Application shutting down.")

app.router.lifespan_context = lifespan

# API Endpoints
@app.get("/api/dataset/status")
def get_dataset_status():
    """Returns the current dataset loading and validation status from the repository."""
    try:
        # If repository is not initialized, run initialization
        if not repository.is_initialized():
            repository.initialize()
            
        loader = DatasetLoader(DEFAULT_DATASET_PATH)
        metadata = loader.get_metadata()
        validation_report = DatasetValidator.validate(metadata, repository._sheets)
        
        return {
            "metadata": metadata.model_dump(),
            "validation_report": validation_report.model_dump() if validation_report else None
        }
    except Exception as e:
        logger.error(f"Error retrieving dataset status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/api/dataset/reload")
def reload_dataset():
    """Forces a reload and re-validation of the dataset from disk into the repository."""
    try:
        logger.info("Manual reload triggered via API.")
        repository.initialize()
        
        loader = DatasetLoader(DEFAULT_DATASET_PATH)
        metadata = loader.get_metadata()
        validation_report = DatasetValidator.validate(metadata, repository._sheets)
        
        return {
            "status": "success",
            "message": "Repository dataset reloaded and validated successfully.",
            "metadata": metadata.model_dump(),
            "validation_report": validation_report.model_dump() if validation_report else None
        }
    except Exception as e:
        logger.error(f"Error reloading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reload dataset: {str(e)}")

@app.post("/api/dataset/upload")
def upload_dataset(file: UploadFile = File(...)):
    """Receives uploaded Excel spreadsheet file, saves it, and reloads database repository."""
    try:
        logger.info(f"Uploading new dataset: {file.filename}")
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(DEFAULT_DATASET_PATH), exist_ok=True)
        
        # Save file to disk overwriting previous
        with open(DEFAULT_DATASET_PATH, "wb") as f:
            f.write(file.file.read())
            
        # Trigger same reload procedure
        repository.initialize()
        loader = DatasetLoader(DEFAULT_DATASET_PATH)
        metadata = loader.get_metadata()
        validation_report = DatasetValidator.validate(metadata, repository._sheets)
        
        return {
            "status": "success",
            "message": "Custom dataset uploaded, saved, and repository reloaded successfully.",
            "metadata": metadata.model_dump(),
            "validation_report": validation_report.model_dump() if validation_report else None
        }
    except Exception as e:
        logger.error(f"Error uploading and reloading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")

@app.get("/api/repository/status")
def get_repository_status():
    """Returns application state and repository statistics."""
    try:
        state = state_manager.get_state().model_dump()
        sheets = repository.list_available_sheets()
        
        sheet_stats = []
        for s in sheets:
            sheet_stats.append({
                "name": s,
                "rows": repository.get_row_count(s),
                "columns": repository.get_column_count(s)
            })
            
        # Extract active hubs and regions dynamically from datasets
        active_hubs = []
        active_regions = []
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        if df_hub is not None and len(df_hub) > 0:
            if "Hub_ID" in df_hub.columns:
                for _, r in df_hub.iterrows():
                    active_hubs.append({
                        "id": str(r["Hub_ID"]),
                        "name": str(r.get("Hub_Name", r["Hub_ID"]))
                    })
            region_col = "Region" if "Region" in df_hub.columns else ("Primary_Region" if "Primary_Region" in df_hub.columns else "")
            if region_col:
                active_regions = sorted(list(df_hub[region_col].dropna().unique()))

        return {
            "state": state,
            "sheets": sheet_stats,
            "is_initialized": repository.is_initialized(),
            "active_hubs": active_hubs,
            "active_regions": active_regions
        }
    except Exception as e:
        logger.error(f"Error fetching repository status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch repository status: {str(e)}")

@app.get("/api/pipeline/report")
def get_pipeline_report():
    """Returns the performance report summary of the data processing pipeline."""
    try:
        report = repository.get_pipeline_report()
        if report is None:
            return {"status": "FAILED", "message": "Pipeline has not run or no dataset was loaded."}
        return report.model_dump()
    except Exception as e:
        logger.error(f"Error fetching pipeline report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pipeline report: {str(e)}")

# BI Dashboard, Compare & Export Models
class BIDashboardRequest(BaseModel):
    filters: Dict[str, Any]

class BICompareRequest(BaseModel):
    entity_type: str
    entity_a: str
    entity_b: str
    filters: Dict[str, Any]

class BIExportRequest(BaseModel):
    filters: Dict[str, Any]
    report_type: str

class GeospatialNetworkRequest(BaseModel):
    filters: Dict[str, Any]

class RouteAnalysisRequest(BaseModel):
    filters: Dict[str, Any]

class PerformanceRequest(BaseModel):
    filters: Dict[str, Any]

class CostAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class TransitAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class InventoryAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class CapacityAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class SLAAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class GraphAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class GeospatialAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class ShortestPathAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]

class CircularSupplyChainRequest(BaseModel):
    filters: Dict[str, Any]

class RouteScoringRequest(BaseModel):
    filters: Dict[str, Any]

class OptimizationReadinessRequest(BaseModel):
    filters: Dict[str, Any]

class AStarAnalyticsRequest(BaseModel):
    filters: Dict[str, Any]
    heuristic_type: Optional[str] = "great-circle"

class GeneticAlgorithmRequest(BaseModel):
    source: str
    destination: str
    filters: Dict[str, Any]
    population_size: Optional[int] = 30
    generations: Optional[int] = 20

class AntColonyRequest(BaseModel):
    source: str
    destination: str
    filters: Dict[str, Any]
    swarm_size: Optional[int] = 15
    iterations: Optional[int] = 10

class RLPreparationRequest(BaseModel):
    source: str
    destination: str
    filters: Dict[str, Any]

class AIDecisionRequest(BaseModel):
    source: str
    destination: str
    filters: Dict[str, Any]

# Explorer API Models & Endpoints
class QueryFilter(BaseModel):
    column: str
    operator: str
    value: Any

class QueryPayload(BaseModel):
    page: int = 1
    page_size: int = 10
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    search_query: Optional[str] = None
    filters: Optional[List[QueryFilter]] = None

@app.get("/api/explorer/datasets")
def list_explorer_datasets():
    """Lists available datasets in repository, excluding raw transactions sheet."""
    try:
        sheets = repository.list_available_sheets()
        # Exclude raw transactions sheet as requested
        filtered_sheets = [s for s in sheets if s not in ["Logistics_Transactions", "Logistics Transactions"]]
        return filtered_sheets
    except Exception as e:
        logger.error(f"Explorer API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/explorer/summary/{dataset_name}")
def get_dataset_summary(dataset_name: str):
    """Returns catalog metadata details for a sheet."""
    try:
        if not repository.sheet_exists(dataset_name):
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Fetch processed sheet if available
        df = repository._processed_sheets.get(dataset_name)
        if df is None:
            df = repository._sheets[dataset_name]
            
        state = state_manager.get_state()
        
        return {
            "dataset_name": dataset_name,
            "rows": len(df),
            "columns": len(df.columns),
            "memory_usage": ExplorerService.get_memory_usage(df),
            "last_loaded": state.last_load_time,
            "validation_status": "VALID" if state.validation_passed else "INVALID",
            "processing_status": "PROCESSED" if dataset_name in repository._processed_sheets else "RAW"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explorer API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/explorer/columns/{dataset_name}")
def get_dataset_columns(dataset_name: str):
    """Returns list of column names and type hints for a sheet."""
    try:
        if not repository.sheet_exists(dataset_name):
            raise HTTPException(status_code=404, detail="Dataset not found")
            
        df = repository._processed_sheets.get(dataset_name)
        if df is None:
            df = repository._sheets[dataset_name]
            
        columns_info = []
        for col in df.columns:
            # Simple type category detection
            series = df[col]
            if pd.api.types.is_datetime64_any_dtype(series):
                col_type = "datetime"
            elif pd.api.types.is_bool_dtype(series):
                col_type = "boolean"
            elif pd.api.types.is_numeric_dtype(series):
                col_type = "numeric"
            else:
                col_type = "text"
            columns_info.append({"name": col, "type": col_type})
            
        return columns_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explorer API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _resolve_sheet_key(dataset_name: str) -> str:
    """Resolves dataset sheet name handling spaces, underscores, and case mismatches."""
    if repository.sheet_exists(dataset_name):
        return dataset_name
    alt = dataset_name.replace(" ", "_")
    if repository.sheet_exists(alt):
        return alt
    alt2 = dataset_name.replace("_", " ")
    if repository.sheet_exists(alt2):
        return alt2
    norm_name = dataset_name.lower().replace(" ", "_")
    for sheet_name in (repository._sheets or {}).keys():
        if sheet_name.lower().replace(" ", "_") == norm_name:
            return sheet_name
    return dataset_name

@app.get("/api/explorer/column-profile/{dataset_name}/{column}")
def get_column_profile(dataset_name: str, column: str):
    """Profiles a single column of a dataset."""
    try:
        sheet_key = _resolve_sheet_key(dataset_name)
        if not repository.sheet_exists(sheet_key):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")
            
        df = repository._processed_sheets.get(sheet_key)
        if df is None:
            df = repository._sheets[sheet_key]
            
        if column not in df.columns:
            raise HTTPException(status_code=404, detail=f"Column '{column}' not found")
            
        profile = ExplorerService.profile_column(df, column)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explorer API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explorer/query/{dataset_name}")
def query_dataset(dataset_name: str, payload: QueryPayload):
    """Queries, filters, searches, and paginates a dataset, returning JSON-safe rows."""
    try:
        sheet_key = _resolve_sheet_key(dataset_name)
        if not repository.sheet_exists(sheet_key):
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")
            
        df = repository._processed_sheets.get(sheet_key)
        if df is None:
            df = repository._sheets[sheet_key]
            
        # Parse filters from model
        filters_list = []
        if payload.filters:
            for f in payload.filters:
                filters_list.append({
                    "column": f.column,
                    "operator": f.operator,
                    "value": f.value
                })
                
        # Perform query
        paginated_df, total_records = ExplorerService.query_dataframe(
            df=df,
            page=payload.page,
            page_size=payload.page_size,
            sort_by=payload.sort_by,
            sort_order=payload.sort_order,
            search_query=payload.search_query,
            filters=filters_list
        )
        
        # Prepare for JSON serialization: format dates, replace NaN/NaT
        serialized_df = paginated_df.copy()
        for col in serialized_df.columns:
            if pd.api.types.is_datetime64_any_dtype(serialized_df[col]):
                # Fill missing dates first to avoid pandas warning
                serialized_df[col] = serialized_df[col].fillna(pd.Timestamp("1970-01-01"))
                serialized_df[col] = serialized_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                
        # Replace NaN with None
        serialized_df = serialized_df.where(pd.notnull(serialized_df), None)
        records = serialized_df.to_dict(orient="records")
        
        logger.info(f"Explorer Query: Dataset='{sheet_key}' (raw '{dataset_name}'), Page={payload.page}, Filters={len(filters_list)}, Results={len(records)}")
        
        return {
            "records": records,
            "total_records": total_records,
            "page": payload.page,
            "page_size": payload.page_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explorer API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard")
def get_executive_dashboard():
    """Returns calculated KPIs, summaries, distributions, and time series data for the dashboard."""
    try:
        payload = AnalyticsService.get_dashboard_payload()
        logger.info("Executive Dashboard Loaded API triggered successfully.")
        return payload
    except Exception as e:
        logger.error(f"Analytics API Error: Failed loading dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bi/dashboard")
def get_bi_dashboard(payload: BIDashboardRequest):
    """Returns dynamically filtered executive dashboard metrics."""
    try:
        data = BIService.get_dashboard_payload(payload.filters)
        logger.info("Filter Applied event logged via API.")
        return data
    except Exception as e:
        logger.error(f"BI API Error: Failed retrieving dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bi/compare")
def compare_bi_entities(payload: BICompareRequest):
    """Computes side-by-side comparison matrix for two logistics entities."""
    try:
        data = BIService.compare_entities(payload.entity_type, payload.entity_a, payload.entity_b, payload.filters)
        return data
    except Exception as e:
        logger.error(f"BI API Error: Failed comparing entities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bi/export")
def export_bi_report(payload: BIExportRequest):
    """Generates downloadable CSV reports for transactions or KPI summary."""
    try:
        csv_data = BIService.generate_csv_report(payload.filters, payload.report_type)
        logger.info("Export Created event logged via API.")
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={payload.report_type}_report.csv"}
        )
    except Exception as e:
        logger.error(f"BI API Error: Failed exporting CSV report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/geospatial/network")
def get_geospatial_network(payload: GeospatialNetworkRequest):
    """Returns dynamically filtered hubs, RCs, shipment flows, and summary KPIs for the map."""
    try:
        data = GeospatialService.get_network_payload(payload.filters)
        logger.info("Map Loaded event logged via API.")
        return data
    except Exception as e:
        logger.error(f"Geospatial API Error: Failed retrieving map network payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/geospatial-network/payload")
def get_geospatial_network_payload(payload: Dict[str, Any] = None):
    """Fallback endpoint for legacy route-recommendation, cost-optimization, and corridor intelligence."""
    params = payload if payload else {}
    filters = params.get("filters", {})
    try:
        net_data = GeospatialService.get_network_payload(filters)
        
        # Build nodes list
        nodes = []
        for h in net_data.get("hubs", []):
            nodes.append({
                "id": h.get("id"),
                "name": h.get("name"),
                "latitude": h.get("lat"),
                "longitude": h.get("lon"),
                "city": h.get("city"),
                "state": h.get("state"),
                "region": h.get("region"),
                "type": h.get("type")
            })
        for rc in net_data.get("repair_centers", []):
            nodes.append({
                "id": rc.get("id"),
                "name": rc.get("name"),
                "latitude": rc.get("lat"),
                "longitude": rc.get("lon"),
                "city": rc.get("city"),
                "state": rc.get("state"),
                "region": rc.get("region"),
                "type": rc.get("type")
            })
            
        # Build routes list
        routes = []
        for f in net_data.get("flows", []):
            orig = f.get("origin_id") or f.get("origin")
            dest = f.get("destination_id") or f.get("destination")
            corr = f.get("corridor") or (f"{orig} → {dest}" if orig and dest else None)
            routes.append({
                "origin": orig,
                "destination": dest,
                "corridor": corr,
                "origin_lat": f.get("origin_lat"),
                "origin_lon": f.get("origin_lon"),
                "dest_lat": f.get("dest_lat"),
                "dest_lon": f.get("dest_lon"),
                "shipment_count": f.get("shipment_count"),
                "avg_transit_time": f.get("avg_transit_time"),
                "avg_cost": f.get("avg_cost"),
                "flow_type": f.get("flow_type")
            })
            
        return {
            "status": "success",
            "nodes": nodes,
            "routes": routes
        }
    except Exception as e:
        logger.error(f"Geospatial Network Payload API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/route-analysis/payload")
def get_route_analysis_payload(payload: RouteAnalysisRequest):
    """Returns dynamically analyzed route metrics, bottlenecks, and graph data."""
    try:
        data = RouteAnalysisService.get_route_analysis_payload(payload.filters)
        return data
    except Exception as e:
        logger.error(f"Route Analysis API Error: Failed retrieving route intelligence payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/performance/payload")
def get_performance_payload(payload: PerformanceRequest):
    """Returns dynamically analyzed logistics KPIs, node scorecards, delay/cost summaries, and trend data."""
    try:
        data = PerformanceService.get_performance_payload(payload.filters)
        return data
    except Exception as e:
        logger.error(f"Performance Monitoring API Error: Failed retrieving performance payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost-analytics/payload")
def get_cost_analytics_payload(payload: CostAnalyticsRequest):
    """Returns comprehensive cost analytics: overview metrics, breakdowns, variance, rankings, and trends."""
    try:
        data = CostEngine.get_cost_analytics(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Cost Analytics API Error: Failed retrieving cost analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transit-analytics/payload")
def get_transit_analytics_payload(payload: TransitAnalyticsRequest):
    """Returns comprehensive transit analytics: overview, distribution, rankings, trends, and outliers."""
    try:
        data = TransitEngine.get_transit_analytics(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Transit Analytics API Error: Failed retrieving transit analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inventory-analytics/payload")
def get_inventory_analytics_payload(payload: InventoryAnalyticsRequest):
    """Returns comprehensive inventory analytics: overview, movement, stock levels, utilization, rankings, and outliers."""
    try:
        data = InventoryEngine.get_inventory_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Inventory Analytics API Error: Failed retrieving inventory analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/capacity-analytics/payload")
def get_capacity_analytics_payload(payload: CapacityAnalyticsRequest):
    """Returns comprehensive capacity analytics: overview, hubs analysis, repair centers analysis, regional capacity breakdowns, bottlenecks, and trends."""
    try:
        data = CapacityEngine.get_capacity_analytics(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Capacity Analytics API Error: Failed retrieving capacity analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-analytics/payload")
def get_sla_analytics_payload(payload: SLAAnalyticsRequest):
    """Returns comprehensive SLA compliance analytics: overview metrics, breakdowns, violations list, rankings, and trends."""
    try:
        data = SLAEngine.get_sla_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"SLA Analytics API Error: Failed retrieving SLA analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/circular-supply-chain/payload")
def get_circular_supply_chain_payload(payload: CircularSupplyChainRequest):
    """Returns AI Circular Supply Chain Optimizer payload: lifecycle decisions, redeployments, harvesting, recycling, and carbon metrics."""
    try:
        data = CircularSupplyChainService.get_circular_supply_chain_payload(payload.filters)
        return data
    except Exception as e:
        logger.error(f"Circular Supply Chain API Error: Failed retrieving payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/circular-supply-chain/export-csv")
def export_circular_supply_chain_csv(payload: CircularSupplyChainRequest):
    """Generates CSV download for circular supply chain predictive redeployment intelligence."""
    try:
        data = CircularSupplyChainService.get_circular_supply_chain_payload(payload.filters)
        redeployments = data.get("redeployments", [])
        df = pd.DataFrame(redeployments)
        csv_content = df.to_csv(index=False)
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=Circular_Supply_Chain_Redeployments.csv"})
    except Exception as e:
        logger.error(f"Circular Supply Chain Export Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graph-analytics/payload")
def get_graph_analytics_payload(payload: GraphAnalyticsRequest):
    """Returns comprehensive route graph analytics: nodes, edges, adjacency list, matrix weights, connectivity metrics, and stats."""
    import math
    try:
        data = GraphEngine.get_graph_payload(payload.filters)
        # Sanitize adjacency_matrix: replace any residual inf/nan with -1.0 for JSON safety
        raw = data.model_dump()
        if isinstance(raw.get('adjacency_matrix'), dict):
            for src in raw['adjacency_matrix']:
                for dst in raw['adjacency_matrix'][src]:
                    v = raw['adjacency_matrix'][src][dst]
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        raw['adjacency_matrix'][src][dst] = -1.0
        return raw
    except Exception as e:
        logger.error(f"Graph Analytics API Error: Failed retrieving graph analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/geospatial-analytics/payload")
def get_geospatial_analytics_payload(payload: GeospatialAnalyticsRequest):
    """Returns comprehensive geographical intelligence payload: haversine distance matrices, nearest mapping arrays, clustering, and coverage indicators."""
    try:
        data = GeospatialEngine.get_geospatial_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Geospatial Analytics API Error: Failed retrieving geospatial analytics payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shortest-path-analytics/payload")
def get_shortest_path_payload(payload: ShortestPathAnalyticsRequest):
    """Returns comprehensive shortest path routing calculations: Dijkstra shortest distances/costs/transit times, BFS hops path results, accessibility list, and traversal benchmarks."""
    try:
        data = ShortestPathEngine.get_shortest_path_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Shortest Path Analytics API Error: Failed retrieving shortest path payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/route-scoring/payload")
def get_route_scoring_payload(payload: RouteScoringRequest):
    """Returns comprehensive route scoring analytics: cost ratings, speed scores, utilization index, SLA scores, overall route score, rankings, comparisons, and business insights."""
    try:
        data = RouteScoringEngine.get_route_scoring_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Route Scoring API Error: Failed retrieving route scoring payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimization-readiness/payload")
def get_optimization_readiness_payload(payload: OptimizationReadinessRequest):
    """Returns comprehensive network optimization readiness payload: indexed nodes, weighted edges, 2D dense distance/cost/transit matrices, validation warning lists, and baseline totals."""
    try:
        data = OptimizationReadinessEngine.get_readiness_payload(payload.filters)
        return data.model_dump()
    except Exception as e:
        logger.error(f"Optimization Readiness API Error: Failed retrieving readiness payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/astar-pathfinding/payload")
def get_astar_payload(payload: AStarAnalyticsRequest):
    """Returns comprehensive A* optimal routes: optimal paths nested by source/destination, heuristic performance comparison profiles, and search statistics."""
    try:
        data = AStarEngine.get_astar_payload(payload.filters, payload.heuristic_type)
        return data.model_dump()
    except Exception as e:
        logger.error(f"A* Pathfinding API Error: Failed retrieving A* payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/genetic-algorithm/optimize")
def get_genetic_optimization(payload: GeneticAlgorithmRequest):
    """Returns comprehensive Genetic Algorithm optimized routes: optimal route chromosome, best fitness over generations, and execution stats."""
    try:
        data = GeneticAlgorithmEngine.optimize_route(
            payload.source, payload.destination, payload.filters, payload.population_size, payload.generations
        )
        return data.model_dump()
    except Exception as e:
        logger.error(f"Genetic Algorithm API Error: Failed retrieving optimized route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ant-colony/optimize")
def get_aco_optimization(payload: AntColonyRequest):
    """Returns comprehensive Ant Colony Optimization optimized routes: best ant route, iteration stats, final pheromone matrix, and algorithm benchmarks."""
    try:
        data = AntColonyEngine.optimize_route(
            payload.source, payload.destination, payload.filters, payload.swarm_size, payload.iterations
        )
        return data.model_dump()
    except Exception as e:
        logger.error(f"Ant Colony Optimization API Error: Failed retrieving optimized route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rl-preparation/environment")
def get_rl_environment(payload: RLPreparationRequest):
    """Returns comprehensive RL prepared environments: state/action definitions, reward configurations, sample bootstrap episodes, and algorithm benchmarks."""
    try:
        data = RLPreparationEngine.generate_environment(
            payload.source, payload.destination, payload.filters
        )
        return data.model_dump()
    except Exception as e:
        logger.error(f"RL Preparation API Error: Failed retrieving environment setup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-preparation/decision-support")
def get_ai_decision_support(payload: AIDecisionRequest):
    """Returns comprehensive AI decision support contexts: feature matrices, scenario recommendation candidates, and explainability summaries."""
    try:
        data = AIPreparationEngine.prepare_decision_support(
            payload.source, payload.destination, payload.filters
        )
        return data.model_dump()
    except Exception as e:
        logger.error(f"AI Preparation API Error: Failed retrieving decision context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/corridor-intelligence/payload")
def get_corridor_intelligence_payload(payload: Dict[str, Any] = None):
    """Returns comprehensive corridor efficiency analytics, normalized scores, and AI recommendations."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = CorridorService.get_corridor_intelligence(filters)
        return data
    except Exception as e:
        logger.error(f"Corridor Intelligence API Error: Failed retrieving corridor data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/route-decision-engine/evaluate")
def evaluate_route_decision_engine(payload: Dict[str, Any] = None):
    """Evaluates all network corridors using the central AI Route Decision Engine."""
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet)
        
        data = RouteDecisionEngine.evaluate_all_corridors(df_tx, df_hub, df_tpr)
        return data
    except Exception as e:
        logger.error(f"Route Decision Engine API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimization-simulator/run")
def run_optimization_simulator(payload: Dict[str, Any] = None):
    """Runs real-time optimization simulation for a specific corridor."""
    corridor_id = payload.get("corridor_id") if payload else "HUB-A → HUB-B"
    try:
        data = RouteDecisionEngine.simulate_corridor_optimization(corridor_id, payload)
        return data
    except Exception as e:
        logger.error(f"Optimization Simulator API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/corridor-drilldown/details")
def get_corridor_drilldown_details(payload: Dict[str, Any] = None):
    """Returns interactive enterprise detail payload for a specific corridor."""
    corridor_id = payload.get("corridor_id") if payload else "HUB-A → HUB-B"
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet)
        
        res = RouteDecisionEngine.evaluate_all_corridors(df_tx, df_hub, df_tpr)
        corridors = res.get("corridors", [])
        
        target = None
        for c in corridors:
            if c["corridor_id"] == corridor_id or c["corridor"] == corridor_id:
                target = c
                break
        if not target and corridors:
            target = corridors[0]
            
        return {
            "corridor": target,
            "decision_summary": res.get("executive_ai_insights", []),
            "predictions": res.get("predictions", {})
        }
    except Exception as e:
        logger.error(f"Corridor DrillDown API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/intelligent-routing/recommend", methods=["GET", "POST"])
@app.api_route("/api/intelligent-routing/recommend/", methods=["GET", "POST"])
@app.api_route("/api/route-recommendation/recommend", methods=["GET", "POST"])
def get_intelligent_route_recommendation(payload: Dict[str, Any] = None):
    """Evaluates a shipment request using the Dell 4-Step Decision Tree and 10-dimension ranking engine."""
    params = payload if payload else {}
    try:
        data = IntelligentRoutingEngine.evaluate_shipment_request(params)
        return data
    except Exception as e:
        logger.error(f"Intelligent Routing API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/intelligent-routing/simulate", methods=["GET", "POST"])
@app.api_route("/api/intelligent-routing/simulate/", methods=["GET", "POST"])
def simulate_intelligent_route_what_if(payload: Dict[str, Any] = None):
    """Simulates What-If scenario parameter overrides for an intelligent shipment route."""
    params = payload if payload else {}
    base_params = params.get("base_params", {})
    overrides = params.get("overrides", {})
    try:
        data = IntelligentRoutingEngine.simulate_what_if_scenario(base_params, overrides)
        return data
    except Exception as e:
        logger.error(f"Intelligent Routing Simulator API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/intelligent-routing/scenarios", methods=["GET", "POST"])
@app.api_route("/api/intelligent-routing/scenarios/", methods=["GET", "POST"])
def get_intelligent_route_scenarios(payload: Dict[str, Any] = None):
    """Generates a 6-scenario side-by-side comparative analysis across optimization goals."""
    base_params = payload if payload else {}
    try:
        data = IntelligentRoutingEngine.generate_scenario_comparison(base_params)
        return data
    except Exception as e:
        logger.error(f"Intelligent Routing Scenarios API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost-optimization/payload")
def get_cost_optimization_payload(payload: Dict[str, Any] = None):
    """Returns enterprise cost optimization evaluation, suboptimal route analysis, and 13-dimension savings."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = CostOptimizationEngine.evaluate_network_cost_optimization(filters)
        return data
    except Exception as e:
        logger.error(f"Cost Optimization Payload API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost-optimization/simulate")
def run_cost_simulation(payload: Dict[str, Any] = None):
    """Runs 10-lever What-If operational cost simulations and returns baseline comparisons and recommendations."""
    filters = payload.get("filters", {}) if payload else {}
    scenarios = payload.get("scenarios", {}) if payload else {}
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        df_hub = repository._processed_sheets.get("Hub_Location_Master")
        tpr_sheet = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet)
        
        data = CostOptimizationEngine.run_what_if_simulation(df_tx, df_hub, df_tpr, scenarios)
        return data
    except Exception as e:
        logger.error(f"Cost Simulation API Error: Failed running simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost-optimization/export")
def export_cost_report(payload: Dict[str, Any] = None):
    """Generates PDF, Excel, or CSV executive cost optimization reports."""
    format_str = payload.get("format", "pdf") if payload else "pdf"
    try:
        data = CostOptimizationEngine.export_cost_optimization_report(format_str)
        return data
    except Exception as e:
        logger.error(f"Cost Optimization Export API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-logistics/payload")
def get_reverse_logistics_payload(payload: Dict[str, Any] = None):
    """Returns comprehensive reverse logistics intelligence payload."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = ReverseLogisticsService.get_reverse_logistics(filters)
        return data
    except Exception as e:
        logger.error(f"Reverse Logistics API Error: Failed retrieving returns payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-logistics/recommend-tpr")
def recommend_tpr_for_shipment(payload: Dict[str, Any] = None):
    """Ranks top 5 candidate repair centers for a reverse shipment."""
    shipment_data = payload if payload else {}
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        tpr_sheet = "TPR_Master" if repository.sheet_exists("TPR_Master") else "Repair_Center_Master"
        df_tpr = repository._processed_sheets.get(tpr_sheet)
        data = ReverseLogisticsEngine.recommend_best_tpr_for_shipment(shipment_data, df_tpr, df_tx)
        return data
    except Exception as e:
        logger.error(f"Recommend TPR API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-logistics/consolidation")
def get_reverse_consolidation_opportunities(payload: Dict[str, Any] = None):
    """Identifies reverse shipment batching opportunities and freight savings."""
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        data = ReverseLogisticsEngine.detect_shipment_consolidation(df_tx)
        return data
    except Exception as e:
        logger.error(f"Reverse Consolidation API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-logistics/tpr-drilldown")
def get_tpr_drilldown_data(payload: Dict[str, Any] = None):
    """Returns detailed capacity, queue, and recommendation payload for a specific TPR."""
    tpr_id = payload.get("tpr_id", "TPR-BLR-01") if payload else "TPR-BLR-01"
    try:
        data = ReverseLogisticsEngine.get_tpr_drilldown_details(tpr_id)
        return data
    except Exception as e:
        logger.error(f"TPR Drilldown API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-logistics/export")
def export_reverse_logistics_report(payload: Dict[str, Any] = None):
    """Generates PDF, Excel, or CSV executive reverse logistics reports."""
    format_str = payload.get("format", "pdf") if payload else "pdf"
    try:
        data = ReverseLogisticsEngine.export_reverse_logistics_report(format_str)
        return data
    except Exception as e:
        logger.error(f"Reverse Logistics Export API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-prediction/payload")
def get_sla_prediction_payload(payload: Dict[str, Any] = None):
    """Returns SLA breach predictions, ML model evaluation metrics, risk scores, and AI recommendations."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = SLAPredictionService.get_prediction_payload(filters)
        return data
    except Exception as e:
        logger.error(f"SLA Prediction API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-prediction/predict")
def predict_shipment_sla_breach(payload: Dict[str, Any] = None):
    """Predicts SLA breach probability and Explainable AI feature attributions for a shipment."""
    shipment_data = payload if payload else {}
    try:
        data = SLAPredictionEngine.predict_shipment_sla_breach(shipment_data)
        return data
    except Exception as e:
        logger.error(f"SLA Predict API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-prediction/evaluate-models")
def evaluate_ml_models(payload: Dict[str, Any] = None):
    """Returns evaluation metrics across Decision Tree, Random Forest, Logistic Regression, and XGBoost."""
    try:
        df_tx = repository._processed_sheets.get("Logistics_Transactions")
        data = SLAPredictionEngine.preprocess_and_train_models(df_tx)
        return data
    except Exception as e:
        logger.error(f"SLA Model Evaluation API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-prediction/export")
def export_sla_report(payload: Dict[str, Any] = None):
    """Generates PDF, Excel, or CSV executive SLA prediction and risk reports."""
    format_str = payload.get("format", "pdf") if payload else "pdf"
    try:
        data = SLAPredictionEngine.export_sla_prediction_report(format_str)
        return data
    except Exception as e:
        logger.error(f"SLA Report Export API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sla-prediction/forecast")
def get_risk_forecast_payload(payload: Dict[str, Any] = None):
    """Returns 7-day rolling risk timeline and corridor forecasts."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = RiskForecastingService.get_forecast_payload(filters)
        return data
    except Exception as e:
        logger.error(f"SLA Forecast API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executive-reporting/payload")
def get_executive_reporting_payload(payload: Dict[str, Any] = None):
    """Returns unified executive reporting, AI narrative, decision support, and KPI payload."""
    filters = payload.get("filters", {}) if payload else {}
    try:
        data = ExecutiveReportingEngine.evaluate_executive_reporting_platform(filters)
        return data
    except Exception as e:
        logger.error(f"Executive Reporting Payload API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executive-reporting/decision-support")
def get_prioritized_decision_support(payload: Dict[str, Any] = None):
    """Returns prioritized high-ROI operational recommendations with detailed evidence and payback metrics."""
    try:
        data = ExecutiveReportingEngine.generate_prioritized_decision_support()
        return data
    except Exception as e:
        logger.error(f"Decision Support API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executive-reporting/smart-alerts")
def get_smart_alerts(payload: Dict[str, Any] = None):
    """Returns smart alerts categorized by Critical, High, Medium, and Low severity."""
    try:
        data = ExecutiveReportingEngine.generate_smart_alerts()
        return data
    except Exception as e:
        logger.error(f"Smart Alerts API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executive-reporting/export")
def export_executive_report(payload: Dict[str, Any] = None):
    """Generates PDF, Excel, or CSV executive decision support reports."""
    format_str = payload.get("format", "pdf") if payload else "pdf"
    try:
        data = ExecutiveReportingEngine.export_executive_report(format_str)
        return data
    except Exception as e:
        logger.error(f"Executive Report Export API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/security/audit-trail")
def search_audit_trail(payload: Dict[str, Any] = None):
    """Returns searchable audit history logs."""
    user_id = payload.get("user_id") if payload else None
    module = payload.get("module") if payload else None
    action = payload.get("action") if payload else None
    try:
        data = AuditTrailEngine.search_audit_trail(user_id=user_id, module=module, action=action)
        return data
    except Exception as e:
        logger.error(f"Audit Trail API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/monitoring/health-status")
def get_system_health():
    """Returns real-time system health status across all components."""
    try:
        data = HealthMonitoringEngine.get_system_health_status()
        return data
    except Exception as e:
        logger.error(f"Health Status API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/monitoring/diagnostics")
def get_system_diagnostics():
    """Returns full system environment diagnostics."""
    try:
        data = HealthMonitoringEngine.get_system_diagnostics()
        return data
    except Exception as e:
        logger.error(f"System Diagnostics API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notifications/center")
def get_notification_center(payload: Dict[str, Any] = None):
    """Returns system notification center alerts."""
    try:
        data = NotificationBackupManager.get_notification_center()
        return data
    except Exception as e:
        logger.error(f"Notification Center API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/backups/manage")
def manage_backups(payload: Dict[str, Any] = None):
    """Creates or lists system backup snapshots."""
    action = payload.get("action", "list") if payload else "list"
    try:
        if action == "create":
            data = NotificationBackupManager.create_backup_snapshot()
        else:
            data = NotificationBackupManager.list_backups()
        return data
    except Exception as e:
        logger.error(f"Backups API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/info")
def get_system_info():
    """Returns System Release Metadata and System Status."""
    return SystemInfoService.get_system_info()

@app.get("/api/v1/system/build")
def get_system_build():
    """Returns System Build Information."""
    return SystemInfoService.get_system_info()

@app.get("/api/v1/system/release-notes")
def get_release_notes():
    """Returns Release Notes for Version 1.0.0."""
    return SystemInfoService.get_release_notes()

@app.post("/api/v1/demo/reset")
def reset_demo_environment():
    """Resets the demo dataset environment for evaluation judges."""
    return SystemInfoService.reset_demo_environment()

@app.get("/api/v1/performance/metrics")
def get_performance_metrics():
    """Returns real-time performance, latency, memory, and cache metrics."""
    return PerformanceOptimizationEngine.get_performance_metrics()

@app.post("/api/v1/performance/cache-manage")
def manage_performance_cache(payload: Dict[str, Any] = None):
    """Manages cache invalidation, flushing, and statistics."""
    action = payload.get("action", "stats") if payload else "stats"
    key = payload.get("key") if payload else None
    return PerformanceOptimizationEngine.manage_cache(action=action, key=key)

@app.post("/api/v1/performance/benchmark")
def generate_performance_benchmark():
    """Generates an automated system performance benchmark report."""
    return PerformanceOptimizationEngine.generate_performance_benchmark()

@app.get("/api/v1/performance/background-jobs")
def get_background_jobs():
    """Lists active and completed background job tasks."""
    return PerformanceOptimizationEngine.get_background_jobs()

@app.get("/api/v1/ai/model-registry")
def get_ai_model_registry():
    """Returns active AI model registry catalog and deployment status."""
    return AIModelLifecycleManager.get_model_registry()

@app.post("/api/v1/ai/model-retrain")
def trigger_ai_model_retraining(payload: Dict[str, Any] = None):
    """Triggers automated retraining workflow on latest logistics dataset."""
    domain = payload.get("domain", "SLA Prediction") if payload else "SLA Prediction"
    return AIModelLifecycleManager.trigger_model_retraining(domain=domain)

@app.get("/api/v1/ai/drift-detection")
def detect_ai_drift():
    """Returns continuous data and model drift detection report."""
    return AIModelLifecycleManager.detect_data_and_model_drift()

@app.post("/api/v1/ai/ab-test")
def evaluate_ai_ab_test():
    """Evaluates candidate model performance in shadow mode against production model."""
    return AIModelLifecycleManager.evaluate_ab_shadow_deployment()

@app.get("/api/v1/ai/feature-store")
def get_ai_feature_store():
    """Returns reusable feature store catalog across training and inference."""
    return AIModelLifecycleManager.get_feature_store_catalog()

@app.post("/api/v1/ai/governance/approve")
def approve_ai_model(payload: Dict[str, Any] = None):
    """Approves a model version for production deployment."""
    model_id = payload.get("model_id", "MOD-SLA-RF-01") if payload else "MOD-SLA-RF-01"
    approved_by = payload.get("approved_by", "Admin") if payload else "Admin"
    return AIModelLifecycleManager.approve_model(model_id=model_id, approved_by=approved_by)

@app.post("/api/v1/ai/governance/rollback")
def rollback_ai_model(payload: Dict[str, Any] = None):
    """Rolls back production model to previous stable version."""
    domain = payload.get("domain", "SLA Prediction") if payload else "SLA Prediction"
    return AIModelLifecycleManager.rollback_model_version(domain=domain)

@app.post("/api/v1/validation/run")
def run_enterprise_validation(payload: Dict[str, Any] = None):
    """Runs full enterprise validation & certification suite."""
    filters = payload.get("filters", {}) if payload else {}
    return EnterpriseValidationEngine.evaluate_enterprise_validation_platform(filters)

@app.get("/api/v1/validation/dell-dataset-certification")
def get_dell_dataset_certification():
    """Returns official Dell dataset certification audit details."""
    res = EnterpriseValidationEngine.evaluate_enterprise_validation_platform()
    return res["dataset_certification"]

@app.get("/api/v1/validation/workflow-status")
def get_workflow_validation_status():
    """Returns 12-step end-to-end workflow execution status."""
    return EnterpriseValidationEngine.validate_end_to_end_workflows()

@app.get("/api/v1/validation/compliance-score")
def get_compliance_score():
    """Returns 100% enterprise compliance score & module acceptance matrix."""
    return EnterpriseValidationEngine.calculate_compliance_score()

@app.post("/api/v1/validation/export")
def export_validation_report(payload: Dict[str, Any] = None):
    """Generates PDF, Excel, or CSV enterprise certification report."""
    format_str = payload.get("format", "pdf") if payload else "pdf"
    return EnterpriseValidationEngine.export_validation_report(format_str)

@app.get("/api/orchestrator/dashboard")
def get_orchestrator_dashboard():
    """Returns metadata for the AI Orchestrator workspace dashboard."""
    try:
        data = WorkflowEngine.get_dashboard_payload()
        return data
    except Exception as e:
        logger.error(f"Orchestrator Dashboard API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orchestrator/run")
def run_orchestrator_workflow(payload: Dict[str, Any] = None):
    """Executes multi-agent orchestrator workflows, aggregates data, and resolves conflict recommendations."""
    params = payload if payload else {}
    try:
        data = WorkflowEngine.run_optimization_workflow(params)
        return data
    except Exception as e:
        logger.error(f"Orchestrator Run API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/history")
def get_reports_history():
    """Returns log of previous report generation history."""
    try:
        data = ReportGenerator.get_history()
        return data
    except Exception as e:
        logger.error(f"Reports History API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/generate")
def compile_report_payload(payload: Dict[str, Any] = None):
    """Generates executive report based on template type and user parameters."""
    params = payload if payload else {}
    report_type = params.get("report_type", "Executive Summary")
    template = params.get("template", "Executive Leadership")
    generated_by = params.get("generated_by", "analyst")
    filters = params.get("filters", {})
    try:
        data = ReportGenerator.compile_report(report_type, template, generated_by, filters)
        return data
    except Exception as e:
        logger.error(f"Reports Generation API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

SYSTEM_CONFIG = {
    "optimization_mode": "dijkstra",
    "log_level": "info",
    "security_level": "strict",
    "cache_timeout": "5.0"
}

@app.get("/api/admin/config")
def get_admin_config():
    """Returns current active system configuration parameters."""
    return SYSTEM_CONFIG

@app.post("/api/admin/config")
def update_admin_config(payload: Dict[str, Any] = None):
    """Updates active system configuration parameters and clears service caches."""
    global SYSTEM_CONFIG
    params = payload if payload else {}
    if "optimization_mode" in params:
        SYSTEM_CONFIG["optimization_mode"] = str(params["optimization_mode"]).lower()
    if "log_level" in params:
        SYSTEM_CONFIG["log_level"] = str(params["log_level"]).lower()
    if "security_level" in params:
        SYSTEM_CONFIG["security_level"] = str(params["security_level"]).lower()
    if "cache_timeout" in params:
        SYSTEM_CONFIG["cache_timeout"] = str(params["cache_timeout"])

    # Clear in-memory service caches so new algorithm applies immediately
    try:
        from backend.services.capacity_engine import CapacityEngine
        CapacityEngine.clear_cache()
    except Exception:
        pass
    try:
        from backend.services.route_scoring_engine import RouteScoringEngine
        RouteScoringEngine.clear_cache()
    except Exception:
        pass

    logger.info(f"System Configuration updated: {SYSTEM_CONFIG}")
    return {"status": "success", "config": SYSTEM_CONFIG}

@app.post("/api/reports/increment-download")
def increment_report_download(payload: Dict[str, Any] = None):
    """Increments the download counter for a specified archive report entry."""
    params = payload if payload else {}
    report_id = params.get("id")
    try:
        history = ReportGenerator.get_history()
        for rep in history:
            if rep.get("id") == report_id:
                rep["downloads"] = rep.get("downloads", 0) + 1
                return {"status": "success", "id": report_id, "downloads": rep["downloads"]}
        return {"status": "not_found", "id": report_id}
    except Exception as e:
        logger.error(f"Reports Increment Download API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/command-center/payload")
def get_command_center_dashboard():
    """Returns command center operations cockpit consolidated payload."""
    try:
        data = CommandCenterService.get_command_center_payload()
        return data
    except Exception as e:
        logger.error(f"Command Center Dashboard API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/command-center/search")
def run_command_center_search(payload: Dict[str, Any] = None):
    """Searches across all shipments, hubs, and corridors based on query parameter."""
    params = payload if payload else {}
    query = params.get("query", "")
    try:
        data = CommandCenterService.global_search(query)
        return data
    except Exception as e:
        logger.error(f"Command Center Search API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))








@app.post("/api/copilot/message")
def post_copilot_message(payload: Dict[str, Any]):
    """Processes user chat message, compiles structured answer, and updates session history."""
    try:
        message = payload.get("message", "")
        filters = payload.get("filters", {})
        
        # Load context
        context = {
            "filters": filters,
            "last_route": conversation_manager.get_context("last_route")
        }
        
        # Add user prompt to history
        conversation_manager.add_message("user", message)
        
        # Process and calculate structured answer
        response_payload = CopilotService.process_prompt(message, context)
        
        # Store last routed domain in context memory for context-awareness
        conversation_manager.update_context("last_route", response_payload.get("route"))
        
        # Add assistant response to history
        assistant_msg = conversation_manager.add_message("assistant", response_payload.get("summary", ""), response_payload)
        
        return {
            "status": "success",
            "message": assistant_msg
        }
    except Exception as e:
        logger.error(f"Copilot Message API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/api/copilot/history")
def get_copilot_history():
    """Returns full active chat log history."""
    return {
        "status": "success",
        "history": conversation_manager.get_history()
    }

@app.post("/api/copilot/history/clear")
def clear_copilot_history():
    """Clears history logs."""
    conversation_manager.clear()
    return {"status": "success", "message": "History cleared"}

@app.post("/api/copilot/message/pin")
def pin_copilot_message(payload: Dict[str, str]):
    msg_id = payload.get("message_id", "")
    pinned = conversation_manager.toggle_pin(msg_id)
    return {"status": "success", "pinned": pinned}

@app.post("/api/copilot/message/favorite")
def favorite_copilot_message(payload: Dict[str, str]):
    msg_id = payload.get("message_id", "")
    favorite = conversation_manager.toggle_favorite(msg_id)
    return {"status": "success", "favorite": favorite}

@app.get("/api/copilot/history/export")
def export_copilot_history():
    """Returns conversation history in raw JSON format for download/export."""
    return conversation_manager.get_history()

# ─── Serve Static Frontend Files ─────────────────────────────────────────────
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", NoCacheStaticFiles(directory=FRONTEND_DIR), name="static")
    for sub in ["css", "js", "components", "design-system", "utils", "pages"]:
        sub_path = os.path.join(FRONTEND_DIR, sub)
        if os.path.exists(sub_path):
            app.mount(f"/{sub}", NoCacheStaticFiles(directory=sub_path), name=sub)

    # Serve index.html at root
    @app.get("/", include_in_schema=False)
    def serve_root():
        headers = {"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"}
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=headers)

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("v1/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = os.path.join(FRONTEND_DIR, full_path)
        headers = {"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0", "Pragma": "no-cache", "Expires": "0"}
        if os.path.isfile(candidate):
            return FileResponse(candidate, headers=headers)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=headers)
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}. API server running standalone.")

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "status": "running",
            "message": "FastAPI standalone backend is active. Frontend directory missing."
        }

if __name__ == "__main__":
    # Run uvicorn server on port 8000
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
