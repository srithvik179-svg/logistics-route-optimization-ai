import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional

from backend.config import DEFAULT_DATASET_PATH, BASE_DIR
from backend.models.dataset_model import (
    DatasetMetadata,
    DatasetValidationReport,
    DatasetModel
)
from backend.services.dataset_loader import DatasetLoader
from backend.validators.dataset_validator import DatasetValidator
from backend.utils.logger import logger

app = FastAPI(
    title="Dell Logistics Route Optimization AI Platform",
    description="Backend API for loading and validating route optimization datasets.",
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

# Global in-memory cache for the dataset
_dataset_cache: Optional[DatasetModel] = None

def get_dataset(force_reload: bool = False) -> DatasetModel:
    """Loads and validates the dataset, caching it in memory."""
    global _dataset_cache
    if _dataset_cache is not None and not force_reload:
        return _dataset_cache

    logger.info("Initializing dataset load and validation process...")
    loader = DatasetLoader(DEFAULT_DATASET_PATH)
    
    # Load raw data
    metadata, sheets_data = loader.load()
    
    # Run validation
    validation_report = DatasetValidator.validate(metadata, sheets_data)
    
    # Cache and return
    _dataset_cache = DatasetModel(
        metadata=metadata,
        sheets_data=sheets_data,
        validation_report=validation_report
    )
    return _dataset_cache

# API Endpoints
@app.get("/api/dataset/status")
def get_dataset_status():
    """Returns the current dataset status, metadata, and validation report."""
    try:
        ds = get_dataset()
        # Serialize validation report and metadata
        return {
            "metadata": ds.metadata.model_dump(),
            "validation_report": ds.validation_report.model_dump() if ds.validation_report else None
        }
    except Exception as e:
        logger.error(f"Error retrieving dataset status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/api/dataset/reload")
def reload_dataset():
    """Forces a reload and re-validation of the dataset from disk."""
    try:
        ds = get_dataset(force_reload=True)
        return {
            "status": "success",
            "message": "Dataset reloaded and validated successfully.",
            "metadata": ds.metadata.model_dump(),
            "validation_report": ds.validation_report.model_dump() if ds.validation_report else None
        }
    except Exception as e:
        logger.error(f"Error reloading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reload dataset: {str(e)}")

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
        return {"status": "running", "message": "FastAPI standalone backend is active. Frontend directory missing."}

if __name__ == "__main__":
    # Run uvicorn server on port 8000
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
