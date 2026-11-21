"""Streamlit dashboard for deploying AI Farmer on Streamlit Community Cloud."""
import base64
import os
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st


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
from app.services.india_languages import LANGUAGE_NAMES
from app.services.location_service import location_service
from app.services.ai_service import ai_service
from app.utils import generate_request_id

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: linear-gradient(rgba(238, 246, 235, .82), rgba(238, 246, 235, .88)),
            url("data:image/png;base64,__FARM_BACKGROUND__");
        background-position: center;
        background-size: cover;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(rgba(242, 248, 239, .93), rgba(242, 248, 239, .93)),
            url("data:image/png;base64,__FARM_BACKGROUND__");
        background-position: center;
        background-size: cover;
    }
    .block-container { max-width: 1180px; padding-top: 1.2rem; }
    [data-testid="stMetric"] { background: rgba(247, 252, 245, .94); border: 1px solid #d2e3d1; padding: 14px; border-radius: 12px; }
    [data-testid="stForm"], [data-testid="stTabs"] [role="tabpanel"] {
        background: rgba(255, 255, 255, .92);
        border: 1px solid rgba(202, 220, 199, .9);
        border-radius: 14px;
        padding: 1rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, .88);
        border-radius: 14px;
    }
    .farm-card { border: 1px solid #dce5de; border-radius: 14px; padding: 16px; background: rgba(255,255,255,.92); margin: 8px 0 16px; }
    .farm-card img { width: 100%; height: 100px; object-fit: cover; border-radius: 9px; margin-bottom: 10px; }
    .weather-panel { padding: 14px; border-radius: 12px; background: linear-gradient(110deg, #f3fbff, #e1f1f6); border: 1px solid #c9e2ec; }
    .muted { color: #64736a; font-size: .9rem; }
    img.farm-project-banner { display: block; width: 100%; height: auto; object-fit: contain; border: 1px solid #dce5de; border-radius: 16px; margin: 0 0 1.1rem; }
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
    st.subheader("Sign in to your farm workspace")
    login_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            phone = st.text_input("Indian mobile number", max_chars=10)
            password = st.text_input("Password", type="password", max_chars=72)
            submitted = st.form_submit_button("Sign in", type="primary")
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
            name = st.text_input("Your name", max_chars=100)
            phone = st.text_input("Indian mobile number", max_chars=10, key="register_phone")
            password = st.text_input(
                "Password (at least 6 characters)",
                type="password",
                max_chars=72,
                key="register_password",
            )
            submitted = st.form_submit_button("Create account", type="primary")
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
        st.markdown(f"### Welcome, {user['name']}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.pop("farmer_user_id", None)
            st.session_state.pop("last_farm_suggestions", None)
            st.rerun()

        with st.form("farm_profile"):
            st.markdown("#### Farm profile")
            regions = list_indian_regions()
            names = [region["name"] for region in regions]
            state_default = profile.get("state")
            state_index = names.index(state_default) if state_default in names else 0
            state = st.selectbox("State / union territory", names, index=state_index)
            district = st.text_input("District", value=profile.get("district") or "")
            area = st.number_input(
                "Farm area (acres)",
                min_value=0.1,
                value=float(profile.get("farm_size_acres") or 1.0),
                step=0.1,
            )
            soil_options = ["", *[soil.value for soil in SoilType]]
            soil_default = profile.get("soil_type") or ""
            soil = st.selectbox(
                "Soil type",
                soil_options,
                index=soil_options.index(soil_default) if soil_default in soil_options else 0,
            )
            irrigation_options = ["", *[item.value for item in IrrigationType]]
            irrigation_default = profile.get("irrigation_type") or ""
            irrigation = st.selectbox(
                "Water access",
                irrigation_options,
                index=irrigation_options.index(irrigation_default)
                if irrigation_default in irrigation_options else 0,
            )
            language_codes = ["en", *[item.value for item in FarmerLanguage if item.value != "en"]]
            language_default = profile.get("language_preference") or "en"
            language = st.selectbox(
                "AI advice language",
                language_codes,
                index=language_codes.index(language_default)
                if language_default in language_codes else 0,
                format_func=lambda code: LANGUAGE_NAMES[code],
            )
            saved = st.form_submit_button("Save farm profile", type="primary")
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
    st.subheader("Field-based farm plan")
    st.caption("Recommendations use your farm details, regional crop references, and available weather data.")
    regions = list_indian_regions()
    region_names = [region["name"] for region in regions]
    profile_state = profile.get("state")
    state_index = region_names.index(profile_state) if profile_state in region_names else 0

    with st.form("farm_plan_form"):
        state = st.selectbox("State / union territory", region_names, index=state_index)
        district = st.text_input("District", value=profile.get("district") or "")
        location_query = st.text_input("Town or village for local weather (optional)")
        search_location = st.form_submit_button("Find weather location")
        area = st.number_input(
            "Farm area (acres)",
            min_value=0.1,
            value=float(profile.get("farm_size_acres") or 1.0),
            step=0.1,
        )
        soil_options = ["", *[soil.value for soil in SoilType]]
        soil_default = profile.get("soil_type") or ""
        soil = st.selectbox(
            "Soil type",
            soil_options,
            index=soil_options.index(soil_default) if soil_default in soil_options else 0,
        )
        season = st.selectbox("Season", [season.value for season in Season])
        irrigation_options = ["", *[item.value for item in IrrigationType]]
        irrigation_default = profile.get("irrigation_type") or ""
        irrigation = st.selectbox(
            "Water access",
            irrigation_options,
            index=irrigation_options.index(irrigation_default)
            if irrigation_default in irrigation_options else 0,
        )
        target_crop = st.text_input("Crop you are growing or considering")
        budget = st.number_input("Budget in rupees (optional)", min_value=0, step=1000)
        language_codes = ["en", *[item.value for item in FarmerLanguage if item.value != "en"]]
        language_default = profile.get("language_preference") or "en"
        language = st.selectbox(
            "AI advice language",
            language_codes,
            index=language_codes.index(language_default)
            if language_default in language_codes else 0,
            format_func=lambda code: LANGUAGE_NAMES[code],
        )
        query = st.text_area("What would you like help with?")
        submitted = st.form_submit_button("Build my farm plan", type="primary")

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
        selected_label = st.selectbox("Choose a matching location", labels)
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

        render_suggestion_card("Crop choices", "crops.svg", show_crops)
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

        render_suggestion_card("Seed & varieties", "seeds.svg", show_seeds)

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

        render_suggestion_card("Fertilizer plan", "fertilizer.svg", show_fertilizers)
    with regional_col:
        def show_regional_crops() -> None:
            intelligence = result.get("regional_intelligence") or {}
            for crop in intelligence.get("specialty_crops", []):
                st.markdown(f"**{crop}**")
            st.caption(intelligence.get("crop_reference_note") or get_crop_reference_note())
            st.warning("Indicative regional candidates only. Check local soil, season, water, and extension advice.")

        render_suggestion_card("Regional specialty crops · indicative", "regional.svg", show_regional_crops)

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

        render_suggestion_card("Local weather", "weather.svg", show_weather)
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

        render_suggestion_card("Soil & water", "soil-water.svg", show_soil_water)

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

        render_suggestion_card("Local market estimate", "market.svg", show_market)
    with adviser_col:
        def show_adviser() -> None:
            if result.get("ai_advice"):
                st.write(result["ai_advice"])
            else:
                st.caption("Configure an AI provider in Streamlit secrets to enable generated agronomist advice.")

        render_suggestion_card("Farm adviser", "diary.svg", show_adviser)


def render_crop_tracker(user: Dict[str, Any], profile: Dict[str, Any]) -> None:
    st.subheader("Crop tracker")
    with st.form("crop_cycle_form"):
        crop = st.text_input("Crop name")
        variety = st.text_input("Variety (optional)")
        season = st.selectbox("Season", [item.value for item in Season])
        area = st.number_input(
            "Field area (acres)",
            min_value=0.1,
            value=float(profile.get("farm_size_acres") or 1.0),
            step=0.1,
        )
        sowing_date = st.date_input("Sowing date (optional)", value=None)
        harvest_date = st.date_input("Expected harvest (optional)", value=None)
        submitted = st.form_submit_button("Start tracking crop", type="primary")
    if submitted:
        if not crop.strip():
            st.error("Enter a crop name.")
        else:
            result = db_service.create_crop_cycle(user["id"], {
                "crop_name": crop.strip(),
                "variety": variety.strip() or None,
                "season": season,
                "field_area_acres": area,
                "soil_type": profile.get("soil_type"),
                "sowing_date": sowing_date.isoformat() if sowing_date else None,
                "expected_harvest_date": harvest_date.isoformat() if harvest_date else None,
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
                st.progress(max(0, min(100, cycle.get("progress_percent") or 0)))
                st.caption(
                    f"{cycle.get('season') or 'Season not set'} · "
                    f"{cycle.get('field_area_acres') or '—'} acres · "
                    f"{cycle.get('status', 'planned').title()}"
                )
    else:
        st.info("Your crop cycles will appear here after you start tracking a crop.")


def render_farm_diary(user: Dict[str, Any]) -> None:
    st.subheader("Farm diary")
    with st.form("farm_record_form"):
        record_type = st.selectbox(
            "Record type",
            ["irrigation", "fertilizer", "pest_control", "expense", "income", "note"],
        )
        details = st.text_area("What happened?")
        amount = st.number_input("Amount in rupees (optional)", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("Save field record", type="primary")
    if submitted:
        if not details.strip():
            st.error("Add a short description before saving the record.")
        else:
            db_service.add_farm_record({
                "user_id": user["id"],
                "record_type": record_type,
                "details": details.strip(),
                "amount_inr": amount or None,
                "metadata": {"logged_by": "streamlit"},
            })
            st.success("Field record saved.")

    records = db_service.get_farm_records(user["id"])
    if records:
        for record in records[:20]:
            amount_text = f" · ₹{record['amount_inr']:,.0f}" if record.get("amount_inr") else ""
            st.markdown(
                f"**{record['record_type'].replace('_', ' ').title()}** · "
                f"{record['date'][:10]}{amount_text}  \n{record['details']}"
            )
            st.divider()
    else:
        st.info("Your saved field records will appear here.")


def main() -> None:
    banner = base64.b64encode((FRONTEND / "farm-hero.png").read_bytes()).decode("ascii")
    st.markdown(
        f'<img class="farm-project-banner" src="data:image/png;base64,{banner}" '
        'alt="AI Farming Project banner showing crop fields, livestock, and a tractor">',
        unsafe_allow_html=True,
    )
    st.title("Your farm, one clear plan.")
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
    )
    expenses = sum(
        record.get("amount_inr") or 0
        for record in records
        if record.get("record_type") == "expense"
    )
    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Crop cycles", len(cycles))
    metric_b.metric("Field records", len(records))
    metric_c.metric("Recorded net balance", f"₹{income - expenses:,.0f}")

    plan_tab, tracker_tab, diary_tab = st.tabs(
        ["🌱 Farm plan", "🚜 Crop tracker", "📓 Farm diary"]
    )
    with plan_tab:
        render_farm_plan(user, profile)
    with tracker_tab:
        render_crop_tracker(user, profile)
    with diary_tab:
        render_farm_diary(user)

    st.caption(
        "Regional crop entries and modeled estimates are decision support, not guarantees. "
        "Confirm advice with soil tests and local agricultural extension services."
    )


if __name__ == "__main__":
    main()
