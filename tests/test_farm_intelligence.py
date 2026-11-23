import json
import uuid
from datetime import date, timedelta
from types import SimpleNamespace

from PIL import Image

from app.agents.agronomist_agent import AgronomistAgent
from app.agents.crop_recommendation_agent import CropRecommendationAgent
from app.agents.state_crop_intelligence_agent import StateCropIntelligenceAgent
from app.api.main import _build_farm_suggestions
from app.schemas.models import FarmerLanguage, FarmInput
from app.services.agriculture_reference import (
    get_state_crop_options,
    get_state_crop_reference,
    list_indian_regions,
)
from app.services.ai_service import AIService
from app.services.agriculture_updates import get_daily_agriculture_update
from app.services.crop_calendar import build_daily_crop_schedule, get_crop_duration_days
from app.services.crop_reference_catalog import get_crop_categories, get_crop_seasons
from app.services.farm_calculator import (
    calculate_fertilizer_requirement,
    estimate_crop_budget,
)
from app.services.farmer_tools import list_farmer_tools
from app.services.disease_service import DiseaseDetectionService
from app.services.database import FarmerProfile, User, db_service
from app.services.gov_scheme_service import GovernmentSchemeService
from app.services.india_languages import INDIAN_LANGUAGES, LANGUAGE_DISPLAY_NAMES
from app.services.location_service import LocationService
from app.services.weather_service import WeatherService


class StubResponse:
    def __init__(self, data):
        self.data = data
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class StubHTTPClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_daily_agriculture_brief_changes_by_date_and_links_official_sources():
    first_date = date(2026, 11, 22)
    first = get_daily_agriculture_update(first_date)
    next_day = get_daily_agriculture_update(first_date + timedelta(days=1))

    assert first["date"] == "2026-11-22"
    assert first["is_live_news"] is False
    assert first["checklist_title"] != next_day["checklist_title"]
    assert any("imd.gov.in" in source["url"] for source in first["official_sources"])
    assert any("myscheme.gov.in" in source["url"] for source in first["official_sources"])


def test_scheme_recommendations_are_state_aware_and_do_not_mutate_catalog():
    service = GovernmentSchemeService()
    recommendations = service.get_relevant_schemes("Punjab", "wheat", 1.5)

    assert len(recommendations) == 10
    assert all(item["farmer_state"] == "Punjab" for item in recommendations)
    assert recommendations[0]["relevance_score"] >= 70
    recommendations[0]["farmer_state"] = "Changed"
    assert all("farmer_state" not in item for item in service.schemes)
    assert any("state" in item["coverage"].lower() for item in recommendations)


def test_farm_calculators_scale_rates_and_estimate_whole_field_returns():
    fertilizer = calculate_fertilizer_requirement(3.5, 12.5, 20)
    budget = estimate_crop_budget(5, 20, 2200, 8000)

    assert fertilizer == {"quantity_kg": 43.75, "estimated_cost_inr": 875.0}
    assert budget == {
        "total_yield_quintal": 100,
        "gross_revenue_inr": 220000,
        "total_cost_inr": 40000,
        "estimated_net_inr": 180000,
    }


def test_farm_calculators_reject_invalid_area_and_negative_inputs():
    import pytest

    with pytest.raises(ValueError):
        calculate_fertilizer_requirement(0, 10)
    with pytest.raises(ValueError):
        estimate_crop_budget(1, -1, 2000, 5000)


def test_farmer_services_directory_covers_requested_apps_and_has_safe_links():
    tools = list_farmer_tools()
    names = {tool["name"] for tool in tools}
    expected_names = {
        "Kisan Suvidha",
        "Meghdoot",
        "Mausam",
        "eNAM",
        "PM-KISAN",
        "Crop Insurance (PMFBY)",
        "Soil Health Card",
        "Kisan e-Mitra",
        "Bharat-VISTAAR",
        "National Pest Surveillance System (NPSS)",
        "AgroStar",
        "DeHaat Kisan",
        "Plantix",
        "Krishify",
        "Bijak",
        "Ninja Kisan",
        "Arya.ag",
        "Outgrow",
        "FarMart",
        "AgriApp",
    }

    assert names == expected_names
    assert all(
        tool["url"].startswith("https://")
        and tool["features"]
        and tool["best_for"]
        for tool in tools
    )


def test_crop_calendar_builds_a_daily_schedule_through_expected_harvest():
    sowing_date = date(2026, 6, 15)
    schedule = build_daily_crop_schedule("Rice", sowing_date)

    assert get_crop_duration_days("paddy") == 120
    assert schedule["duration_days"] == 120
    assert len(schedule["daily_schedule"]) == 121
    assert schedule["daily_schedule"][0]["date"] == "2026-06-15"
    assert schedule["daily_schedule"][0]["day_after_sowing"] == 0
    assert schedule["daily_schedule"][-1]["day_after_sowing"] == 120
    assert schedule["daily_schedule"][-1]["weekly_or_milestone_task"].startswith("Record harvest")
    assert "panicle" in schedule["daily_schedule"][75]["stage_guidance"]
    assert all(item["daily_check"] for item in schedule["daily_schedule"])


def test_crop_calendar_uses_farmer_harvest_date_for_unlisted_crop():
    sowing_date = date(2026, 3, 1)
    harvest_date = date(2026, 5, 30)

    schedule = build_daily_crop_schedule("Watermelon", sowing_date, harvest_date)

    assert schedule["duration_days"] == 90
    assert schedule["expected_harvest_date"] == "2026-05-30"


def test_crop_reference_includes_seasons_and_expanded_use_categories():
    seasons = {season["name"]: season for season in get_crop_seasons()}
    categories = {item["name"] for item in get_crop_categories()}

    assert {"Kharif", "Rabi", "Zaid"} == set(seasons)
    assert "June–July" in seasons["Kharif"]["description"]
    assert {
        "Food grains and pulses",
        "Commercial and fibre crops",
        "Oilseeds",
        "Plantation crops",
        "Horticulture",
        "Spices and condiments",
        "Fodder crops",
        "Medicinal and aromatic crops",
    }.issubset(categories)


def test_language_options_include_scheduled_languages_with_native_names():
    scheduled_language_codes = {
        language.value
        for language in FarmerLanguage
        if language != FarmerLanguage.ENGLISH
    }

    assert {language["code"] for language in INDIAN_LANGUAGES} == scheduled_language_codes
    for language in INDIAN_LANGUAGES:
        assert LANGUAGE_DISPLAY_NAMES[language["code"]] == (
            f"{language['name']} ({language['native_name']})"
        )


def test_disease_image_check_never_guesses_when_model_is_unavailable(tmp_path):
    service = object.__new__(DiseaseDetectionService)
    service.model = None
    service.model_loaded = False
    image_path = tmp_path / "leaf.png"
    Image.new("RGB", (8, 8), color="green").save(image_path)

    result = service.detect_from_image(str(image_path), "Tomato")

    assert result["disease_name"] == "Unable to detect"
    assert result["detection_method"] == "model_unavailable"
    assert result["confidence"] == 0


def test_symptom_check_returns_a_reference_match_without_model_inference():
    service = object.__new__(DiseaseDetectionService)
    service.disease_database = service._load_disease_database()

    result = service.detect_from_symptoms("Tomato", [
        "Dark brown spots with concentric rings (target spot)",
        "Yellowing of older leaves from bottom",
    ])

    assert result["disease_name"] == "Early Blight"
    assert result["detection_method"] == "symptom_based"


def test_ai_provider_auto_selects_the_first_configured_vendor():
    service = AIService()
    service.settings = SimpleNamespace(
        ai_provider="auto",
        ai_api_key=None,
        ai_model=None,
        ai_base_url=None,
        openai_api_key=None,
        groq_api_key="test-key",
        groq_model="llama-test",
        gemini_api_key="another-test-key",
        anthropic_api_key=None,
        openrouter_api_key=None,
        ollama_base_url="http://localhost:11434/v1",
    )

    provider, key, model, base_url = service._provider_config()

    assert (provider, key, model) == ("groq", "test-key", "llama-test")
    assert base_url == "https://api.groq.com/openai/v1"


def test_ai_service_supports_openai_compatible_chat(monkeypatch):
    service = AIService()
    service._provider_config = lambda: (
        "groq",
        "test-key-not-a-real-credential",
        "test-model",
        "https://api.example.test/v1",
    )
    client = StubHTTPClient(StubResponse({
        "choices": [{"message": {"content": "Check soil moisture first."}}],
    }))
    monkeypatch.setattr("app.services.ai_service.httpx.Client", lambda **kwargs: client)

    answer = service.complete("Farm adviser", "Suggest next steps")

    assert answer == "Check soil moisture first."
    url, request = client.calls[0]
    assert url == "https://api.example.test/v1/chat/completions"
    assert request["headers"]["Authorization"].startswith("Bearer ")
    assert request["json"]["model"] == "test-model"


def test_ai_service_supports_anthropic_messages(monkeypatch):
    service = AIService()
    service._provider_config = lambda: (
        "anthropic",
        "test-key-not-a-real-credential",
        "claude-test",
        None,
    )
    client = StubHTTPClient(StubResponse({
        "content": [{"type": "text", "text": "Test the soil before fertilizing."}],
    }))
    monkeypatch.setattr("app.services.ai_service.httpx.Client", lambda **kwargs: client)

    assert service.complete("Farm adviser", "Suggest next steps") == "Test the soil before fertilizing."
    url, request = client.calls[0]
    assert url == "https://api.anthropic.com/v1/messages"
    assert request["headers"]["anthropic-version"] == "2023-06-01"
    assert request["json"]["model"] == "claude-test"


def test_ai_service_supports_gemini_generate_content(monkeypatch):
    service = AIService()
    service._provider_config = lambda: ("gemini", "test-key", "gemini-test", None)
    client = StubHTTPClient(StubResponse({
        "candidates": [{"content": {"parts": [{"text": "Check local rainfall."}]}}],
    }))
    monkeypatch.setattr("app.services.ai_service.httpx.Client", lambda **kwargs: client)

    assert service.complete("Farm adviser", "Suggest next steps") == "Check local rainfall."
    url, request = client.calls[0]
    assert url.endswith("/models/gemini-test:generateContent")
    assert request["params"] == {"key": "test-key"}


def test_ai_adviser_receives_farm_fields_and_specialist_findings(monkeypatch):
    observed = {}

    def complete(system_prompt, user_prompt):
        observed["system"] = system_prompt
        observed["payload"] = json.loads(user_prompt)
        return "Check local rainfall before irrigation."

    monkeypatch.setattr("app.agents.agronomist_agent.ai_service.complete", complete)
    monkeypatch.setattr(
        "app.agents.agronomist_agent.ai_service.status",
        lambda: {"configured": True, "provider": "ollama", "model": "llama3.1"},
    )
    state = {
        "farm_context": {
            "farmer_id": "private-user-id",
            "state": "Punjab",
            "district": "Ludhiana",
            "latitude": 30.9,
            "longitude": 75.8,
            "farm_size_acres": 5,
            "soil_type": "alluvial",
            "season": "rabi",
            "budget_inr": 20000,
            "previous_crop": "rice",
            "irrigation_type": "drip",
            "target_crop": "wheat",
            "language_preference": "pa",
        },
        "user_query": "Suggest water-saving measures.",
        "agent_messages": [{
            "agent_name": "WeatherAgent",
            "message": "Rain is forecast tomorrow.",
            "timestamp": "2026-01-01T00:00:00",
            "data": {"rainy_days": 1},
            "priority": "high",
        }],
        "crop_recommendations": [{
            "crop_name": "Wheat",
            "confidence_score": .9,
            "expected_yield_quintal_per_acre": 22,
        }],
        "weather_forecast": {
            "source": "open-meteo",
            "forecast": [{"date": "2026-01-02", "rainfall_mm": 4}],
        },
        "fertilizer_plan": {"fertilizers": [{"fertilizer_name": "Urea"}]},
    }

    result = AgronomistAgent()._execute(state)

    assert result["agronomist_advice"] == "Check local rainfall before irrigation."
    assert result["ai_provider_status"]["provider"] == "ollama"
    payload = observed["payload"]
    assert payload["farm_fields"]["previous_crop"] == "rice"
    assert payload["farm_fields"]["budget_inr"] == 20000
    assert payload["response_language"] == "Punjabi"
    assert "Respond in Punjabi" in observed["system"]
    assert "farmer_id" not in payload["farm_fields"]
    assert "latitude" not in payload["farm_fields"]
    assert payload["specialist_findings"]["weather_forecast"]["source"] == "open-meteo"
    assert payload["farmer_question"] == "Suggest water-saving measures."


def test_open_meteo_forecast_maps_location_weather(monkeypatch):
    weather = WeatherService()
    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        lambda *args, **kwargs: StubResponse({
            "daily": {
                "time": ["2026-11-20"],
                "temperature_2m_max": [28],
                "temperature_2m_min": [17],
                "precipitation_probability_max": [40],
                "precipitation_sum": [2.4],
                "wind_speed_10m_max": [12],
                "weather_code": [61],
            },
        }),
    )

    result = weather._get_open_meteo_forecast(30.9, 75.8, 7)

    assert result["source"] == "open-meteo"
    assert result["coordinates"] == {"latitude": 30.9, "longitude": 75.8}
    assert result["forecast"][0]["condition"] == "Rain"
    assert result["forecast"][0]["rainfall_probability_percent"] == 40


def test_location_search_returns_coordinates_without_exposing_provider_details(monkeypatch):
    service = LocationService()

    class Response(StubResponse):
        pass

    monkeypatch.setattr(
        "app.services.location_service.httpx.get",
        lambda *args, **kwargs: Response({
            "results": [{
                "name": "Ludhiana",
                "admin1": "Punjab",
                "admin2": "Ludhiana",
                "country": "India",
                "latitude": 30.9,
                "longitude": 75.8,
            }],
        }),
    )

    result = service.search("Ludhiana")

    assert result == [{
        "name": "Ludhiana",
        "district": "Ludhiana",
        "state": "Punjab",
        "country": "India",
        "latitude": 30.9,
        "longitude": 75.8,
        "timezone": None,
    }]


def test_field_suggestions_choose_crop_and_share_all_field_data(monkeypatch):
    captured = {}

    class StubAgent:
        def __init__(self, name, execute):
            self.name = name
            self.execute = execute

        def run(self, state):
            captured.setdefault("order", []).append(state["current_agent_name"])
            if state["current_agent_name"] == "crop_recommendation":
                state["crop_recommendations"] = [{
                    "crop_name": "Wheat",
                    "confidence_score": .88,
                    "expected_yield_quintal_per_acre": 22,
                    "estimated_cost_per_acre": 12000,
                }]
            elif state["current_agent_name"] == "seed_recommendation":
                state["seed_recommendations"] = [{"variety_name": "HD 2967"}]
            elif state["current_agent_name"] == "fertilizer_planner":
                state["fertilizer_plan"] = {"fertilizers": [{"fertilizer_name": "Urea"}]}
            elif state["current_agent_name"] == "weather_forecast":
                state["weather_forecast"] = {"source": "test", "forecast": []}
            elif state["current_agent_name"] == "soil_health_analyzer":
                state["soil_health_report"] = {"health_status": "Good"}
            elif state["current_agent_name"] == "ai_agronomist_assistant":
                captured["farm_context_sent_to_ai"] = {
                    key: value for key, value in state["farm_context"].items()
                    if key not in {"farmer_id", "latitude", "longitude"}
                }
                state["agronomist_advice"] = "Review this plan with your local advisor."
                state["ai_provider_status"] = {"configured": False, "provider": "none"}
            return state

    agent_names = {
        "crop_recommendation": "crop_recommendation",
        "state_crop_intelligence": "state_crop_intelligence",
        "weather_forecast": "weather_forecast",
        "soil_health_analyzer": "soil_health_analyzer",
        "seed_recommendation": "seed_recommendation",
        "fertilizer_planner": "fertilizer_planner",
        "irrigation_planner": "irrigation_planner",
        "market_price_prediction": "market_price_prediction",
        "ai_agronomist_assistant": "ai_agronomist_assistant",
    }
    monkeypatch.setattr(
        "app.api.main.AGENTS",
        {name: StubAgent(name, None) for name in agent_names},
    )
    farm_input = FarmInput(
        state="Punjab",
        district="Ludhiana",
        latitude=30.9,
        longitude=75.8,
        farm_size_acres=5,
        soil_type="alluvial",
        season="rabi",
        budget_inr=20000,
        previous_crop="rice",
        irrigation_type="drip",
        language_preference="pa",
        query="How should I reduce water use?",
    )

    result = _build_farm_suggestions(
        farm_input,
        {"id": "test-farmer"},
        "suggestion-test",
    )

    assert result["selected_crop"] == "wheat"
    assert result["seed_recommendations"] == [{"variety_name": "HD 2967"}]
    assert result["fertilizer_plan"] == [{"fertilizer_name": "Urea"}]
    assert captured["farm_context_sent_to_ai"]["soil_type"] == "alluvial"
    assert captured["farm_context_sent_to_ai"]["budget_inr"] == 20000
    assert captured["farm_context_sent_to_ai"]["previous_crop"] == "rice"
    assert captured["farm_context_sent_to_ai"]["language_preference"] == "pa"
    assert "farmer_id" not in captured["farm_context_sent_to_ai"]
    assert "latitude" not in captured["farm_context_sent_to_ai"]


def test_indicative_crop_reference_covers_all_states_and_union_territories():
    regions = list_indian_regions()
    assert len(regions) == 36
    assert sum(region["type"] == "state" for region in regions) == 28
    assert sum(region["type"] == "union_territory" for region in regions) == 8
    assert all(region["major_crops"] and region["specialty_crops"] for region in regions)
    assert get_state_crop_reference("Orissa")["name"] == "Odisha"
    assert get_state_crop_reference("Pondicherry")["name"] == "Puducherry"
    punjab_crops = get_state_crop_options("Punjab")
    assert "wheat" in punjab_crops
    assert "Basmati rice" in punjab_crops
    assert len({crop.casefold() for crop in punjab_crops}) == len(punjab_crops)


def test_location_search_uses_state_context_and_filters_other_states(monkeypatch):
    observed = {}

    def fake_get(url, params, timeout):
        observed.update(params)
        return StubResponse({"results": [
            {
                "name": "Dugri",
                "admin1": "Punjab",
                "admin2": "Ludhiana",
                "country": "India",
                "latitude": 30.9,
                "longitude": 75.8,
            },
            {
                "name": "Dugri",
                "admin1": "Haryana",
                "admin2": "Hisar",
                "country": "India",
                "latitude": 29.1,
                "longitude": 75.7,
            },
        ]})

    monkeypatch.setattr("app.services.location_service.httpx.get", fake_get)

    locations = LocationService().search(
        "Dugri",
        state="Punjab",
        district="Ludhiana",
    )

    assert observed["name"] == "Dugri, Ludhiana, Punjab"
    assert [location["state"] for location in locations] == ["Punjab"]


def test_farm_profile_persists_village_and_clears_stale_coordinates():
    user_id = str(uuid.uuid4())
    session = db_service.get_session()
    session.add(User(
        id=user_id,
        phone=f"9{uuid.uuid4().int % 10**9:09d}",
        password_hash="not-used-for-this-test",
        name="Location Test",
    ))
    session.commit()
    try:
        db_service.create_or_update_profile(user_id, {
            "state": "Punjab",
            "district": "Ludhiana",
            "village": "Dugri",
            "latitude": 30.9,
            "longitude": 75.8,
        })
        profile = db_service.get_profile(user_id)
        assert profile["village"] == "Dugri"
        assert profile["latitude"] == 30.9
        assert profile["longitude"] == 75.8

        db_service.create_or_update_profile(user_id, {
            "state": "Haryana",
            "district": "Hisar",
            "latitude": None,
            "longitude": None,
        })
        profile = db_service.get_profile(user_id)
        assert profile["latitude"] is None
        assert profile["longitude"] is None
    finally:
        session.query(FarmerProfile).filter_by(user_id=user_id).delete()
        session.query(User).filter_by(id=user_id).delete()
        session.commit()
        session.close()


def test_regional_crop_reference_influences_crop_ranking():
    state = {
        "farm_context": {
            "state": "Maharashtra",
            "district": "Nashik",
            "soil_type": "black",
            "season": "kharif",
            "irrigation_type": "flood",
            "farm_size_acres": 4,
        },
        "agent_messages": [],
        "errors": [],
    }

    result = CropRecommendationAgent().run(state)
    soybean = next(
        crop for crop in result["crop_recommendations"]
        if crop["crop_name"] == "Soybean"
    )
    assert "Commonly grown in Maharashtra" in soybean["reasoning"]


def test_state_agent_adds_regional_specialty_candidates():
    state = {
        "farm_context": {"state": "Assam", "season": "kharif"},
        "agent_messages": [],
        "errors": [],
    }

    result = StateCropIntelligenceAgent().run(state)
    regional = result["state_crop_intelligence"]
    assert "Assam tea" in regional["specialty_crops"]
    assert regional["official_local_validation_required"] is True
    assert "not official recommendations" in regional["crop_reference_note"]


def test_analysis_state_carries_language_preference():
    from app.api.main import _build_analysis_state

    state = _build_analysis_state(
        FarmInput(
            state="Punjab",
            district="Ludhiana",
            language_preference="pa",
        ),
        {"id": "test-farmer"},
        "language-test",
    )
    assert state["farm_context"]["language_preference"] == "pa"
