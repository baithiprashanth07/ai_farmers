"""FastAPI application for AI Farmer - Complete Production API v3.0."""
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.schemas.models import FarmInput, AI_FarmerResponse, FarmerLanguage
from app.schemas.state import AI_Farmer_State
from app.graph.supervisor import ai_farmer_graph, AGENTS, supervisor_router
from app.services.ai_service import ai_service
from app.services.location_service import location_service
from app.services.database import db_service
from app.services.agriculture_reference import list_indian_regions, get_crop_reference_note
from app.services.india_languages import INDIAN_LANGUAGES
from app.services.ecommerce_service import ec_service_instance
from app.services.auth_service import auth_service, verify_token
from app.services.notification_service import notification_service
from app.utils import logger, generate_request_id

app = FastAPI(
    title="AI Farmer",
    description="Production-grade Multi-Agent AI Platform for Smart Farming with Auth, Crop Lifecycle & E-Commerce",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

security = HTTPBearer(auto_error=False)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ============ AUTH DEPENDENCY ============
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@app.get("/api/v1/languages")
async def get_supported_languages():
    """List English and India's 22 scheduled languages."""
    return {"languages": [{"code": "en", "name": "English", "native_name": "English"}, *INDIAN_LANGUAGES]}


@app.get("/api/v1/regions")
async def get_indian_regions():
    """List indicative state/UT crops and specialty crops, not verified farm advice."""
    return {"regions": list_indian_regions(), "reference_note": get_crop_reference_note()}

# ============ HOME PAGE ============
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as index_file:
            return index_file.read()
    return _default_homepage()


@app.get("/service-worker.js")
async def get_service_worker():
    worker_path = os.path.join(frontend_path, "service-worker.js")
    return FileResponse(
        worker_path,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )

def _default_homepage():
    return """
    <!DOCTYPE html><html><head><title>AI Farmer</title>
    <style>body{font-family:system-ui;background:linear-gradient(135deg,#1a5d1a,#2d8a2d);color:white;text-align:center;padding:3rem}
    h1{font-size:3rem} .btn{background:#ff9800;color:white;padding:1rem 2rem;border-radius:30px;text-decoration:none;display:inline-block;margin:1rem}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem;max-width:1000px;margin:2rem auto}
    .card{background:rgba(255,255,255,0.15);padding:1.5rem;border-radius:15px}
    </style></head><body>
    <h1>🌾 AI Farmer v3.0</h1><p>Multi-Agent AI + Auth + Crop Lifecycle + E-Commerce</p>
    <a href="/docs" class="btn">📚 API Docs</a><a href="/app" class="btn">Dashboard</a>
    <div class="grid">
    <div class="card"><h3>🔐 Auth System</h3><p>JWT login, farmer profiles, crop lifecycle tracking</p></div>
    <div class="card"><h3>🤖 20 AI Agents</h3><p>Complete farm analysis from sowing to selling</p></div>
    <div class="card"><h3>🛒 E-Commerce</h3><p>80+ agri products with UPI/COD payments</p></div>
    <div class="card"><h3>📱 SMS Alerts</h3><p>Weather, pest, irrigation, harvest notifications</p></div>
    </div></body></html>
    """

# ============ HEALTH ============
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "features": [
            "farmer_auth",
            "crop_lifecycle",
            "farm_records",
            "agent_progress_stream",
            "mobile_pwa",
            "ecommerce",
            "indian_language_advice",
            "regional_crop_reference",
        ],
        "ai": ai_service.status(),
        "agents": list(AGENTS.keys()),
        "agent_count": len(AGENTS),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/agents")
async def list_agents():
    return {"agents": [{"id": k, "name": v.name, "description": v.description, "status": "active"} for k, v in AGENTS.items()]}


@app.get("/api/v1/ai/status")
async def get_ai_status(current_user: dict = Depends(get_current_user)):
    """Report configured AI provider and model without exposing API credentials."""
    return ai_service.status()


@app.get("/api/v1/locations/search")
async def search_farm_locations(
    query: str = Query(..., min_length=2, max_length=120),
    current_user: dict = Depends(get_current_user),
):
    """Search Indian districts and towns and return farm map coordinates."""
    locations = await run_in_threadpool(location_service.search, query)
    return {"locations": locations, "count": len(locations)}

# ============ AUTHENTICATION ============
class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    password: str = Field(..., min_length=6, max_length=72)
    name: str = Field(..., min_length=2)
    email: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes.")
        return password


class LoginRequest(BaseModel):
    phone: str
    password: str = Field(..., max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes.")
        return password

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    token: Optional[str] = None
    token_type: str = "bearer"
    profile_complete: Optional[bool] = None

@app.post("/api/v1/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new farmer account."""
    result = auth_service.register(request.phone, request.password, request.name, request.email)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    # Send welcome SMS
    notification_service.send_welcome_message(request.phone, request.name)

    return AuthResponse(**result)

@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login and get JWT token."""
    result = auth_service.login(request.phone, request.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error"))
    return AuthResponse(**result)

@app.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user details."""
    profile = db_service.get_profile(current_user["id"])
    return {
        "user": current_user,
        "profile": profile,
        "profile_complete": profile is not None
    }

# ============ FARMER PROFILE ============
class ProfileCreateRequest(BaseModel):
    state: str
    district: str
    village: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    farm_size_acres: float
    total_land_acres: Optional[float] = None
    owned_land_acres: Optional[float] = None
    leased_land_acres: Optional[float] = None
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    irrigation_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    farming_experience_years: Optional[int] = None
    farming_type: Optional[str] = "conventional"
    annual_income_inr: Optional[float] = None
    has_kcc: bool = False
    has_insurance: bool = False
    language_preference: FarmerLanguage = FarmerLanguage.ENGLISH
    notification_sms: bool = True
    notification_whatsapp: bool = True

@app.post("/api/v1/profile")
async def create_profile(request: ProfileCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create or update farmer profile after registration."""
    profile_data = request.model_dump()
    result = db_service.create_or_update_profile(current_user["id"], profile_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": "Profile saved successfully", "profile_id": result["profile_id"]}

@app.get("/api/v1/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get farmer profile."""
    profile = db_service.get_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete your profile.")
    return profile


class LanguagePreferenceRequest(BaseModel):
    language_preference: FarmerLanguage


@app.put("/api/v1/profile/language")
async def update_language_preference(
    request: LanguagePreferenceRequest,
    current_user: dict = Depends(get_current_user),
):
    """Persist language preference when the farmer has a profile."""
    saved = db_service.update_profile_language(
        current_user["id"],
        request.language_preference.value,
    )
    return {"success": True, "saved_to_profile": saved}

# ============ CROP SELECTION & LIFECYCLE ============
class CropSelectRequest(BaseModel):
    crop_name: str
    variety: Optional[str] = None
    season: str
    field_area_acres: float
    soil_type: Optional[str] = None
    seed_used: Optional[str] = None
    seed_quantity_kg: Optional[float] = None
    seed_cost_inr: Optional[float] = None
    sowing_date: Optional[str] = None
    expected_harvest_date: Optional[str] = None
    expected_yield_quintal: Optional[float] = None

@app.post("/api/v1/crops/select")
async def select_crop(request: CropSelectRequest, current_user: dict = Depends(get_current_user)):
    """Select a crop to start tracking its lifecycle."""
    crop_data = request.model_dump()
    result = db_service.create_crop_cycle(current_user["id"], crop_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Send confirmation
    user = db_service.get_user_by_id(current_user["id"])
    if user and user.phone:
        msg = f"🌾 Crop Tracking Started: {request.crop_name.title()} ({request.variety or 'default variety'}) on {request.field_area_acres} acres. AI Farmer will guide you through every stage!"
        notification_service._send_sms(user.phone, msg)

    return {"success": True, "message": f"Crop tracking started for {request.crop_name}", "cycle_id": result["cycle_id"]}

@app.get("/api/v1/cycles")
async def get_crop_cycles(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all crop cycles for the farmer."""
    cycles = db_service.get_crop_cycles(current_user["id"], status)
    return {"cycles": cycles, "count": len(cycles)}

@app.get("/api/v1/cycles/{cycle_id}/summary")
async def get_cycle_summary(cycle_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete lifecycle summary from start to end."""
    summary = db_service.get_crop_cycle_summary(cycle_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary

class CropUpdateRequest(BaseModel):
    status: Optional[str] = None
    progress_percent: Optional[int] = None
    germination_date: Optional[str] = None
    flowering_date: Optional[str] = None
    harvest_date: Optional[str] = None
    actual_yield_quintal: Optional[float] = None
    yield_quality: Optional[str] = None
    selling_price_per_quintal: Optional[float] = None
    total_revenue_inr: Optional[float] = None
    market_sold_to: Optional[str] = None
    notes: Optional[str] = None

@app.patch("/api/v1/cycles/{cycle_id}")
async def update_crop_cycle(cycle_id: str, request: CropUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update crop cycle status and milestones."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    result = db_service.update_crop_cycle(cycle_id, updates)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    # Send milestone alert
    if request.status == "harvesting":
        user = db_service.get_user_by_id(current_user["id"])
        cycle = db_service.get_crop_cycle_summary(cycle_id)
        if user and cycle:
            notification_service.send_harvest_reminder(
                current_user["id"], user.phone, 
                cycle["crop_name"], 
                cycle.get("expected_harvest_date", "soon")
            )

    return {"success": True, "message": "Crop cycle updated", "cycle_id": cycle_id}

@app.post("/api/v1/cycles/{cycle_id}/log")
async def log_activity(cycle_id: str, record_type: str = Form(...), details: str = Form(...), 
                       amount_inr: Optional[float] = Form(None), current_user: dict = Depends(get_current_user)):
    """Log farm activity (irrigation, fertilization, pest control, etc.)."""
    record = {
        "user_id": current_user["id"],
        "crop_cycle_id": cycle_id,
        "record_type": record_type,
        "details": details,
        "amount_inr": amount_inr,
        "metadata": {"logged_by": "api", "cycle_id": cycle_id}
    }
    record_id = db_service.add_farm_record(record)
    return {"success": True, "record_id": record_id, "message": f"{record_type} logged successfully"}

@app.get("/api/v1/cycles/{cycle_id}/timeline")
async def get_crop_timeline(cycle_id: str, current_user: dict = Depends(get_current_user)):
    """Get visual timeline of crop lifecycle."""
    summary = db_service.get_crop_cycle_summary(cycle_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    timeline = []
    stages = [
        ("Planning", summary.get("created_at"), "Crop selected and planning completed"),
        ("Sowing", summary.get("sowing_date"), f"{summary['crop_name'].title()} sown with {summary.get('seed_used', 'selected seeds')}"),
        ("Germination", summary.get("germination_date"), "Seeds germinated successfully"),
        ("Flowering", summary.get("flowering_date"), "Crop reached flowering stage"),
        ("Harvesting", summary.get("harvest_date"), f"Harvested {summary.get('actual_yield_quintal', 'expected')} quintals"),
        ("Selling", summary.get("total_revenue_inr") and summary["total_revenue_inr"] > 0, f"Sold at Rs.{summary.get('selling_price_per_quintal', 'market')}/quintal"),
    ]

    for stage_name, date_or_bool, description in stages:
        if date_or_bool:
            date_val = date_or_bool if isinstance(date_or_bool, str) else "Completed"
            timeline.append({"stage": stage_name, "date": date_val, "description": description, "completed": True})
        else:
            timeline.append({"stage": stage_name, "date": "Pending", "description": description, "completed": False})

    return {
        "crop": summary["crop_name"],
        "variety": summary.get("variety"),
        "status": summary["status"],
        "progress": summary["progress_percent"],
        "timeline": timeline,
        "financial_summary": {
            "total_expenses": summary.get("total_expenses_inr", 0),
            "total_revenue": summary.get("total_revenue_inr", 0),
            "total_profit": summary.get("total_profit_inr", 0),
            "profit_per_acre": summary.get("profit_per_acre_inr", 0)
        }
    }

# ============ CORE FARM ANALYSIS (AUTHENTICATED) ============
def _build_analysis_state(farm_input: FarmInput, current_user: dict, request_id: str) -> AI_Farmer_State:
    return {
        "request_id": request_id,
        "user_query": farm_input.query or f"Analyze farm for {farm_input.target_crop or 'optimal crops'}",
        "farm_context": {
            "farmer_id": current_user["id"],
            "state": farm_input.state,
            "district": farm_input.district,
            "language_preference": farm_input.language_preference.value,
            "latitude": farm_input.latitude,
            "longitude": farm_input.longitude,
            "soil_type": farm_input.soil_type.value if farm_input.soil_type else None,
            "farm_size_acres": farm_input.farm_size_acres,
            "season": farm_input.season.value if farm_input.season else None,
            "budget_inr": farm_input.budget_inr,
            "previous_crop": farm_input.previous_crop,
            "irrigation_type": farm_input.irrigation_type.value if farm_input.irrigation_type else None,
            "target_crop": farm_input.target_crop,
        },
        "uploaded_image_path": None,
        "agent_messages": [],
        "errors": [],
        "active_agents": [],
        "completed_agents": [],
    }


def _build_analysis_response(
    farm_input: FarmInput,
    result: Dict[str, Any],
    request_id: str,
) -> AI_FarmerResponse:
    return AI_FarmerResponse(
        request_id=request_id,
        timestamp=datetime.now(),
        farm_input=farm_input,
        crop_recommendations=result.get("crop_recommendations"),
        weather_forecast=result.get("weather_forecast", {}).get("forecast") if result.get("weather_forecast") else None,
        disease_detection=result.get("disease_detection"),
        fertilizer_plan=result.get("fertilizer_plan", {}).get("fertilizers") if result.get("fertilizer_plan") else None,
        market_prices=result.get("market_price_prediction", {}).get("prices") if result.get("market_price_prediction") else None,
        government_schemes=result.get("government_schemes"),
        risk_assessment=result.get("risk_assessment"),
        yield_prediction=result.get("yield_prediction"),
        profit_prediction=result.get("profit_prediction"),
        agronomist_advice=result.get("agronomist_advice"),
        ai_provider=result.get("ai_provider_status", ai_service.status()),
        agent_execution_log=[message["message"] for message in result.get("agent_messages", [])],
        status="success" if not result.get("errors") else "partial",
    )


def _format_sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _build_farm_suggestions(
    farm_input: FarmInput,
    current_user: Dict[str, Any],
    request_id: str,
) -> Dict[str, Any]:
    state = _build_analysis_state(farm_input, current_user, request_id)
    state["user_query"] = farm_input.query or "Give field-specific crop, input, and weather recommendations."

    ordered_agents = [
        "crop_recommendation",
        "state_crop_intelligence",
        "weather_forecast",
        "soil_health_analyzer",
    ]
    for agent_name in ordered_agents:
        state["current_agent_name"] = agent_name
        state = AGENTS[agent_name].run(state)
    state.pop("current_agent_name", None)

    if not farm_input.target_crop and state.get("crop_recommendations"):
        state["farm_context"]["target_crop"] = state["crop_recommendations"][0]["crop_name"].lower()

    if state["farm_context"].get("target_crop"):
        for agent_name in (
            "seed_recommendation",
            "fertilizer_planner",
            "irrigation_planner",
            "market_price_prediction",
            "ai_agronomist_assistant",
        ):
            state["current_agent_name"] = agent_name
            state = AGENTS[agent_name].run(state)
    state.pop("current_agent_name", None)

    return {
        "request_id": request_id,
        "location": {
            "state": farm_input.state,
            "district": farm_input.district,
            "latitude": farm_input.latitude,
            "longitude": farm_input.longitude,
        },
        "crop_recommendations": state.get("crop_recommendations", []),
        "selected_crop": state["farm_context"].get("target_crop"),
        "seed_recommendations": state.get("seed_recommendations", []),
        "fertilizer_plan": state.get("fertilizer_plan", {}).get("fertilizers", []),
        "irrigation_plan": state.get("irrigation_plan"),
        "soil_health": state.get("soil_health_report"),
        "regional_intelligence": state.get("state_crop_intelligence"),
        "weather": state.get("weather_forecast"),
        "market": state.get("market_price_prediction"),
        "yield": state.get("yield_prediction"),
        "profit": state.get("profit_prediction"),
        "ai_advice": state.get("agronomist_advice"),
        "ai_provider": state.get("ai_provider_status", ai_service.status()),
        "agent_messages": state.get("agent_messages", []),
        "errors": state.get("errors", []),
    }


@app.post("/api/v1/farm/suggestions")
async def get_farm_suggestions(
    farm_input: FarmInput,
    current_user: dict = Depends(get_current_user),
):
    """Generate farm-field recommendations using location, soil, season, and crop details."""
    request_id = generate_request_id()
    return await run_in_threadpool(
        _build_farm_suggestions,
        farm_input,
        current_user,
        request_id,
    )


@app.post("/api/v1/analyze", response_model=AI_FarmerResponse)
async def analyze_farm(farm_input: FarmInput, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Run a complete multi-agent farm analysis (requires auth)."""
    request_id = generate_request_id()
    state = _build_analysis_state(farm_input, current_user, request_id)

    try:
        config = {"configurable": {"thread_id": request_id}}
        result = ai_farmer_graph.invoke(state, config=config)
        response = _build_analysis_response(farm_input, result, request_id)

        # Send weather alert if extreme conditions
        user = db_service.get_user_by_id(current_user["id"])
        if user and user.phone and result.get("weather_forecast"):
            notification_service.send_weather_alert(current_user["id"], user.phone, result["weather_forecast"])

        background_tasks.add_task(_save_analysis, request_id, current_user["id"], result)
        return response

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze/stream")
async def stream_farm_analysis(
    farm_input: FarmInput,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Stream agent handoffs and the final farm advisory as server-sent events."""
    request_id = generate_request_id()
    state = _build_analysis_state(farm_input, current_user, request_id)
    total_agents = len(supervisor_router(state))

    def events():
        config = {"configurable": {"thread_id": request_id}}
        last_result = state
        last_reported_agent_count = 0

        for snapshot in ai_farmer_graph.stream(state, config=config, stream_mode="values"):
            last_result = snapshot
            completed = snapshot.get("completed_agents", [])
            if len(completed) > last_reported_agent_count:
                agent_name = completed[-1]
                message = next(
                    (
                        item["message"]
                        for item in reversed(snapshot.get("agent_messages", []))
                        if item["agent_name"] == agent_name
                    ),
                    f"{agent_name} completed its analysis.",
                )
                yield _format_sse("progress", {
                    "agent": agent_name,
                    "completed": len(completed),
                    "total": total_agents,
                    "message": message,
                })
                last_reported_agent_count = len(completed)

        background_tasks.add_task(_save_analysis, request_id, current_user["id"], last_result)
        response = _build_analysis_response(farm_input, last_result, request_id)
        yield _format_sse("result", response.model_dump(mode="json"))
        yield _format_sse("done", {"request_id": request_id})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

def _save_analysis(request_id: str, user_id: str, result: dict):
    try:
        db_service.add_farm_record({
            "user_id": user_id,
            "record_type": "ai_analysis",
            "details": f"Multi-agent analysis. Agents: {', '.join(result.get('completed_agents', []))}",
            "metadata": {
                "agents_run": result.get("completed_agents", []),
                "errors": result.get("errors", []),
                "top_crop": result.get("crop_recommendations", [{}])[0].get("crop_name") if result.get("crop_recommendations") else None
            }
        })
    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")

# ============ DISEASE DETECTION ============
@app.post("/api/v1/detect-disease")
async def detect_disease(crop: str = Form(...), image: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    request_id = generate_request_id()
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{request_id}_{image.filename}")

    with open(file_path, "wb") as f:
        f.write(await image.read())

    from app.agents import DiseaseDetectionAgent, AgronomistAgent
    state: AI_Farmer_State = {
        "request_id": request_id,
        "user_query": f"Disease detection for {crop}",
        "farm_context": {"farmer_id": current_user["id"], "target_crop": crop},
        "uploaded_image_path": file_path,
        "agent_messages": [], "errors": [], "active_agents": [], "completed_agents": []
    }

    state = DiseaseDetectionAgent().run(state)
    state = AgronomistAgent().run(state)

    return {
        "request_id": request_id,
        "disease_detection": state.get("disease_detection"),
        "medicine_recommendations": state.get("medicine_recommendations"),
        "agronomist_advice": state.get("agronomist_advice")
    }

# ============ NOTIFICATIONS ============
@app.get("/api/v1/notifications")
async def get_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user)):
    """Get user notifications."""
    notifs = notification_service.get_user_notifications(current_user["id"], unread_only)
    return {"notifications": notifs, "count": len(notifs)}

# ============ E-COMMERCE (AUTHENTICATED) ============
class ProductSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    crop: Optional[str] = None
    organic_only: bool = False
    min_price: float = 0
    max_price: float = 999999

@app.post("/api/v1/shop/search")
async def search_products(search: ProductSearch):
    results = ec_service_instance.search_products(
        query=search.query, category=search.category, crop=search.crop,
        organic_only=search.organic_only, min_price=search.min_price, max_price=search.max_price
    )
    return {"total": len(results), "products": results}

@app.get("/api/v1/shop/product/{product_id}")
async def get_product(product_id: str):
    product = ec_service_instance.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/api/v1/shop/categories")
async def get_categories():
    return {"categories": [
        {"id": "seed", "name": "Seeds", "icon": "🌱", "count": 20},
        {"id": "fertilizer", "name": "Fertilizers", "icon": "🧪", "count": 16},
        {"id": "pesticide", "name": "Crop Protection", "icon": "🛡️", "count": 18},
        {"id": "equipment", "name": "Equipment & Tools", "icon": "🔧", "count": 14},
    ]}

@app.get("/api/v1/shop/recommendations")
async def get_recommendations(crop: str = Query(..., description="Crop name for input recommendations")):
    recommendations = ec_service_instance.get_recommendations_for_crop(crop)
    return {"crop": crop, "recommended_inputs": recommendations}

@app.post("/api/v1/shop/cart/add")
async def add_to_cart(farmer_id: str = Form(...), product_id: str = Form(...), quantity: float = Form(...)):
    result = ec_service_instance.add_to_cart(farmer_id, product_id, quantity)
    return result

@app.get("/api/v1/shop/cart/{farmer_id}")
async def get_cart(farmer_id: str):
    return ec_service_instance.get_cart(farmer_id)

class OrderRequest(BaseModel):
    farmer_id: str
    shipping_address: dict
    payment_method: str = "COD"

@app.post("/api/v1/shop/order")
async def place_order(order: OrderRequest):
    result = ec_service_instance.place_order(order.farmer_id, order.shipping_address, order.payment_method)
    return result

# ============ FARM RECORDS ============
@app.post("/api/v1/records")
async def add_record(record: dict, current_user: dict = Depends(get_current_user)):
    record["user_id"] = current_user["id"]
    record_id = db_service.add_farm_record(record)
    return {"record_id": record_id, "status": "saved"}

@app.get("/api/v1/records")
async def get_records(record_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    records = db_service.get_farm_records(current_user["id"], record_type)
    return {"records": records, "count": len(records)}

# ============ DASHBOARD ============
@app.get("/app", response_class=HTMLResponse)
async def dashboard():
    return await root()

@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    """Get farmer dashboard summary."""
    profile = db_service.get_profile(current_user["id"])
    cycles = db_service.get_crop_cycles(current_user["id"])
    records = db_service.get_farm_records(current_user["id"])
    notifications = db_service.get_notifications(current_user["id"], unread_only=True)

    # Calculate stats
    total_expenses = sum(r.get("amount_inr", 0) for r in records if r.get("record_type") == "expense" and r.get("amount_inr"))
    total_income = sum(r.get("amount_inr", 0) for r in records if r.get("record_type") == "income" and r.get("amount_inr"))

    active_crops = [c for c in cycles if c["status"] not in ["completed", "sold"]]
    completed_crops = [c for c in cycles if c["status"] in ["completed", "sold"]]

    return {
        "farmer_name": current_user.get("name"),
        "profile_complete": profile is not None,
        "farm_location": f"{profile.get('district', '')}, {profile.get('state', '')}" if profile else None,
        "farm_size_acres": profile.get("farm_size_acres") if profile else None,
        "language_preference": profile.get("language_preference") if profile else None,
        "stats": {
            "total_crop_cycles": len(cycles),
            "active_crops": len(active_crops),
            "completed_crops": len(completed_crops),
            "total_expenses_inr": total_expenses,
            "total_income_inr": total_income,
            "net_profit_inr": total_income - total_expenses,
            "total_records": len(records),
            "unread_notifications": len(notifications)
        },
        "active_crops": active_crops[:3],
        "recent_notifications": notifications[:5],
        "quick_actions": [
            {"label": "Start New Crop", "action": "/api/v1/crops/select", "icon": "🌱"},
            {"label": "Analyze Farm", "action": "/api/v1/analyze", "icon": "🤖"},
            {"label": "Check Weather", "action": "/api/v1/weather", "icon": "🌤️"},
            {"label": "Shop Inputs", "action": "/api/v1/shop/search", "icon": "🛒"},
            {"label": "View Schemes", "action": "/api/v1/schemes", "icon": "🏛️"},
        ]
    }
