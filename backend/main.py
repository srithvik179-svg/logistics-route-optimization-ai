import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional

from backend.config import BASE_DIR
from backend.services.repository import repository
from backend.services.state_manager import state_manager
from backend.utils.logger import logger
from backend.services.dataset_loader import DatasetLoader
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
