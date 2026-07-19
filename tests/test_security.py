"""Verification test suite for the Enterprise Security & Access Control Layer (Phase 27).

Tests token generation, role mapping scopes, route permissions locks, and audit logging.
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.repository import repository
from backend.main import app
from backend.security.jwt_manager import JWTManager
from backend.security.audit_logger import AuditLogger
from backend.models.user_role import UserRole


def setup():
    """Initialize repository for tests."""
    if not repository.is_initialized():
        repository.initialize()


def test_jwt_generation_and_decoding():
    """Verify JWT token creation and correct decoding validation payload."""
    print("\n--- TESTING JWT TOKENS ---")
    td = JWTManager.create_tokens("user-111", "testuser", UserRole.LOGISTICS_ANALYST)
    
    assert td.access_token is not None
    assert td.token_type == "bearer"
    
    principal = JWTManager.decode_token(td.access_token)
    assert principal is not None
    assert principal.user_id == "user-111"
    assert principal.username == "testuser"
    assert principal.role == UserRole.LOGISTICS_ANALYST
    assert "optimization:write" in principal.permissions
    assert "admin:write" not in principal.permissions
    
    print("✓ JWT creation and decoding verified.")


def test_unauthorized_access():
    """Verify API returns 401 Unauthorized when missing credentials."""
    print("\n--- TESTING UNAUTHORIZED LOCK ---")
    client = TestClient(app)
    # Call a secured endpoint (like audit logs) without headers
    response = client.get("/api/v1/security/audit-logs")
    assert response.status_code == 401
    
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == 401
    assert "Missing Authorization" in data["error"]["detail"]
    print("✓ Unauthorized endpoint lock verified.")


def test_rbac_forbidden_access():
    """Verify API returns 403 Forbidden when user has insufficient roles scopes."""
    print("\n--- TESTING FORBIDDEN RBAC LOCK ---")
    client = TestClient(app)
    
    # 1. Log in as Viewer
    res_login = client.post("/api/v1/security/auth/token", json={"username": "viewer", "password": "viewer123"})
    assert res_login.status_code == 200
    token = res_login.json()["payload"]["access_token"]

    # 2. Call audit-logs endpoint (requires admin:write scope)
    headers = {"Authorization": f"Bearer {token}"}
    res_call = client.get("/api/v1/security/audit-logs", headers=headers)
    assert res_call.status_code == 403
    
    data = res_call.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == 403
    assert "Insufficient permissions" in data["error"]["detail"]
    print("✓ RBAC Forbidden lock verified.")


def test_authorized_access_and_audit():
    """Verify authorized users gain access and audit logs are recorded."""
    print("\n--- TESTING AUTHORIZED ACCESS & AUDIT LOGS ---")
    client = TestClient(app)
    
    # 1. Log in as Administrator
    res_login = client.post("/api/v1/security/auth/token", json={"username": "admin", "password": "admin123"})
    assert res_login.status_code == 200
    token = res_login.json()["payload"]["access_token"]

    # 2. Call audit-logs endpoint
    headers = {"Authorization": f"Bearer {token}"}
    res_call = client.get("/api/v1/security/audit-logs", headers=headers)
    assert res_call.status_code == 200
    
    data = res_call.json()
    assert data["status"] == "success"
    
    payload = data["payload"]
    assert len(payload) > 0
    
    # Verify a login success event was recorded in audit logs
    event_types = [e["event_type"] for e in payload]
    assert "LOGIN" in event_types
    assert "API_ACCESS" in event_types

    print(f"Logged audit event count: {len(payload)}")
    print("✓ Authorized access and audit logging verified.")


if __name__ == "__main__":
    print("Initializing Enterprise Security verification suite...")
    setup()

    test_jwt_generation_and_decoding()
    test_unauthorized_access()
    test_rbac_forbidden_access()
    test_authorized_access_and_audit()

    print("\n" + "=" * 60)
    print("All Enterprise Security tests passed successfully!")
    print("=" * 60)
