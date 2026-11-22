"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class Season(str, Enum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"
    YEAR_ROUND = "year_round"


class IrrigationType(str, Enum):
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    FLOOD = "flood"
    RAINFED = "rainfed"
    SUBSURFACE = "subsurface"


class SoilType(str, Enum):
    ALLUVIAL = "alluvial"
    BLACK = "black"
    RED = "red"
    LATERITE = "laterite"
    DESERT = "desert"
    MOUNTAIN = "mountain"
    SALINE = "saline"
    PEATY = "peaty"
    LOAMY = "loamy"
    SANDY = "sandy"
    CLAYEY = "clayey"


class FarmerLanguage(str, Enum):
    ENGLISH = "en"
    ASSAMESE = "as"
    BENGALI = "bn"
    BODO = "brx"
    DOGRI = "doi"
    GUJARATI = "gu"
    HINDI = "hi"
    KANNADA = "kn"
    KASHMIRI = "ks"
    KONKANI = "kok"
    MAITHILI = "mai"
    MALAYALAM = "ml"
    MANIPURI = "mni"
    MARATHI = "mr"
    NEPALI = "ne"
    ODIA = "or"
    PUNJABI = "pa"
    SANSKRIT = "sa"
    SANTALI = "sat"
    SINDHI = "sd"
    TAMIL = "ta"
    TELUGU = "te"
    URDU = "ur"


class FarmInput(BaseModel):
    """Base input for farm analysis."""
    farmer_id: Optional[str] = Field(None, description="Optional farmer identifier; authenticated user identity is used by the API")
    state: str = Field(..., description="Indian state")
    district: str = Field(..., description="District name")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    farm_size_acres: Optional[float] = Field(None, gt=0)
    soil_type: Optional[SoilType] = None
    season: Optional[Season] = None
    budget_inr: Optional[float] = Field(None, ge=0)
    previous_crop: Optional[str] = None
    irrigation_type: Optional[IrrigationType] = None
    target_crop: Optional[str] = None
    query: Optional[str] = Field(None, description="Natural language query from farmer")
    language_preference: FarmerLanguage = FarmerLanguage.ENGLISH


class CropRecommendation(BaseModel):
    crop_name: str
    confidence_score: float = Field(..., ge=0, le=1)
    expected_yield_quintal_per_acre: float
    market_demand: str  # high, medium, low
    water_requirement: str  # high, medium, low
    suitable_soil: List[str]
    season: str
    estimated_cost_per_acre: float
    estimated_revenue_per_acre: float
    reasoning: str


class WeatherForecast(BaseModel):
    date: str
    temp_max_c: float
    temp_min_c: float
    humidity_percent: Optional[float] = None
    rainfall_probability_percent: Optional[float] = None
    rainfall_mm: float
    wind_speed_kmh: float
    condition: str
    advisory: str


class DiseaseDetectionResult(BaseModel):
    disease_name: str
    confidence: float = Field(..., ge=0, le=1)
    severity: str  # low, medium, high
    symptoms: List[str]
    causes: List[str]
    organic_treatment: List[str]
    chemical_treatment: List[str]
    preventive_measures: List[str]
    image_annotated_path: Optional[str] = None


class FertilizerPlan(BaseModel):
    fertilizer_name: str
    quantity_kg_per_acre: float
    application_timing: str
    application_method: str
    estimated_cost_inr: float
    organic_alternative: Optional[str] = None


class MarketPrice(BaseModel):
    commodity: str
    market: str
    min_price_inr_per_quintal: float
    max_price_inr_per_quintal: float
    modal_price_inr_per_quintal: float
    price_trend: str  # rising, falling, stable
    forecast_next_30_days: str
    date: str


class GovernmentScheme(BaseModel):
    scheme_name: str
    ministry: str
    description: str
    eligibility: List[str]
    benefits: List[str]
    application_process: str
    deadline: Optional[str] = None
    official_link: Optional[str] = None


class RiskAssessment(BaseModel):
    risk_category: str  # weather, market, pest, financial, operational
    risk_level: str  # low, medium, high, critical
    probability: float = Field(..., ge=0, le=1)
    impact: str
    mitigation_strategies: List[str]
    insurance_recommended: bool


class AI_FarmerResponse(BaseModel):
    """Unified response from the AI Farmer platform."""
    request_id: str
    timestamp: datetime
    farm_input: FarmInput
    crop_recommendations: Optional[List[CropRecommendation]] = None
    weather_forecast: Optional[List[WeatherForecast]] = None
    disease_detection: Optional[DiseaseDetectionResult] = None
    fertilizer_plan: Optional[List[FertilizerPlan]] = None
    market_prices: Optional[List[MarketPrice]] = None
    government_schemes: Optional[List[GovernmentScheme]] = None
    risk_assessment: Optional[List[RiskAssessment]] = None
    yield_prediction: Optional[Dict[str, Any]] = None
    profit_prediction: Optional[Dict[str, Any]] = None
    agronomist_advice: Optional[str] = None
    ai_provider: Optional[Dict[str, Any]] = None
    agent_execution_log: List[str]
    status: str  # success, partial, error
