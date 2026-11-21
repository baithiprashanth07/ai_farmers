"""Tests for AI Farmer."""
import pytest
from fastapi.testclient import TestClient
import app.api.main as api_module
from app.api.main import app, get_current_user
from app.services.auth_service import pwd_context

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent_count"] == len(data["agents"])

def test_list_agents():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == len({agent["id"] for agent in data["agents"]})


def test_language_and_regional_crop_reference_endpoints():
    languages = client.get("/api/v1/languages")
    regions = client.get("/api/v1/regions")
    assert languages.status_code == regions.status_code == 200
    assert len(languages.json()["languages"]) == 23
    assert len(regions.json()["regions"]) == 36
    assert "not official recommendations" in regions.json()["reference_note"]
    assert "specialty_crops" in regions.json()["regions"][0]


def test_language_preference_requires_authentication_and_valid_language():
    assert client.put("/api/v1/profile/language", json={
        "language_preference": "pa",
    }).status_code == 401
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-farmer"}
    try:
        invalid = client.put("/api/v1/profile/language", json={
            "language_preference": "xx",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert invalid.status_code == 422


def test_language_preference_updates_existing_farmer_profile(monkeypatch):
    updated = {}

    def update_profile_language(user_id, language):
        updated["value"] = (user_id, language)
        return True

    monkeypatch.setattr(api_module.db_service, "update_profile_language", update_profile_language)
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-farmer"}
    try:
        response = client.put("/api/v1/profile/language", json={
            "language_preference": "ta",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["saved_to_profile"] is True
    assert updated["value"] == ("test-farmer", "ta")

def test_farm_analysis_requires_authentication():
    payload = {"state": "Punjab", "district": "Ludhiana", "farm_size_acres": 5}
    assert client.post("/api/v1/analyze", json=payload).status_code == 401
    assert client.post("/api/v1/analyze/stream", json=payload).status_code == 401

def test_registration_rejects_passwords_over_bcrypt_limit():
    response = client.post("/api/v1/auth/register", json={
        "name": "Test Farmer",
        "phone": "9876543210",
        "password": "é" * 37,
    })
    assert response.status_code == 422
    assert "72 UTF-8 bytes" in response.text

def test_password_hash_accepts_15_character_password():
    sample_password = "FarmTest1234567"
    password_hash = pwd_context.hash(sample_password)
    assert pwd_context.verify(sample_password, password_hash)

def test_mobile_dashboard_and_service_worker():
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "Build my farm plan" in dashboard.text
    assert client.get("/app").text == dashboard.text

    manifest = client.get("/static/manifest.webmanifest")
    assert manifest.status_code == 200
    assert manifest.json()["display"] == "standalone"

    service_worker = client.get("/service-worker.js")
    assert service_worker.status_code == 200
    assert service_worker.headers["service-worker-allowed"] == "/"

def test_analysis_stream_reports_agent_progress(monkeypatch):
    class StubGraph:
        def stream(self, state, config, stream_mode):
            assert stream_mode == "values"
            snapshot = {
                **state,
                "completed_agents": ["crop_recommendation"],
                "active_agents": [],
                "agent_messages": [{
                    "agent_name": "crop_recommendation",
                    "message": "Crop options checked for this field.",
                    "timestamp": "2026-01-01T00:00:00",
                    "data": {},
                    "priority": "medium",
                }],
                "errors": [],
                "agronomist_advice": "Check soil moisture before irrigation.",
            }
            yield snapshot

    monkeypatch.setattr(api_module, "ai_farmer_graph", StubGraph())
    monkeypatch.setattr(api_module, "_save_analysis", lambda *args: None)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test-farmer",
        "name": "Test Farmer",
        "phone": "9000000000",
    }
    try:
        response = client.post("/api/v1/analyze/stream", json={
            "state": "Punjab",
            "district": "Ludhiana",
            "farm_size_acres": 5,
            "target_crop": "wheat",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert "event: progress" in response.text
    assert "Crop options checked for this field." in response.text
    assert "event: result" in response.text
    assert "Check soil moisture before irrigation." in response.text

def test_ai_status_and_location_lookup_require_authentication(monkeypatch):
    assert client.get("/api/v1/ai/status").status_code == 401
    assert client.get("/api/v1/locations/search?query=Ludhiana").status_code == 401

    monkeypatch.setattr(
        api_module.location_service,
        "search",
        lambda query: [{
            "name": "Ludhiana",
            "district": "Ludhiana",
            "state": "Punjab",
            "country": "India",
            "latitude": 30.9,
            "longitude": 75.8,
            "timezone": "Asia/Kolkata",
        }],
    )
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test-farmer",
        "name": "Test Farmer",
        "phone": "9000000000",
    }
    try:
        status_response = client.get("/api/v1/ai/status")
        location_response = client.get("/api/v1/locations/search?query=Ludhiana")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status_response.status_code == 200
    assert "api_key" not in status_response.json()
    assert location_response.json()["locations"][0]["longitude"] == 75.8

def test_farm_suggestions_require_authentication_and_return_field_data(monkeypatch):
    assert client.post("/api/v1/farm/suggestions", json={
        "state": "Punjab",
        "district": "Ludhiana",
        "farm_size_acres": 5,
    }).status_code == 401

    monkeypatch.setattr(api_module, "_build_farm_suggestions", lambda farm, user, request_id: {
        "request_id": request_id,
        "location": {"state": farm.state, "district": farm.district},
        "crop_recommendations": [{"crop_name": "Wheat"}],
        "seed_recommendations": [{"variety_name": "HD 2967"}],
        "fertilizer_plan": [{"fertilizer_name": "Urea"}],
        "weather": {"source": "open-meteo", "forecast": []},
    })
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "test-farmer",
        "name": "Test Farmer",
        "phone": "9000000000",
    }
    try:
        response = client.post("/api/v1/farm/suggestions", json={
            "state": "Punjab",
            "district": "Ludhiana",
            "farm_size_acres": 5,
            "latitude": 30.9,
            "longitude": 75.8,
            "soil_type": "alluvial",
            "season": "rabi",
            "target_crop": "wheat",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["crop_recommendations"][0]["crop_name"] == "Wheat"
    assert response.json()["seed_recommendations"][0]["variety_name"] == "HD 2967"
    assert response.json()["weather"]["source"] == "open-meteo"

def test_ecommerce_categories():
    response = client.get("/api/v1/shop/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 4

def test_ecommerce_search():
    payload = {"query": "urea", "category": "fertilizer"}
    response = client.post("/api/v1/shop/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
