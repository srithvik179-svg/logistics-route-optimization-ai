import os
import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
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
from backend.config import DEFAULT_DATASET_PATH
from backend.validators.dataset_validator import DatasetValidator

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

# Initialize repository on application startup
@app.on_event("startup")
def startup_event():
    logger.info("Application starting up... Initializing repository.")
    repository.initialize()

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
            
        return {
            "state": state,
            "sheets": sheet_stats,
            "is_initialized": repository.is_initialized()
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
    """Lists available datasets in repository."""
    try:
        return repository.list_available_sheets()
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

@app.get("/api/explorer/column-profile/{dataset_name}/{column}")
def get_column_profile(dataset_name: str, column: str):
    """Profiles a single column of a dataset."""
    try:
        if not repository.sheet_exists(dataset_name):
            raise HTTPException(status_code=404, detail="Dataset not found")
            
        df = repository._processed_sheets.get(dataset_name)
        if df is None:
            df = repository._sheets[dataset_name]
            
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
        if not repository.sheet_exists(dataset_name):
            raise HTTPException(status_code=404, detail="Dataset not found")
            
        df = repository._processed_sheets.get(dataset_name)
        if df is None:
            df = repository._sheets[dataset_name]
            
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
        
        logger.info(f"Explorer Query: Dataset='{dataset_name}', Page={payload.page}, Filters={len(filters_list)}, Results={len(records)}")
        
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

@app.post("/api/graph-analytics/payload")
def get_graph_analytics_payload(payload: GraphAnalyticsRequest):
    """Returns comprehensive route graph analytics: nodes, edges, adjacency list, matrix weights, connectivity metrics, and stats."""
    try:
        data = GraphEngine.get_graph_payload(payload.filters)
        return data.model_dump()
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

# Serve Static Frontend Files
# Path to frontend directory
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    # Mount css/js static files
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    # Serve index.html at root
    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}. API server running standalone.")
    
    @app.get("/")
    def root():
        return {
            "status": "running",
            "message": "FastAPI standalone backend is active. Frontend directory missing."
        }

if __name__ == "__main__":
    # Run uvicorn server on port 8000
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
