from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_circular_supply_chain_full_payload():
    response = client.post("/api/circular-supply-chain/payload", json={"filters": {}})
    assert response.status_code == 200
    res_data = response.json()
    
    payload = res_data.get("payload", res_data)
    assert "overview" in payload
    assert "decision_matrix" in payload
    assert "redeployments" in payload
    assert "harvesting_opportunities" in payload
    assert "sustainability" in payload
    assert "ai_recommendations" in payload
    assert "lifecycle_flow" in payload

    # Verify decision matrix categories
    matrix = payload["decision_matrix"]
    assert len(matrix) >= 4
    categories = [m["category"] for m in matrix]
    assert "Repair & Redeploy" in categories
    assert "Direct Reuse" in categories
    assert "Component Harvest" in categories
    assert "Responsible Recycling" in categories

    # Verify redeployments table data
    redeployments = payload["redeployments"]
    assert len(redeployments) >= 5
    for r in redeployments:
        assert "part_number" in r
        assert "origin_hub" in r
        assert "recommended_destination" in r
        assert "confidence" in r or "confidence_score" in r

    # Verify harvesting opportunities
    harvesting = payload["harvesting_opportunities"]
    assert len(harvesting) >= 3
    for h in harvesting:
        assert "component" in h or "parent_part" in h
        assert "recoverable_parts" in h
        assert "confidence" in h

    # Verify sustainability metrics
    sustain = payload["sustainability"]
    assert "carbon_saved_kg" in sustain or "co2_saved_kg" in sustain
    assert "repair_success_rate" in sustain

    # Verify AI recommendations
    recs = payload["ai_recommendations"]
    assert len(recs) >= 3
    for rec in recs:
        assert "recommendation" in rec
        assert "business_reason" in rec
        assert "evidence" in rec
        assert "confidence" in rec

    print("test_circular_supply_chain_full_payload passed successfully!")

if __name__ == "__main__":
    test_circular_supply_chain_full_payload()
