"""Verification test suite for the Enterprise Geospatial Visualization Platform (Phase 32).

Asserts geospatial mapping helper logs are embedded inside app.js.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app


def test_observability_geospatial_logs():
    """Verify that app.js contains all required Phase 32 observability log strings."""
    print("\n--- TESTING GEOSPATIAL OBSERVABILITY LOGS ---")
    client = TestClient(app)
    response = client.get("/static/js/app.js")
    
    assert response.status_code == 200
    js_content = response.text
    
    # Assert observability logging matches specifications
    assert "[Observability] Map Initialized" in js_content
    assert "[Observability] Locations Loaded" in js_content
    assert "[Observability] Routes Rendered" in js_content
    assert "[Observability] Optimization Layer Loaded" in js_content
    print("✓ Geospatial mapping logging hooks verified in app.js.")


if __name__ == "__main__":
    print("Initializing Geospatial Visualization verification suite...")
    
    test_observability_geospatial_logs()
    
    print("\n" + "=" * 60)
    print("All Geospatial Visualization platform tests passed successfully!")
    print("=" * 60)
