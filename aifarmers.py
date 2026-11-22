"""Streamlit dashboard for deploying AI Farmer on Streamlit Community Cloud."""
import base64
import csv
import io
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
from PIL import Image, UnidentifiedImageError


st.set_page_config(
    page_title="AI Farmer",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
FARM_BACKGROUND = base64.b64encode((FRONTEND / "farm-hero.png").read_bytes()).decode("ascii")


def load_streamlit_secrets() -> None:
    """Expose root-level Streamlit secrets to the app's Pydantic settings."""
    try:
        secrets = st.secrets
        for key, value in secrets.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ.setdefault(key.upper(), str(value))
    except FileNotFoundError:
        return


load_streamlit_secrets()

from app.api.main import _build_farm_suggestions
from app.schemas.models import FarmerLanguage, FarmInput, IrrigationType, Season, SoilType
from app.services.agriculture_reference import get_crop_reference_note, list_indian_regions
from app.services.auth_service import auth_service
from app.services.database import db_service
from app.services.india_languages import LANGUAGE_DISPLAY_NAMES
from app.services.location_service import location_service
from app.services.ai_service import ai_service
from app.services import disease_service_instance, ec_service_instance, gov_scheme_service_instance
from app.services.agriculture_updates import get_daily_agriculture_update
from app.services.farm_calculator import calculate_fertilizer_requirement, estimate_crop_budget
from app.services.farmer_tools import list_farmer_tools
from app.services.crop_calendar import (
    build_daily_crop_schedule,
    get_crop_duration_days,
    get_crop_name_options,
)
from app.services.crop_reference_catalog import get_crop_categories, get_crop_seasons
from app.utils import generate_request_id

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        color: #233b2b;
    }
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(238, 246, 235, .82), rgba(238, 246, 235, .88)),
            url("data:image/png;base64,__FARM_BACKGROUND__");
        background-position: center;
        background-size: cover;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(rgba(233, 242, 224, .96), rgba(233, 242, 224, .96)),
            url("data:image/png;base64,__FARM_BACKGROUND__");
        background-position: center;
        background-size: cover;
    }
    .block-container { max-width: 1240px; padding-top: 1.5rem; padding-bottom: 3rem; }
    h1, h2, h3, h4 { color: #234b32; letter-spacing: -.025em; }
    [data-testid="stMetric"] { background: rgba(247, 252, 245, .97); border: 1px solid #c8dbc4; padding: 14px; border-radius: 14px; }
    [data-testid="stForm"], [data-testid="stTabs"] [role="tabpanel"] {
        background: rgba(250, 252, 246, .96);
        border: 1px solid rgba(190, 211, 183, .95);
        border-radius: 16px;
        padding: 1.15rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(250, 252, 246, .92);
        border: 1px solid rgba(207, 220, 199, .75);
        border-radius: 16px;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: #48634c;
        font-weight: 700;
        border-radius: 10px 10px 0 0;
        padding: .65rem .85rem;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #fff;
        background: #34734a;
    }
    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: #34734a;
        border-color: #34734a;
        border-radius: 10px;
    }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-radius: 9px;
    }
    .farm-card { border: 1px solid #cbdcc7; border-radius: 16px; padding: 16px; background: rgba(250,252,246,.96); margin: 8px 0 16px; }
    .farm-card img { width: 100%; height: 100px; object-fit: cover; border-radius: 9px; margin-bottom: 10px; }
    .weather-panel { padding: 14px; border-radius: 14px; background: linear-gradient(110deg, #f3fbff, #e1f1f6); border: 1px solid #c9e2ec; }
    .muted { color: #64736a; font-size: .9rem; }
    img.farm-project-banner { display: block; width: 100%; height: auto; object-fit: contain; border: 1px solid #cbdcc7; border-radius: 18px; margin: 0 0 1.1rem; box-shadow: 0 8px 24px rgba(34, 73, 43, .12); }
    </style>
    """.replace("__FARM_BACKGROUND__", FARM_BACKGROUND),
    unsafe_allow_html=True,
)


def show_illustration(name: str, alt: str) -> None:
    """Render a bundled SVG illustration without requiring a separate static server."""
    image_path = FRONTEND / "illustrations" / name
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{encoded}" alt="{alt}" '
        'style="width:100%;height:104px;object-fit:cover;border-radius:10px;">',
        unsafe_allow_html=True,
    )


def user_from_id(user_id: str) -> Optional[Dict[str, Any]]:
    user = db_service.get_user_by_id(user_id)
    if not user or not user.is_active:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "user_type": user.user_type,
    }


def render_authentication() -> None:
    st.subheader("🔐 Sign in to your farm workspace")
    login_tab, register_tab = st.tabs(["🔑 Sign in", "📝 Create account"])

    with login_tab:
        with st.form("login_form"):
            phone = st.text_input("📱 Indian mobile number", max_chars=10)
            password = st.text_input("🔒 Password", type="password", max_chars=72)
            submitted = st.form_submit_button("🔑 Sign in", type="primary")
        if submitted:
            if not phone.isdigit() or len(phone) != 10 or phone[0] not in "6789":
                st.error("Enter a valid 10-digit Indian mobile number.")
            elif len(password.encode("utf-8")) > 72:
                st.error("Password must not exceed 72 UTF-8 bytes.")
            else:
                result = auth_service.login(phone, password)
                if result.get("success"):
                    st.session_state["farmer_user_id"] = result["user_id"]
                    st.rerun()
                st.error(result.get("error", "Could not sign in."))

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("👤 Your name", max_chars=100)
            phone = st.text_input("📱 Indian mobile number", max_chars=10, key="register_phone")
            password = st.text_input(
                "🔒 Password (at least 6 characters)",
                type="password",
                max_chars=72,
                key="register_password",
            )
            submitted = st.form_submit_button("📝 Create account", type="primary")
        if submitted:
            if len(name.strip()) < 2:
                st.error("Enter your name (at least 2 characters).")
            elif not phone.isdigit() or len(phone) != 10 or phone[0] not in "6789":
                st.error("Enter a valid 10-digit Indian mobile number.")
            elif len(password) < 6 or len(password.encode("utf-8")) > 72:
                st.error("Use a password of at least 6 characters and at most 72 UTF-8 bytes.")
            else:
                result = auth_service.register(phone, password, name.strip())
                if result.get("success"):
                    st.session_state["farmer_user_id"] = result["user_id"]
                    st.rerun()
                st.error(result.get("error", "Could not create account."))


def render_profile(user: Dict[str, Any]) -> Dict[str, Any]:
    profile = db_service.get_profile(user["id"]) or {}
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {user['name']}")
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state.pop("farmer_user_id", None)
            st.session_state.pop("last_farm_suggestions", None)
            st.rerun()

        with st.form("farm_profile"):
            st.markdown("#### 🚜 Farm profile")
            regions = list_indian_regions()
            names = [region["name"] for region in regions]
            state_default = profile.get("state")
            state_index = names.index(state_default) if state_default in names else 0
            state = st.selectbox("🗺️ State / union territory", names, index=state_index)
            district = st.text_input("📍 District", value=profile.get("district") or "")
            area = st.number_input(
                "📐 Farm area (acres)",
                min_value=0.1,
                value=float(profile.get("farm_size_acres") or 1.0),
                step=0.1,
            )
            soil_options = ["", *[soil.value for soil in SoilType]]
            soil_default = profile.get("soil_type") or ""
            soil = st.selectbox(
                "🧱 Soil type",
                soil_options,
                index=soil_options.index(soil_default) if soil_default in soil_options else 0,
            )
            irrigation_options = ["", *[item.value for item in IrrigationType]]
            irrigation_default = profile.get("irrigation_type") or ""
            irrigation = st.selectbox(
                "💧 Water access",
                irrigation_options,
                index=irrigation_options.index(irrigation_default)
                if irrigation_default in irrigation_options else 0,
            )
            language_codes = ["en", *[item.value for item in FarmerLanguage if item.value != "en"]]
            language_default = profile.get("language_preference") or "en"
            language = st.selectbox(
                "🗣️ AI advice language",
                language_codes,
                index=language_codes.index(language_default)
                if language_default in language_codes else 0,
                format_func=lambda code: LANGUAGE_DISPLAY_NAMES[code],
            )
            saved = st.form_submit_button("💾 Save farm profile", type="primary")
        if saved:
            if not district.strip():
                st.error("Enter a district to save your farm profile.")
            else:
                result = db_service.create_or_update_profile(user["id"], {
                    "state": state,
                    "district": district.strip(),
                    "farm_size_acres": area,
                    "soil_type": soil or None,
                    "irrigation_type": irrigation or None,
                    "language_preference": language,
                })
                if result.get("success"):
                    st.success("Farm profile saved.")
                    st.rerun()
                st.error(result.get("error", "Could not save your profile."))
        st.caption("AI advice uses your selected language. Interface text is currently English.")
    return profile


def render_suggestion_card(title: str, illustration: str, body: Any) -> None:
    with st.container(border=True):
        show_illustration(illustration, "")
        st.markdown(f"#### {title}")
        body()


def render_farm_plan(user: Dict[str, Any], profile: Dict[str, Any]) -> None:
    st.subheader("🌾 Field-based farm plan")
    st.caption("Recommendations use your farm details, regional crop references, and available weather data.")
    regions = list_indian_regions()
    region_names = [region["name"] for region in regions]
    profile_state = profile.get("state")
    state_index = region_names.index(profile_state) if profile_state in region_names else 0

    with st.form("farm_plan_form"):
        state = st.selectbox("🗺️ State / union territory", region_names, index=state_index)
        district = st.text_input("📍 District", value=profile.get("district") or "")
        location_query = st.text_input("📌 Town or village for local weather (optional)")
        search_location = st.form_submit_button("🔎 Find weather location")
        area = st.number_input(
            "📐 Farm area (acres)",
            min_value=0.1,
            value=float(profile.get("farm_size_acres") or 1.0),
            step=0.1,
        )
        soil_options = ["", *[soil.value for soil in SoilType]]
        soil_default = profile.get("soil_type") or ""
        soil = st.selectbox(
            "🧱 Soil type",
            soil_options,
            index=soil_options.index(soil_default) if soil_default in soil_options else 0,
        )
        season = st.selectbox("🗓️ Growing season", [season.value for season in Season])
        irrigation_options = ["", *[item.value for item in IrrigationType]]
        irrigation_default = profile.get("irrigation_type") or ""
        irrigation = st.selectbox(
            "💧 Water access",
            irrigation_options,
            index=irrigation_options.index(irrigation_default)
            if irrigation_default in irrigation_options else 0,
        )
        target_crop = st.text_input("🌱 Crop you are growing or considering")
        budget = st.number_input("💰 Budget in rupees (optional)", min_value=0, step=1000)
        language_codes = ["en", *[item.value for item in FarmerLanguage if item.value != "en"]]
        language_default = profile.get("language_preference") or "en"
        language = st.selectbox(
            "🗣️ AI advice language",
            language_codes,
            index=language_codes.index(language_default)
            if language_default in language_codes else 0,
            format_func=lambda code: LANGUAGE_DISPLAY_NAMES[code],
        )
        query = st.text_area("❓ What would you like help with?")
        submitted = st.form_submit_button("🌿 Build my farm plan", type="primary")

    selected_location = st.session_state.get("farm_location")
    if search_location:
        if len(location_query.strip()) < 2:
            st.warning("Enter at least two characters to search for a weather location.")
        else:
            locations = location_service.search(location_query.strip())
            st.session_state["farm_location_options"] = locations
            if not locations:
                st.warning("No places found. You can continue without location-specific weather.")

    locations = st.session_state.get("farm_location_options", [])
    if locations:
        labels = [
            f"{item['name']}, {item['district']}, {item['state']}"
            for item in locations
        ]
        selected_label = st.selectbox("📍 Choose a matching location", labels)
        selected_location = locations[labels.index(selected_label)]
        st.session_state["farm_location"] = selected_location
        if not district:
            district = selected_location["district"]

    if submitted:
        if not district.strip():
            st.error("Enter a district before building a farm plan.")
            return
        try:
            farm_input = FarmInput(
                state=state,
                district=district.strip(),
                latitude=selected_location.get("latitude") if selected_location else None,
                longitude=selected_location.get("longitude") if selected_location else None,
                farm_size_acres=area,
                soil_type=soil or None,
                season=season,
                irrigation_type=irrigation or None,
                target_crop=target_crop.strip() or None,
                budget_inr=budget or None,
                language_preference=language,
                query=query.strip() or None,
            )
            with st.spinner("Your crop, soil, weather, and input specialists are preparing recommendations…"):
                result = _build_farm_suggestions(
                    farm_input,
                    user,
                    generate_request_id(),
                )
            st.session_state["last_farm_suggestions"] = result
            st.success("Your farm plan is ready.")
        except Exception as error:
            st.error(f"Farm plan could not be generated: {error}")

    result = st.session_state.get("last_farm_suggestions")
    if not result:
        return

    provider = result.get("ai_provider") or ai_service.status()
    if provider.get("configured"):
        st.caption(f"AI adviser: {provider.get('provider')} · {provider.get('model')}")
    else:
        st.info("AI provider is not configured. Rule-based farm recommendations remain available.")

    crop_col, seed_col = st.columns(2)
    with crop_col:
        def show_crops() -> None:
            crops = result.get("crop_recommendations", [])
            if not crops:
                st.caption("No crop matches were returned. Try adding soil, season, and water details.")
            for crop in crops:
                st.markdown(
                    f"**{crop['crop_name']} · {round(crop['confidence_score'] * 100)}% match**"
                )
                st.write(
                    f"{crop['water_requirement']} water · {crop['season']} · "
                    f"{crop['expected_yield_quintal_per_acre']} qtl/acre estimated yield"
                )
                st.caption(crop["reasoning"])

        render_suggestion_card("🌱 Crop choices", "crops.svg", show_crops)
    with seed_col:
        def show_seeds() -> None:
            seeds = result.get("seed_recommendations", [])
            if not seeds:
                st.caption("Choose a crop to see seed and variety guidance.")
            for seed in seeds:
                st.markdown(f"**{seed.get('variety_name') or seed.get('name', 'Suggested variety')}**")
                st.write(" · ".join(str(value) for value in (
                    seed.get("duration"), seed.get("yield"), seed.get("seed_rate"),
                    seed.get("region"), seed.get("certified_by"),
                ) if value))

        render_suggestion_card("🌾 Seed & varieties", "seeds.svg", show_seeds)

    fertilizer_col, regional_col = st.columns(2)
    with fertilizer_col:
        def show_fertilizers() -> None:
            fertilizers = result.get("fertilizer_plan", [])
            if not fertilizers:
                st.caption("Select a crop to see a fertilizer plan.")
            for item in fertilizers:
                st.markdown(f"**{item['fertilizer_name']} · {item['quantity_kg_per_acre']} kg/acre**")
                st.write(
                    f"{item['application_timing']} · {item['application_method']} · "
                    f"₹{item['estimated_cost_inr']}/acre (estimate)"
                )

        render_suggestion_card("🧪 Fertilizer plan", "fertilizer.svg", show_fertilizers)
    with regional_col:
        def show_regional_crops() -> None:
            intelligence = result.get("regional_intelligence") or {}
            for crop in intelligence.get("specialty_crops", []):
                st.markdown(f"**{crop}**")
            st.caption(intelligence.get("crop_reference_note") or get_crop_reference_note())
            st.warning("Indicative regional candidates only. Check local soil, season, water, and extension advice.")

        render_suggestion_card("📍 Regional specialty crops · indicative", "regional.svg", show_regional_crops)

    weather = result.get("weather") or {}
    weather_col, soil_col = st.columns(2)
    with weather_col:
        def show_weather() -> None:
            forecast = weather.get("forecast", [])
            if weather.get("source"):
                st.caption(f"Forecast source: {weather['source']}")
            if not forecast:
                st.caption("Weather is unavailable until a location is selected.")
            for day in forecast[:5]:
                st.markdown(f"**{day['date']} · {day['condition']}**")
                st.write(
                    f"{day['temp_min_c']}–{day['temp_max_c']} °C · "
                    f"{day['rainfall_mm']} mm rain · {day['advisory']}"
                )

        render_suggestion_card("🌦️ Local weather", "weather.svg", show_weather)
    with soil_col:
        def show_soil_water() -> None:
            soil_health = result.get("soil_health") or {}
            if soil_health:
                st.markdown(
                    f"**Modeled soil estimate: {soil_health.get('health_status')} · "
                    f"score {soil_health.get('health_score')}/100**"
                )
                st.write(
                    f"Estimated pH {soil_health.get('ph_level')} · "
                    f"{soil_health.get('texture')} · confirm with a soil test."
                )
            plan = result.get("irrigation_plan") or {}
            if plan:
                st.markdown(f"**Water plan: {plan.get('irrigation_system', 'field-based schedule')}**")
                st.write(" ".join(plan.get("general_advice", [])) or plan.get("recommendation", ""))

        render_suggestion_card("🧱 Soil & water", "soil-water.svg", show_soil_water)

    market_col, adviser_col = st.columns(2)
    with market_col:
        def show_market() -> None:
            prices = (result.get("market") or {}).get("prices", [])
            if not prices:
                st.caption("No market estimate is available for this plan.")
            for price in prices[:3]:
                st.markdown(f"**{price['commodity']} · {price['market']}**")
                st.write(
                    f"₹{price['modal_price_inr_per_quintal']}/quintal · "
                    f"{price['price_trend']} trend · illustrative estimate, not a live quote"
                )

        render_suggestion_card("📈 Local market estimate", "market.svg", show_market)
    with adviser_col:
        def show_adviser() -> None:
            if result.get("ai_advice"):
                st.write(result["ai_advice"])
            else:
                st.caption("Configure an AI provider in Streamlit secrets to enable generated agronomist advice.")

        render_suggestion_card("🤖 Farm adviser", "diary.svg", show_adviser)


def render_crop_tracker(user: Dict[str, Any], profile: Dict[str, Any]) -> None:
    st.subheader("🚜 Crop tracker")
    with st.form("crop_cycle_form"):
        crop_choice = st.selectbox(
            "🌱 Select a crop",
            ["Choose a crop", *get_crop_name_options(), "Other / not listed"],
        )
        crop = (
            st.text_input("🌿 Crop name") if crop_choice == "Other / not listed"
            else "" if crop_choice == "Choose a crop"
            else crop_choice
        )
        if crop and get_crop_duration_days(crop):
            st.caption(
                f"Indicative reference duration: about {get_crop_duration_days(crop)} days. "
                "Variety, climate, and local practice can change this."
            )
        variety = st.text_input("🌾 Variety (optional)")
        season = st.selectbox("🗓️ Growing season", [item.value for item in Season])
        area = st.number_input(
            "📐 Field area (acres)",
            min_value=0.1,
            value=float(profile.get("farm_size_acres") or 1.0),
            step=0.1,
        )
        sowing_date = st.date_input("🌱 Sowing date (optional)", value=None)
        harvest_date = st.date_input("🌾 Expected harvest (optional)", value=None)
        submitted = st.form_submit_button("🚜 Start tracking crop", type="primary")
    if submitted:
        if not crop.strip():
            st.error("Choose a crop or select “Other / not listed” and enter its name.")
        elif sowing_date and harvest_date and harvest_date <= sowing_date:
            st.error("Expected harvest must be after sowing.")
        else:
            duration_days = get_crop_duration_days(crop)
            expected_harvest = harvest_date
            if not expected_harvest and sowing_date and duration_days:
                expected_harvest = sowing_date + timedelta(days=duration_days)
            result = db_service.create_crop_cycle(user["id"], {
                "crop_name": crop.strip(),
                "variety": variety.strip() or None,
                "season": season,
                "field_area_acres": area,
                "soil_type": profile.get("soil_type"),
                "sowing_date": sowing_date.isoformat() if sowing_date else None,
                "expected_harvest_date": expected_harvest.isoformat() if expected_harvest else None,
            })
            if result.get("success"):
                st.success(f"Crop tracking started for {crop.strip()}.")
            else:
                st.error(result.get("error", "Crop cycle could not be created."))

    cycles = db_service.get_crop_cycles(user["id"])
    if cycles:
        for cycle in cycles:
            with st.container(border=True):
                st.markdown(f"**{cycle['crop_name'].title()}** · {cycle.get('variety') or 'Variety not set'}")
                st.caption(
                    f"{cycle.get('season') or 'Season not set'} · "
                    f"{cycle.get('field_area_acres') or '—'} acres · "
                    f"{cycle.get('status', 'planned').title()}"
                )
                render_crop_cycle_schedule(user["id"], cycle)
    else:
        st.info("Your crop cycles will appear here after you start tracking a crop.")

    with st.expander("📚 Crop seasons and classifications"):
        st.caption(
            "Season windows and crop uses are broad Indian references. Actual planting dates and "
            "classifications vary by state, district, variety, and market."
        )
        season_tab, category_tab = st.tabs(["🗓️ Growing seasons", "🌿 Crop categories"])
        with season_tab:
            for season_info in get_crop_seasons():
                with st.container(border=True):
                    st.markdown(f"#### {season_info['name']}")
                    st.write(season_info["description"])
                    st.caption(f"Examples: {season_info['examples']}")
        with category_tab:
            for category in get_crop_categories():
                with st.container(border=True):
                    st.markdown(f"#### {category['name']}")
                    st.write(category["purpose"])
                    st.caption(f"Examples: {category['examples']}")


def render_crop_cycle_schedule(user_id: str, cycle: Dict[str, Any]) -> None:
    """Render a date-specific crop guide and allow saving its checks to the diary."""
    crop_name = cycle["crop_name"]
    cycle_id = cycle["id"]
    with st.expander(f"📅 Daily growing guide · {crop_name.title()}"):
        sowing_value = cycle.get("sowing_date")
        if not sowing_value:
            st.info("Add the sowing date to build a day-by-day growing guide.")
            with st.form(f"crop_start_dates_{cycle_id}"):
                sowing_date = st.date_input("🌱 Sowing date", value=None, key=f"crop_sow_{cycle_id}")
                harvest_date = st.date_input(
                    "🌾 Expected harvest (optional)",
                    value=None,
                    key=f"crop_harvest_{cycle_id}",
                )
                save_dates = st.form_submit_button("💾 Save crop dates")
            if save_dates:
                if not sowing_date:
                    st.error("Enter the sowing date to start the growing guide.")
                    return
                duration = get_crop_duration_days(crop_name)
                expected_harvest = harvest_date or (
                    sowing_date + timedelta(days=duration) if duration else None
                )
                if expected_harvest and expected_harvest <= sowing_date:
                    st.error("Expected harvest must be after sowing.")
                    return
                updates = {"sowing_date": sowing_date.isoformat()}
                if expected_harvest:
                    updates["expected_harvest_date"] = expected_harvest.isoformat()
                result = db_service.update_crop_cycle(cycle_id, updates)
                if result.get("success"):
                    st.rerun()
                st.error(result.get("error", "Could not save crop dates."))
            return

        sowing_date = date.fromisoformat(str(sowing_value)[:10])
        harvest_value = cycle.get("expected_harvest_date")
        expected_harvest = (
            date.fromisoformat(str(harvest_value)[:10]) if harvest_value else None
        )
        try:
            guide = build_daily_crop_schedule(crop_name, sowing_date, expected_harvest)
        except ValueError as error:
            st.warning(str(error))
            with st.form(f"crop_expected_harvest_{cycle_id}"):
                harvest_date = st.date_input(
                    "🌾 Expected harvest date",
                    value=None,
                    key=f"crop_expected_date_{cycle_id}",
                )
                save_harvest_date = st.form_submit_button("💾 Save expected harvest date")
            if save_harvest_date:
                if not harvest_date or harvest_date <= sowing_date:
                    st.error("Choose an expected harvest date after sowing.")
                    return
                result = db_service.update_crop_cycle(
                    cycle_id,
                    {"expected_harvest_date": harvest_date.isoformat()},
                )
                if result.get("success"):
                    st.rerun()
                st.error(result.get("error", "Could not save expected harvest date."))
            return

        duration = guide["duration_days"]
        current_day = max(0, min(duration, (date.today() - sowing_date).days))
        st.caption(
            f"{duration} days after sowing · expected harvest {guide['expected_harvest_date']} · "
            f"duration: {guide['duration_source']}"
        )
        st.progress(round(current_day / max(duration, 1) * 100))
        selected_day = st.slider(
            "📆 Choose a day after sowing",
            min_value=0,
            max_value=duration,
            value=current_day,
            key=f"crop_schedule_day_{cycle_id}",
        )
        schedule_day = guide["daily_schedule"][selected_day]
        st.markdown(
            f"**Day {selected_day} · {schedule_day['date']} · "
            f"{schedule_day['growth_stage']}**"
        )
        st.write(schedule_day["daily_check"])
        st.info(schedule_day["stage_guidance"])
        if schedule_day["weekly_or_milestone_task"]:
            st.caption(schedule_day["weekly_or_milestone_task"])
        st.warning(guide["caveat"])

        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=guide["daily_schedule"][0].keys())
        writer.writeheader()
        writer.writerows(guide["daily_schedule"])
        st.download_button(
            "⬇️ Download every day's schedule (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"crop-schedule-{cycle_id}.csv",
            mime="text/csv",
            key=f"crop_schedule_download_{cycle_id}",
        )
        if st.button(
            "📓 Add selected day's check to farm diary",
            key=f"crop_schedule_diary_{cycle_id}",
        ):
            db_service.add_farm_record({
                "user_id": user_id,
                "crop_cycle_id": cycle_id,
                "crop_name": crop_name,
                "record_type": "note",
                "date": schedule_day["date"],
                "details": (
                    f"Day {selected_day} · {schedule_day['growth_stage']}: "
                    f"{schedule_day['daily_check']} {schedule_day['stage_guidance']}"
                ),
                "metadata": {
                    "source": "daily_crop_guide",
                    "day_after_sowing": selected_day,
                },
            })
            st.success("Crop check added to your farm diary.")


def render_farm_diary(user: Dict[str, Any]) -> None:
    st.subheader("📓 Farm diary")
    crop_cycles = db_service.get_crop_cycles(user["id"])
    cycle_labels = {
        f"{cycle['crop_name'].title()} · {cycle['season'] or 'Season not set'} · {cycle['id'][:8]}":
            cycle
        for cycle in crop_cycles
    }
    with st.form("farm_record_form"):
        record_type = st.selectbox(
            "📋 Record type",
            [
                "sowing", "irrigation", "fertilizer", "weeding", "pest_control",
                "spraying", "harvest", "expense", "income", "note",
            ],
        )
        activity_date = st.date_input("📅 Activity date", value=date.today())
        crop_label = st.selectbox("🌱 Crop cycle", ["General farm", *cycle_labels])
        details = st.text_area("📝 What happened?")
        amount = st.number_input("💰 Amount in rupees (optional)", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("💾 Save field record", type="primary")
    if submitted:
        if not details.strip():
            st.error("Add a short description before saving the record.")
        else:
            db_service.add_farm_record({
                "user_id": user["id"],
                "crop_cycle_id": cycle_labels[crop_label]["id"] if crop_label in cycle_labels else None,
                "crop_name": cycle_labels[crop_label]["crop_name"] if crop_label in cycle_labels else None,
                "record_type": record_type,
                "date": activity_date.isoformat(),
                "details": details.strip(),
                "amount_inr": amount or None,
                "metadata": {"logged_by": "streamlit"},
            })
            st.success("Field record saved.")

    records = db_service.get_farm_records(user["id"])
    if records:
        for record in records[:20]:
            amount_text = f" · ₹{record['amount_inr']:,.0f}" if record.get("amount_inr") else ""
            crop_text = f" · {record['crop_name'].title()}" if record.get("crop_name") else ""
            st.markdown(
                f"**{record['record_type'].replace('_', ' ').title()}** · "
                f"{record['date'][:10]}{crop_text}{amount_text}  \n{record['details']}"
            )
            st.divider()
    else:
        st.info("Your saved field records will appear here.")


def render_livestock(user: Dict[str, Any]) -> None:
    st.subheader("🐄 Livestock & dairy records")
    st.caption("Keep production and animal-health notes alongside your crop records.")
    with st.form("livestock_record_form"):
        animal = st.text_input("🐄 Animal or flock (for example, dairy cows or poultry)")
        activity = st.selectbox(
            "🥛 Production or care record",
            ["Milk production", "Egg production", "Animal count", "Health / vaccination", "Feed"],
        )
        quantity_col, unit_col = st.columns(2)
        with quantity_col:
            quantity = st.number_input("📦 Quantity (optional)", min_value=0.0, step=1.0)
        with unit_col:
            unit = st.selectbox("📏 Unit", ["litres", "eggs", "animals", "kg", "other"])
        financial_type = st.selectbox("💳 Financial category (optional)", ["None", "Income", "Expense"])
        amount = st.number_input("💰 Income or expense (₹, optional)", min_value=0.0, step=100.0)
        details = st.text_area("📝 Notes (for example, feed, symptoms, or treatment)")
        submitted = st.form_submit_button("💾 Save livestock record", type="primary")
    if submitted:
        if not animal.strip() or (quantity == 0 and not details.strip()):
            st.error("Enter an animal or flock and a quantity or note.")
        elif amount > 0 and financial_type == "None":
            st.error("Choose whether the livestock amount is income or expense.")
        else:
            record_type = "income" if financial_type == "Income" else (
                "expense" if financial_type == "Expense" else "livestock"
            )
            description = f"{activity}: {animal.strip()}"
            if details.strip():
                description += f" — {details.strip()}"
            db_service.add_farm_record({
                "user_id": user["id"],
                "record_type": record_type,
                "details": description,
                "amount_inr": amount or None,
                "metadata": {
                    "livestock": True,
                    "animal": animal.strip(),
                    "activity": activity,
                    "quantity": quantity or None,
                    "unit": unit,
                },
            })
            st.success("Livestock record saved.")

    records = [
        record for record in db_service.get_farm_records(user["id"])
        if record.get("metadata", {}).get("livestock")
    ]
    milk_total = sum(
        record["metadata"].get("quantity") or 0
        for record in records
        if record["metadata"].get("activity") == "Milk production"
        and record["metadata"].get("unit") == "litres"
    )
    eggs_total = sum(
        record["metadata"].get("quantity") or 0
        for record in records
        if record["metadata"].get("activity") == "Egg production"
        and record["metadata"].get("unit") == "eggs"
    )
    metric_a, metric_b = st.columns(2)
    metric_a.metric("🥛 Milk logged · all time", f"{milk_total:,.1f} L")
    metric_b.metric("🥚 Eggs logged · all time", f"{eggs_total:,.0f}")
    if records:
        for record in records[:20]:
            amount_text = f" · ₹{record['amount_inr']:,.0f}" if record.get("amount_inr") else ""
            quantity_value = record.get("metadata", {}).get("quantity")
            unit = record.get("metadata", {}).get("unit", "")
            quantity_text = f" · {quantity_value:g} {unit}" if quantity_value else ""
            st.markdown(
                f"**{record['date'][:10]}** · {record['details']}{quantity_text}{amount_text}"
            )
            st.divider()
    else:
        st.info("Your milk, poultry, feed, and animal-health records will appear here.")


def render_marketplace(user: Dict[str, Any]) -> None:
    st.subheader("🛒 Farm input marketplace")
    st.caption(
        "Browse the bundled demo catalogue. Prices, stock, sellers, and cart are sample data; "
        "this prototype does not process payments or connect produce sellers to buyers."
    )
    with st.form("marketplace_search_form"):
        query_col, category_col, crop_col = st.columns(3)
        with query_col:
            query = st.text_input("🔎 Search farm inputs")
        with category_col:
            category = st.selectbox(
                "🗂️ Category",
                ["All", "seed", "fertilizer", "pesticide", "equipment"],
                format_func=lambda value: "All categories" if value == "All" else value.title(),
            )
        with crop_col:
            crop = st.text_input("🌱 Crop filter (optional)")
        searched = st.form_submit_button("🔎 Search catalogue")

    if searched or "marketplace_products" not in st.session_state:
        st.session_state["marketplace_products"] = ec_service_instance.search_products(
            query=query.strip() or None,
            category=None if category == "All" else category,
            crop=crop.strip() or None,
        )
    products = st.session_state["marketplace_products"]
    if not products:
        st.info("No demo catalogue products match these filters.")
    for offset in range(0, len(products), 2):
        columns = st.columns(2)
        for column, product in zip(columns, products[offset:offset + 2]):
            with column:
                with st.container(border=True):
                    st.markdown(f"#### {product['name']}")
                    st.write(product["description"])
                    st.caption(
                        f"{product['category'].title()} · {product['seller']} · "
                        f"₹{product['price_inr']:,.0f}/{product['unit']} · "
                        f"{product['stock_quantity']} in sample stock"
                    )
                    quantity = st.number_input(
                        f"📦 Quantity ({product['unit']})",
                        min_value=0.1,
                        max_value=float(max(product["stock_quantity"], 0.1)),
                        value=1.0,
                        step=0.1,
                        key=f"market_quantity_{product['id']}",
                        disabled=product["stock_quantity"] <= 0,
                    )
                    if st.button(
                        "🛒 Add to demo cart",
                        key=f"market_add_{product['id']}",
                        disabled=product["stock_quantity"] <= 0,
                    ):
                        result = ec_service_instance.add_to_cart(
                            user["id"], product["id"], quantity
                        )
                        if result.get("success"):
                            st.success("Added to your demo cart.")
                        else:
                            st.error(result.get("error", "Could not add this item."))

    cart = ec_service_instance.get_cart(user["id"])
    if cart["items"]:
        with st.expander(f"🛒 Demo cart · {len(cart['items'])} line items"):
            for item in cart["items"]:
                st.write(
                    f"{item['quantity']:g} × {item['product']['name']} — "
                    f"₹{item['item_total']:,.0f}"
                )
            st.metric("💳 Estimated sample total (includes demo delivery)", f"₹{cart['total']:,.0f}")


def render_crop_health() -> None:
    st.subheader("🩺 Crop health check")
    st.caption(
        "Photo-based detection requires a trained disease model. Computer-vision results are not "
        "a diagnosis; confirm symptoms with a KVK or agricultural extension expert."
    )
    if disease_service_instance.model_loaded:
        crop = st.text_input("🌱 Crop in the photo", key="health_image_crop")
        uploaded = st.file_uploader(
            "📷 Upload a clear leaf or crop image (PNG or JPEG)",
            type=["png", "jpg", "jpeg"],
            key="health_image",
        )
        if uploaded is not None and st.button("🔬 Analyze crop photo", type="primary"):
            if not crop.strip():
                st.error("Enter the crop name before analyzing the image.")
                return
            image_bytes = uploaded.getvalue()
            if len(image_bytes) > 10 * 1024 * 1024:
                st.error("Choose an image smaller than 10 MB.")
                return
            try:
                with Image.open(io.BytesIO(image_bytes)) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError):
                st.error("The uploaded file is not a valid PNG or JPEG image.")
                return

            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=Path(uploaded.name).suffix,
                    delete=False,
                ) as image_file:
                    image_file.write(image_bytes)
                    temporary_path = image_file.name
                result = disease_service_instance.detect_from_image(temporary_path, crop.strip())
            except OSError as error:
                st.error(f"Could not analyze the uploaded photo: {error}")
                return
            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)

            if result.get("disease_name") == "Unable to detect":
                st.warning(result.get("message", "The model could not assess this photo."))
            elif result.get("detection_method") != "yolov11_cv":
                st.warning(
                    "The trained model did not return a disease classification. "
                    "Do not use a fallback result as a diagnosis."
                )
            else:
                st.markdown(f"**Possible issue:** {result.get('disease_name', 'No result')}")
                confidence = result.get("confidence")
                if confidence is not None:
                    st.caption(
                        f"Model confidence: {confidence:.0%} · "
                        f"Severity estimate: {result.get('severity', 'unknown')}"
                    )
                if result.get("symptoms"):
                    st.markdown("**Symptoms in the reference:** " + "; ".join(result["symptoms"]))
                if result.get("preventive_measures"):
                    st.markdown("**Preventive checks:** " + "; ".join(result["preventive_measures"]))
                st.warning(
                    "Do not apply a pesticide based only on this result. Verify the diagnosis, "
                    "product label, crop approval, dosage, and waiting period with a local expert."
                )
    else:
        st.warning(
            "Photo recognition is unavailable because no trained model is installed. "
            "You can still compare reported symptoms below; this does not analyze a photo."
        )
        st.caption(
            "To enable photo scanning, install a validated model at "
            "`data/models/disease_detection.pt`; the repository does not include trained weights."
        )

    st.divider()
    st.markdown("#### 🔎 Symptom-based check")
    st.caption(
        "Compare what you observe with the crop reference. This rule-based check is not an image "
        "diagnosis or confirmed disease identification."
    )
    crops = sorted({
        disease["crop"]
        for disease in disease_service_instance.disease_database.values()
    })
    if not crops:
        st.info("No crop symptom references are available.")
        return
    symptom_crop = st.selectbox("🌿 Crop with symptoms", crops, key="symptom_crop")
    references = disease_service_instance.get_all_diseases_for_crop(symptom_crop)
    symptom_labels = {
        f"{reference['disease_name']} · {symptom}": symptom
        for reference in references
        for symptom in reference["symptoms"]
    }
    selected_labels = st.multiselect(
        "👀 Select visible symptoms from the reference",
        list(symptom_labels),
        key="symptom_reference_choices",
    )
    other_symptoms = st.text_area(
        "📝 Other symptoms (one per line)",
        key="symptom_free_text",
    )
    if st.button("🧩 Compare reported symptoms", key="compare_symptoms"):
        symptoms = [symptom_labels[label] for label in selected_labels]
        symptoms.extend(
            symptom.strip()
            for symptom in other_symptoms.splitlines()
            if symptom.strip()
        )
        if not symptoms:
            st.error("Select or describe at least one visible symptom.")
            return
        result = disease_service_instance.detect_from_symptoms(symptom_crop, symptoms)
        if result.get("disease_name") == "Unknown / Complex Condition":
            st.warning(result.get("message", "No close symptom reference was found."))
            st.info(result.get("recommendation", "Ask a local agricultural extension expert."))
            return
        st.markdown(f"**Possible symptom match:** {result['disease_name']}")
        st.caption("Rule-based reference match only; it is not a diagnosis or probability score.")
        if result.get("matched_symptoms"):
            st.markdown("**Matching reference symptoms:** " + "; ".join(result["matched_symptoms"]))
        if result.get("preventive_measures"):
            st.markdown("**General prevention references:** " + "; ".join(result["preventive_measures"]))
        st.warning(
            "Confirm the cause with a KVK or agricultural expert before treatment. "
            "Do not apply pesticides based only on this symptom match."
        )


def render_scheme_and_daily_updates(profile: Dict[str, Any], cycles: list) -> None:
    st.subheader("📰 Daily agriculture brief")
    update = get_daily_agriculture_update()
    st.caption(f"Farm checklist for {update['date']} · not live news headlines")
    st.markdown(f"**{update['checklist_title']}:** {update['checklist']}")
    st.info(update["seasonal_focus"])
    source_links = " · ".join(
        f"[{source['name']}]({source['url']})" for source in update["official_sources"]
    )
    st.markdown(f"🔗 Official sources: {source_links}")

    st.divider()
    st.subheader("🏛️ Government schemes")
    state = profile.get("state") or "India"
    crop = next(
        (cycle.get("crop_name") for cycle in cycles if cycle.get("status") not in {"completed", "sold"}),
        None,
    )
    schemes = gov_scheme_service_instance.get_relevant_schemes(
        state,
        crop,
        float(profile.get("farm_size_acres") or 0) or None,
    )
    st.caption(
        f"National programs relevant to {state}"
        + (f" and {crop}" if crop else "")
        + ". Confirm current eligibility, benefits, and application dates with the official portal "
        "or your state agriculture department."
    )
    for scheme in schemes:
        with st.expander(f"📜 {scheme['scheme_name']} · {scheme['coverage']}"):
            st.write(scheme["description"])
            st.markdown(f"**Eligibility:** {'; '.join(scheme['eligibility'])}")
            st.markdown(f"**Benefits:** {'; '.join(scheme['benefits'])}")
            st.markdown(f"**How to check/apply:** {scheme['application_process']}")
            st.caption(f"Application timing: {scheme['deadline']}")
            st.markdown(f"[Official scheme information]({scheme['official_link']})")
    st.markdown(
        f"**Find state-specific programs for {state}:** "
        "[Search the Government of India's myScheme portal](https://www.myscheme.gov.in/). "
        "State schemes and enrollment windows change; verify them with the relevant department."
    )


def render_farmer_services() -> None:
    st.subheader("🧭 Farmer apps & public agriculture services")
    st.caption(
        "A directory of the services you named. Links open their publishers or official portals; "
        "they are not partnerships or live integrations with this project."
    )
    st.info(
        "Available inside this project: crop planning, weather forecasts, crop tracking, farm and "
        "livestock records, calculators, scheme references, and a model-dependent crop photo check."
    )
    tools = list_farmer_tools()
    category_col, search_col = st.columns(2)
    with category_col:
        category = st.selectbox("🗂️ Service type", ["All", "Government", "Private"])
    with search_col:
        search = st.text_input("🔎 Find a service")
    search_term = search.strip().casefold()
    visible_tools = [
        tool for tool in tools
        if (category == "All" or tool["category"] == category)
        and (
            not search_term
            or search_term in tool["name"].casefold()
            or search_term in tool["best_for"].casefold()
            or search_term in tool["features"].casefold()
        )
    ]
    for offset in range(0, len(visible_tools), 3):
        columns = st.columns(3)
        for column, tool in zip(columns, visible_tools[offset:offset + 3]):
            with column:
                with st.container(border=True):
                    st.markdown(f"#### 🌐 {tool['name']}")
                    st.caption(f"{tool['category']} · {tool['publisher']}")
                    st.markdown(f"**Best for:** {tool['best_for']}")
                    st.write(tool["features"])
                    st.link_button("↗️ Open service", tool["url"], use_container_width=True)
    if not visible_tools:
        st.info("No services match that search.")
    st.caption(
        "Check each publisher's current availability, eligibility, fees, and privacy terms. "
        "This app does not send your farm profile to these services."
    )


def render_calculators(profile: Dict[str, Any]) -> None:
    st.subheader("🧮 Farm calculators")
    st.caption(
        "Calculations use only the figures you enter. They do not recommend fertilizer rates, "
        "predict guaranteed yields, or replace local market quotes."
    )
    fertilizer_tab, budget_tab = st.tabs(
        ["🧪 Fertilizer quantity & cost", "💰 Crop budget & returns"]
    )
    with fertilizer_tab:
        st.markdown("#### ⚖️ Scale a confirmed per-acre application rate")
        area = st.number_input(
            "📐 Field area (acres)",
            min_value=0.1,
            value=max(float(profile.get("farm_size_acres") or 1.0), 0.1),
            step=0.1,
            key="calculator_fertilizer_area",
        )
        rows = []
        for index in range(1, 4):
            name_col, rate_col, price_col = st.columns(3)
            with name_col:
                name = st.text_input(f"🧪 Input {index}", key=f"calculator_input_name_{index}")
            with rate_col:
                rate = st.number_input(
                    f"📏 Rate kg/acre {index}",
                    min_value=0.0,
                    step=1.0,
                    key=f"calculator_input_rate_{index}",
                )
            with price_col:
                price = st.number_input(
                    f"💰 Price ₹/kg {index} (optional)",
                    min_value=0.0,
                    step=1.0,
                    key=f"calculator_input_price_{index}",
                )
            if name.strip() and rate > 0:
                rows.append((name.strip(), calculate_fertilizer_requirement(
                    area, rate, price if price > 0 else None
                )))
        if rows:
            for name, result in rows:
                cost = result.get("estimated_cost_inr")
                cost_text = f" · estimated cost ₹{cost:,.0f}" if cost is not None else ""
                st.write(f"**{name}:** {result['quantity_kg']:,.2f} kg for {area:g} acres{cost_text}")
        else:
            st.info("Enter an input name and a per-acre rate to calculate the required quantity.")
        st.caption("Use a rate confirmed by a soil test, crop recommendation, or local extension expert.")

    with budget_tab:
        st.markdown("#### 📊 Estimate whole-field crop returns")
        budget_area = st.number_input(
            "📐 Field area (acres)",
            min_value=0.1,
            value=max(float(profile.get("farm_size_acres") or 1.0), 0.1),
            step=0.1,
            key="calculator_budget_area",
        )
        yield_rate = st.number_input("🌾 Estimated yield (quintals/acre)", min_value=0.0, step=1.0)
        sale_price = st.number_input("💹 Expected sale price (₹/quintal)", min_value=0.0, step=100.0)
        crop_cost = st.number_input("🧾 Estimated production cost (₹/acre)", min_value=0.0, step=1000.0)
        estimate = estimate_crop_budget(budget_area, yield_rate, sale_price, crop_cost)
        metric_a, metric_b = st.columns(2)
        metric_a.metric("🌾 Estimated whole-field yield", f"{estimate['total_yield_quintal']:,.2f} qtl")
        metric_b.metric("💹 Estimated gross revenue", f"₹{estimate['gross_revenue_inr']:,.0f}")
        metric_c, metric_d = st.columns(2)
        metric_c.metric("🧾 Estimated total cost", f"₹{estimate['total_cost_inr']:,.0f}")
        metric_d.metric("💰 Estimated net return", f"₹{estimate['estimated_net_inr']:,.0f}")


def main() -> None:
    banner = base64.b64encode((FRONTEND / "farm-hero.png").read_bytes()).decode("ascii")
    st.markdown(
        f'<img class="farm-project-banner" src="data:image/png;base64,{banner}" '
        'alt="AI Farming Project banner showing crop fields, livestock, and a tractor">',
        unsafe_allow_html=True,
    )
    st.title("🌾 Your farm, one clear plan.")
    st.caption(
        "Field-aware crop planning, weather guidance, crop tracking, and farm records for Indian farmers."
    )

    user_id = st.session_state.get("farmer_user_id")
    user = user_from_id(user_id) if user_id else None
    if not user:
        st.session_state.pop("farmer_user_id", None)
        render_authentication()
        return

    profile = render_profile(user)
    cycles = db_service.get_crop_cycles(user["id"])
    records = db_service.get_farm_records(user["id"])
    income = sum(
        record.get("amount_inr") or 0
        for record in records
        if record.get("record_type") == "income"
        or record.get("metadata", {}).get("financial_type") == "income"
    )
    expenses = sum(
        record.get("amount_inr") or 0
        for record in records
        if record.get("record_type") == "expense"
        or record.get("metadata", {}).get("financial_type") == "expense"
    )
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("🌱 Crop cycles", len(cycles))
    metric_b.metric("📒 Field records", len(records))
    metric_c.metric("💰 Recorded net balance", f"₹{income - expenses:,.0f}")

    plan_tab, tracker_tab, diary_tab, livestock_tab, health_tab, market_tab, schemes_tab, calculator_tab, services_tab = st.tabs(
        [
            "🌱 Farm plan",
            "🚜 Crop tracker",
            "📓 Farm diary",
            "🐄 Livestock",
            "🩺 Crop health",
            "🛒 Marketplace",
            "🏛️ Schemes & updates",
            "🧮 Calculators",
            "🧭 Services hub",
        ]
    )
    with plan_tab:
        render_farm_plan(user, profile)
    with tracker_tab:
        render_crop_tracker(user, profile)
    with diary_tab:
        render_farm_diary(user)
    with livestock_tab:
        render_livestock(user)
    with health_tab:
        render_crop_health()
    with market_tab:
        render_marketplace(user)
    with schemes_tab:
        render_scheme_and_daily_updates(profile, cycles)
    with calculator_tab:
        render_calculators(profile)
    with services_tab:
        render_farmer_services()

    st.caption(
        "Regional crop entries and modeled estimates are decision support, not guarantees. "
        "Confirm advice with soil tests and local agricultural extension services."
    )


if __name__ == "__main__":
    main()
