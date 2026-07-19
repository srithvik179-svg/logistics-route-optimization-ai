"""Verification test suite for the Frontend Integration Layer (Phase 29).

Asserts static files serving and references in index.html.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app


def test_static_integration_js_served():
    """Verify that api_gateway_integration.js is correctly mounted and served."""
    print("\n--- TESTING STATIC INTEGRATION SCRIPT SERVING ---")
    client = TestClient(app)
    response = client.get("/static/js/api_gateway_integration.js")
    
    assert response.status_code == 200
    assert "Frontend Connected" in response.text
    print("✓ api_gateway_integration.js served successfully.")


def test_index_html_references_script():
    """Verify that index.html references the integration script before app.js."""
    print("\n--- TESTING INDEX.HTML REFERENCES ---")
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    html_content = response.text
    
    # Assert script tag exists
    assert "/static/js/api_gateway_integration.js" in html_content
    # Assert it appears before app.js
    idx_integration = html_content.find("/static/js/api_gateway_integration.js")
    idx_app = html_content.find("/static/js/app.js")
    
    assert idx_integration != -1
    assert idx_app != -1
    assert idx_integration < idx_app
    print("✓ Integration script loading priority verified in index.html.")


if __name__ == "__main__":
    print("Initializing Frontend Integration verification suite...")
    
    test_static_integration_js_served()
    test_index_html_references_script()
    
    print("\n" + "=" * 60)
    print("All Frontend Integration tests passed successfully!")
    print("=" * 60)
