"""Verification test suite for the Enterprise UI Modernization Foundation (Phase 30).

Asserts static layout elements, modern styles rules serving, and references in index.html.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.main import app


def test_modernized_css_served():
    """Verify style.css is mounted and serves Phase 30 modernization foundation classes."""
    print("\n--- TESTING MODERNIZED CSS SERVING ---")
    client = TestClient(app)
    response = client.get("/static/css/style.css")
    
    assert response.status_code == 200
    css_content = response.text
    
    # Assert modernization styles exist
    assert "btn-sidebar-toggle" in css_content
    assert "sidebar.collapsed" in css_content
    assert "UI MODERNIZATION FOUNDATION" in css_content
    print("✓ Modernized style.css served successfully.")


def test_index_html_has_sidebar_toggle():
    """Verify that index.html contains the sidebar toggle button."""
    print("\n--- TESTING SIDEBAR TOGGLE IN INDEX.HTML ---")
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    html_content = response.text
    
    assert "sidebar-toggle" in html_content
    assert "btn-sidebar-toggle" in html_content
    print("✓ Sidebar toggle button layout verified in index.html.")


if __name__ == "__main__":
    print("Initializing UI Modernization verification suite...")
    
    test_modernized_css_served()
    test_index_html_has_sidebar_toggle()
    
    print("\n" + "=" * 60)
    print("All UI Modernization foundation tests passed successfully!")
    print("=" * 60)
