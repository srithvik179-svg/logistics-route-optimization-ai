from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_command_center_3d_frontend_route():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Check 3D AI Command Center sidebar item
    assert 'id="nav-command-3d"' in html
    assert 'data-target="command-3d-section"' in html
    assert '3D AI Command Center' in html

    # Check 3D AI Command Center section container
    assert 'id="command-3d-section"' in html
    assert 'id="canvas-3d-scene"' in html
    assert 'id="command-3d-inspector"' in html
    assert 'id="command-3d-alerts-container"' in html

    # Check script tags
    assert 'three.min.js' in html
    assert 'OrbitControls.js' in html
    assert 'command_center_3d.js' in html

    print("test_command_center_3d_frontend_route passed successfully!")

if __name__ == "__main__":
    test_command_center_3d_frontend_route()
