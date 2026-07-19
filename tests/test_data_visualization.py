"""Verification test suite for the Enterprise Data Visualization Layer (Phase 31).

Asserts data visualization helper logs are embedded inside app.js.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app


def test_observability_visualization_logs():
    """Verify that app.js contains all required Phase 31 observability log strings."""
    print("\n--- TESTING VISUALIZATION OBSERVABILITY LOGS ---")
    client = TestClient(app)
    response = client.get("/static/js/app.js")
    
    assert response.status_code == 200
    js_content = response.text
    
    # Assert observability logging matches specifications
    assert "[Observability] Visualization Loaded" in js_content
    assert "[Observability] Charts Rendered" in js_content
    assert "[Observability] Dashboard Updated" in js_content
    assert "[Observability] Filters Applied" in js_content
    print("✓ Visualization logging hooks verified in app.js.")


if __name__ == "__main__":
    print("Initializing Data Visualization verification suite...")
    
    test_observability_visualization_logs()
    
    print("\n" + "=" * 60)
    print("All Data Visualization layer tests passed successfully!")
    print("=" * 60)
