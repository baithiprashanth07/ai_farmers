# AI Farmer - System Architecture Documentation

## Document Information
- **Version**: 2.0.0
- **Date**: July 2026
- **Status**: Working prototype; production readiness requires deployment and provider validation
- **Classification**: Technical Architecture

---

## 1. Executive Summary

AI Farmer is a FastAPI and LangGraph farming application with 19 registered agent workflows, farmer authentication, crop-cycle tracking, and farm records. Selected workflows run sequentially and share their findings through graph state; the API can stream agent progress to the mobile-ready web interface. External data sources and production deployment controls require separate configuration and validation.

The farm-planning interface can request AI agronomist advice in English or any of India's 22 scheduled languages. The selected language is carried in shared farm context for both streamed analysis and automatic field suggestions. State and union-territory crop data is served from `data/india_state_crops.json` and informs regional crop ranking and specialty-crop candidates. This catalogue is indicative only; it is not an authoritative agronomic recommendation source and must be checked against district-level conditions and local agricultural guidance.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Responsive   │  │  Mobile Web  │  │  External    │  │  External    │      │
│  │ PWA         │  │  Browser     │  │  Messaging   │  │  Voice       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │   API GATEWAY     │
                          │   (Nginx + SSL)   │
                          └─────────┬─────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                              APPLICATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FASTAPI APPLICATION SERVER                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │   │
│  │  │  Analysis  │  │  Disease   │  │  E-Commerce│  │  Records   │ │   │
│  │  │  Router    │  │  Router    │  │  Router    │  │  Router    │ │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘ │   │
│  └────────┼───────────────┼───────────────┼───────────────┼────────┘   │
└───────────┼───────────────┼───────────────┼───────────────┼────────────┘
            │               │               │               │
┌───────────▼───────────────▼───────────────▼───────────────▼────────────┐
│                         SERVICE LAYER                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Weather   │  │  Market    │  │  Soil      │  │  Disease   │       │
│  │  Service   │  │  Service   │  │  Service   │  │  Service   │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  GovScheme │  │  E-Commerce│  │  Database  │  │  RAG/KB    │       │
│  │  Service   │  │  Service   │  │  Service   │  │  Service   │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           AGENT LAYER (LangGraph)                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    SUPERVISOR AGENT                                  │  │
│  │  (Conditional routing, state management, error handling)          │  │
│  └──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬───┘  │
│         │      │      │      │      │      │      │      │      │      │
│  ┌──────▼──┐ ┌▼─────┐ ┌▼────┐ ┌▼────┐ ┌▼────┐ ┌▼────┐ ┌▼────┐ ┌▼────┐ │
│  │ CropRec │ │State │ │Seed │ │Sow  │ │Weath│ │Irrig│ │Soil │ │Fert │ │
│  │  Agent  │ │Crop  │ │Rec  │ │Plan │ │er   │ │ation│ │Health│ │ilizer│ │
│  └─────────┘ └──────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ Disease │ │  Pest   │ │ Market  │ │  Risk   │ │  Gov    │         │
│  │ Detect  │ │ Detect  │ │ Price   │ │ Predict │ │ Scheme  │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              AI AGRONOMIST (LLM Synthesis Layer)                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                         DATA LAYER                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  SQLite/   │  │  Redis     │  │  Vector    │  │  Object    │       │
│  │  PostgreSQL│  │  Cache     │  │  DB (RAG)  │  │  Storage   │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                      EXTERNAL SERVICES LAYER                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │OpenWeather │  │  Agmarknet │  │  PM-KISAN  │  │   IMD      │     │
│  │    Map     │  │    API     │  │    API     │  │   API      │     │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │  OpenAI    │  │  Soil Test │  │  Payment   │                     │
│  │  GPT-4o    │  │    API     │  │  Gateway   │                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Communication Pattern

All agents communicate through a **shared state object** (`AI_Farmer_State`) that follows the TypedDict pattern:

```python
class AI_Farmer_State(TypedDict, total=False):
    user_query: str
    farm_context: FarmContext
    # Agent outputs
    crop_recommendations: List[Dict]
    weather_forecast: Dict
    soil_health_report: Dict
    disease_detection: Dict
    # ... (20 fields for 20 agents)
    # Workflow tracking
    active_agents: List[str]
    completed_agents: List[str]
    agent_messages: List[AgentMessage]
    errors: List[str]
    # Final output
    final_report: Dict
    response_to_user: str
```

### 2.3 Conditional Routing Logic

The Supervisor Agent uses intent-based routing:

```
IF user_query contains "disease" OR uploaded_image exists:
    → Activate DiseaseDetectionAgent

IF target_crop is specified:
    → Activate CropSpecificAgents (Seed, Sowing, Fertilizer, Irrigation)

IF user_query contains "scheme" OR "subsidy":
    → Activate GovSchemeAgent

IF user_query contains "risk" OR "insurance":
    → Activate RiskPredictorAgent

ALWAYS:
    → Activate CoreAgents (CropRec, Weather, Soil)
    → End with AgronomistAgent (synthesis)
```

---

## 3. Component Design

### 3.1 BaseAgent Class

All agents inherit from `BaseAgent` which provides:
- **Execution Wrapper**: Logging, error handling, timing
- **State Management**: Read/write to shared state
- **Database Logging**: Automatic execution tracking
- **Message Passing**: Inter-agent communication

```python
class BaseAgent(ABC):
    def run(self, state: AI_Farmer_State) -> AI_Farmer_State:
        # 1. Log start
        # 2. Execute _execute()
        # 3. Handle errors gracefully
        # 4. Log to database
        # 5. Return updated state
```

### 3.2 LangGraph Integration

```python
workflow = StateGraph(AI_Farmer_State)

# Add nodes
for agent_name, agent in AGENTS.items():
    workflow.add_node(agent_name, agent.run)

# Define edges
workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "crop_recommendation")
workflow.add_edge("crop_recommendation", "weather_forecast")
# ... (conditional edges)
workflow.add_edge("agronomist", END)

# Compile with memory
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### 3.3 Service Layer

| Service | Responsibility | External Dependencies |
|---------|---------------|---------------------|
| WeatherService | Forecast + agricultural advisories | OpenWeatherMap API |
| MarketService | Mandi prices + profit prediction | Agmarknet API (mock) |
| SoilService | Soil analysis + deficiency detection | Internal database |
| DiseaseService | CV-based disease detection | YOLOv11 model (optional) |
| GovSchemeService | Scheme eligibility + details | Internal database |
| ECommerceService | Product catalog + orders | Internal database |
| DatabaseService | Persistence + audit logging | SQLite/PostgreSQL |

---

## 4. Data Flow

### 4.1 Complete Analysis Flow

```
1. Farmer submits farm details via API
   ↓
2. Supervisor analyzes intent and routes to agents
   ↓
3. Parallel execution of independent agents:
   - CropRecommendationAgent → crop_recommendations
   - WeatherAgent → weather_forecast
   - SoilHealthAgent → soil_health_report
   - StateCropIntelligenceAgent → state_crop_intelligence
   ↓
4. Sequential execution of dependent agents:
   - SeedRecommendationAgent (needs crop) → seed_recommendations
   - SowingPlannerAgent (needs crop + weather) → sowing_plan
   - FertilizerPlannerAgent (needs soil + crop) → fertilizer_plan
   - IrrigationPlannerAgent (needs crop + weather) → irrigation_plan
   - MarketPriceAgent (needs crop) → market_price_prediction
   - RiskPredictorAgent (needs all above) → risk_assessment
   ↓
5. AgronomistAgent synthesizes all outputs → agronomist_advice
   ↓
6. Response returned to farmer with all recommendations
```

### 4.2 Disease Detection Flow

```
1. Farmer uploads crop image
   ↓
2. Image saved to storage
   ↓
3. DiseaseDetectionAgent processes image:
   a. Try YOLOv11 model (if available)
   b. Fallback to knowledge-based detection
   ↓
4. MedicineRecommendationAgent provides treatments
   ↓
5. AgronomistAgent provides comprehensive advice
```

---

## 5. Database Design

### 5.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ farmer_profiles │       │  farm_records   │       │ agent_execution │
│     (1)         │◄──────│     (N)         │       │     logs        │
└─────────────────┘       └─────────────────┘       └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────┐
│     orders      │       │  order_items    │
│     (1)         │◄──────│     (N)         │
└─────────────────┘       └─────────────────┘
```

### 5.2 Schema Details

**farmer_profiles**
```sql
CREATE TABLE farmer_profiles (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    state VARCHAR(50),
    district VARCHAR(50),
    village VARCHAR(100),
    farm_size_acres FLOAT,
    soil_type VARCHAR(30),
    irrigation_type VARCHAR(30),
    crops_history TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**farm_records**
```sql
CREATE TABLE farm_records (
    id VARCHAR PRIMARY KEY,
    farmer_id VARCHAR REFERENCES farmer_profiles(id),
    record_type VARCHAR(30),  -- sowing, irrigation, fertilization, pest_control, harvest, expense, income, ai_analysis
    crop_name VARCHAR(50),
    date TIMESTAMP,
    details TEXT,
    metadata_json TEXT,  -- Flexible JSON data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**agent_execution_logs**
```sql
CREATE TABLE agent_execution_logs (
    id VARCHAR PRIMARY KEY,
    request_id VARCHAR INDEX,
    agent_name VARCHAR(50),
    input_data TEXT,
    output_data TEXT,
    execution_time_ms INTEGER,
    status VARCHAR(20),  -- success, error, partial
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Security Considerations

### 6.1 Authentication & Authorization
- JWT-based authentication for farmers
- Role-based access control (Farmer, Admin, Agent)
- API key validation for external service calls

### 6.2 Data Protection
- PII encryption at rest (farmer phone, location)
- HTTPS/TLS for all communications
- Input sanitization and validation
- SQL injection prevention via SQLAlchemy ORM

### 6.3 API Security
- Rate limiting (100 requests/minute per farmer)
- CORS configuration for approved domains
- Request size limits (10MB for images)
- Timeout handling for external APIs

---

## 7. Scalability Plan

### 7.1 Horizontal Scaling

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────►│  FastAPI    │────►│  PostgreSQL │
│  (Load      │     │  Instance 1 │     │  (Primary)  │
│  Balancer)  │────►│  FastAPI    │────►│             │
│             │     │  Instance 2 │     │  Redis      │
│             │────►│  FastAPI    │     │  (Cache)    │
└─────────────┘     │  Instance N │     └─────────────┘
                    └─────────────┘
```

### 7.2 Caching Strategy
- Redis for weather forecasts (TTL: 1 hour)
- Redis for market prices (TTL: 30 minutes)
- Redis for product catalog (TTL: 24 hours)
- Application-level caching for soil analysis

### 7.3 Background Processing
- Celery for async tasks (image processing, report generation)
- Redis as message broker
- Separate worker processes for ML inference

---

## 8. Monitoring & Observability

### 8.1 Metrics
- Agent execution time (p50, p95, p99)
- API response time
- External API latency
- Error rates per agent
- Active farmer count
- Order conversion rate

### 8.2 Logging
- Structured JSON logging via Loguru
- Log rotation (10MB files, 30-day retention)
- Correlation IDs for request tracing
- Agent execution audit trail

### 8.3 Alerting
- PagerDuty integration for critical errors
- Slack notifications for agent failures
- Email alerts for order issues

---

## 9. Disaster Recovery

### 9.1 Backup Strategy
- Database: Daily automated backups to S3
- Images: S3 with versioning
- Configuration: Git-based version control

### 9.2 Recovery Objectives
- RPO (Recovery Point Objective): 1 hour
- RTO (Recovery Time Objective): 30 minutes

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **LangGraph** | Framework for building stateful, multi-agent applications |
| **RAG** | Retrieval-Augmented Generation - combines LLMs with document retrieval |
| **IPM** | Integrated Pest Management |
| **KVK** | Krishi Vigyan Kendra (Farm Science Center) |
| **FPO** | Farmer Producer Organization |
| **MSP** | Minimum Support Price |
| **PMFBY** | Pradhan Mantri Fasal Bima Yojana (Crop Insurance) |
| **DAS** | Days After Sowing |
| **PHI** | Pre-Harvest Interval |
| **ETL** | Economic Threshold Level |

---

*Document Version: 2.0.0 | Last Updated: July 2026*
