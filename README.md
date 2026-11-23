# 🌾 AI Farmer — Mobile-Ready Farm Planning and Crop Tracking

> **Your farm, a clear plan. Smart steps for steady growth.**
>
> 🔐 Farmer Accounts | 🌱 Crop Tracking | 🤖 Shared-State Agent Workflow | 📱 Installable Web App | 💰 Farm Diary

---

## 📋 Table of Contents

- [Overview](#overview)
- [What's New in v3.0](#whats-new-in-v30)
- [Architecture](#architecture)
- [Farming Agent Workflow](#farming-agent-workflow)
- [Features](#features)
- [Authentication & Profiles](#authentication--profiles)
- [Crop Lifecycle Tracking](#crop-lifecycle-tracking)
- [E-Commerce](#e-commerce)
- [SMS Alerts](#sms-alerts)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [License](#license)

---

## 🎯 Overview

AI Farmer is a farmer-focused web application backed by FastAPI and LangGraph. Farmers can create an account, request crop and farm advice, track crop cycles, and keep field and financial records from a phone or desktop browser.

### Key Capabilities
- **Live farm analysis**: See specialist-agent progress and the final farm advisory as it is produced.
- **Sequential agent handoffs**: Each selected workflow receives the shared farm context, earlier findings, and agent messages.
- **Automatic field recommendations**: Choose a state, enter a district and village/town, and use contextual geocoder suggestions for a location; receive regional crop choices and location-specific weather plus crop, seed, fertilizer, irrigation, soil, and market estimates.
- **Multiple model providers**: Configure OpenAI, Groq, Gemini, Anthropic Claude, OpenRouter, Ollama, or another OpenAI-compatible endpoint.
- **Indian-language AI advice**: Select English or any of India's 22 scheduled languages for generated agronomist advice; Indian language options are shown in English and their native scripts. The rest of the dashboard interface remains in English.
- **Regional crop planning**: State/UT selection loads major and specialty crop reference candidates for all 28 states and 8 union territories, with regional crop candidates used to inform rankings.
- **Crop tracking and farm diary**: Start crop cycles and record irrigation, inputs, expenses, income, and field notes.
- **Daily crop lifecycle guide**: Select a crop and sowing date to view a day-by-day monitoring schedule through the expected harvest; download it or add a selected check to the crop-linked diary.
- **Crop seasons and classifications**: Browse indicative Kharif, Rabi, and Zaid windows and expanded crop-use categories.
- **Livestock records**: Log dairy, poultry, feed, animal health, and optional income or expenses.
- **Farm calculators**: Scale a soil-test or extension-approved input rate to field area and estimate crop revenue, costs, and net returns from farmer-entered figures.
- **Government schemes and daily brief**: Review national scheme references, find state-specific programs through myScheme, and get a rotating field checklist with official weather and market links.
- **Farmer services hub**: Find the named government apps and private agriculture services in one searchable directory with publisher links.
- **Marketplace and crop health**: Browse the bundled sample farm-input catalogue; compare reported crop symptoms without a model, or use photo detection when trained weights are installed.
- **Mobile-ready PWA**: Responsive screens, installable app shell, and offline access to the shell (API data still requires a connection).
- **Farmer accounts**: Phone-number sign-in with bearer-token authentication.

> **Readiness note:** This is a working application prototype, not a production-certified agricultural or financial service. External weather, market, SMS, and LLM integrations depend on provider configuration and should be validated before field use.

Farm profile details and specialist findings are sent to the configured AI provider when generating AI advice. Do not enter personal identifiers in farming questions. For local-only model inference, run Ollama and configure `AI_PROVIDER=ollama`; weather and geocoding still use the Open-Meteo service.

The state/UT crop catalogue is an **indicative planning reference**, not a verified government dataset or a guarantee of local suitability. Verify crop choices, varieties, inputs, and timing against current district conditions, soil tests, water availability, and local agricultural extension advice. AI-generated advice is available only after configuring a provider; the language selection affects AI advice, not the pre-written interface labels. Language preferences are saved in the browser and synced to an existing farmer profile.

Public reference endpoints: `GET /api/v1/languages` lists English and the 22 scheduled languages; `GET /api/v1/regions` returns all 36 states/UTs with indicative major and specialty crops and the catalogue caveat. Authenticated `PUT /api/v1/profile/language` syncs a preference to an existing profile.

---

## ✨ Farmer Workflows

### 🔐 Authentication & User Management
- JWT-based login/registration with bcrypt password hashing
- Farmer profile creation with complete farm details
- Secure token-based API access
- Phone number-based authentication (India format)

### 🌱 Crop Lifecycle Tracking
- Select crop and track from planning to selling
- Visual timeline of all farming stages
- Log every activity: irrigation, fertilization, pest control, labor
- Automatic expense and income tracking
- Profit per acre calculation
- Harvest readiness alerts

### 📱 Optional Notifications
- Notification endpoints are available; delivery requires a configured SMS or messaging provider.

### 🛒 Enhanced E-Commerce
- 80+ products across seeds, fertilizers, pesticides, equipment
- Crop-specific input recommendations
- Shopping cart and order management
- Payment methods: COD, UPI, Card, Net Banking
- Order tracking and delivery estimates

### 📊 Farmer Dashboard
- Farm overview with active crop and diary totals
- Live progress messages from the farm analysis agents
- Crop recommendation, weather outlook, and agronomist advisory
- Crop cycle creation and recent activity records
- Installable mobile web app with a cached application shell
- Automatic field-driven crop, seed, fertilizer, weather, and market suggestions
- Town/district search with farm coordinates for localized weather forecasts

### 🧠 Language Model Providers
Copy `.env.example` to `.env` and configure one provider before starting the server:

| Provider | Configuration |
|----------|---------------|
| OpenAI | `AI_PROVIDER=openai` and `OPENAI_API_KEY` |
| Groq | `AI_PROVIDER=groq` and `GROQ_API_KEY` |
| Gemini | `AI_PROVIDER=gemini` and `GEMINI_API_KEY` |
| Anthropic Claude | `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` |
| OpenRouter | `AI_PROVIDER=openrouter` and `OPENROUTER_API_KEY` |
| Ollama | `AI_PROVIDER=ollama`, optional `AI_MODEL`, and a reachable local Ollama server |
| vLLM, LocalAI, or another compatible endpoint | `AI_PROVIDER=custom`, `AI_BASE_URL`, `AI_MODEL`, and optional `AI_API_KEY` |

`AI_PROVIDER=auto` detects the first configured hosted provider (OpenAI, Groq, Gemini, Anthropic, then OpenRouter). `GET /api/v1/ai/status` reports the selected provider and model, never its secret. The AI integration is optional; deterministic farm recommendations remain available without model credentials.

## ☁️ Deploy on Streamlit Community Cloud

The project includes a Streamlit dashboard entry point at `streamlit_app.py`. Push the project to a GitHub repository you control, then create a Streamlit Community Cloud app using that repository, the deployment branch, and `streamlit_app.py` as the main file. Streamlit installs the dependencies from the root `requirements.txt`.

Add secrets in the Streamlit app's **Settings → Secrets**. Use the root-level uppercase setting names shown in `.streamlit/secrets.toml.example`. For persistent farmer accounts, profiles, crop cycles, and diary records, configure a managed PostgreSQL `DATABASE_URL`; Streamlit Community Cloud's local filesystem is not a durable database. Keep `SECRET_KEY` unique and private. An AI provider key is optional; without one, deterministic farm recommendations still work. Do not commit `secrets.toml` or live credentials.

The existing FastAPI web app remains available separately with `python main.py`; Streamlit Community Cloud runs `streamlit_app.py` and does not run the FastAPI server as a second service. The Streamlit dashboard provides sign-in/registration, farm profiles, field recommendations, crop tracking, farm diary, livestock records, calculators, scheme references, a daily farm checklist, a searchable directory of the named farmer services, and sample input browsing. Directory links open external publishers and are not live integrations or endorsements. Marketplace catalogue entries are demo data and do not process orders. Photo disease detection requires a trained model at `data/models/disease_detection.pt`; without one, the app offers only a clearly labeled rule-based symptom reference and will not guess from a photo. Scheme eligibility and application windows change, so confirm them with official portals and state departments. Verify the Cloud deployment, database connection, and provider credentials after publishing; these changes prepare the app but do not publish it to an account.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Responsive   │  │ Mobile Web  │  │  External    │  │  External    │      │
│  │ PWA         │  │ Browser     │  │  Messaging   │  │  Voice       │      │
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
│                           FASTAPI APPLICATION v3.0                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   Auth   │ │  Profile │ │   Crop   │ │  Analyze │ │   Shop   │         │
│  │  Router  │ │  Router  │ │ Lifecycle│ │  Router  │ │  Router  │         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │
│       │            │            │            │            │                │
│  ┌────▼────────────▼────────────▼────────────▼────────────▼────────────┐  │
│  │                         SERVICE LAYER                                 │  │
│  │  AuthService | ProfileService | CropCycleService | NotificationService│  │
│  │  WeatherService | MarketService | SoilService | DiseaseService        │  │
│  │  ECommerceService | DatabaseService | RAGService                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────────────────────────────▼────────────────────────────────────┐  │
│  │                      LANGGRAPH MULTI-AGENT SYSTEM                     │  │
│  │  Supervisor → 20 Specialized Agents → AI Agronomist (LLM Synthesis)  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────────────────────────────▼────────────────────────────────────┐  │
│  │                         DATA LAYER                                    │  │
│  │  PostgreSQL/SQLite | Redis Cache | ChromaDB (RAG) | S3 Storage      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Farming Agent Workflow

The API currently registers 19 agent workflows. Workflows are routed according to the farm input and query; selected agents run sequentially, share findings through the LangGraph state, and publish a message for downstream agents. Some workflow names intentionally reuse the same underlying specialist implementation.

| # | Workflow | Description |
|---|----------|-------------|
| 1 | **Crop Recommendation** | Recommends crops based on soil, climate, and season |
| 2 | **State-wise Crop Intelligence** | Regional crop patterns, MSP, and best practices |
| 3 | **Seed Recommendation** | Certified seeds and variety information |
| 4 | **Sowing Planner** | Sowing windows, seed treatment, and spacing |
| 5 | **Weather Forecast** | Forecast with agricultural advisories |
| 6 | **Irrigation Planner** | Water-use planning |
| 7 | **Fertilizer Planner** | Nutrient plans and organic alternatives |
| 8 | **Soil Health Analyzer** | Soil condition and nutrient analysis |
| 9 | **Nutrient Deficiency Detector** | Symptom-based deficiency guidance |
| 10 | **Disease Detection** | Crop disease assessment |
| 11 | **Pest Detection** | Pest identification and IPM guidance |
| 12 | **Medicine Recommendation** | Treatment options |
| 13 | **Yield Prediction** | Crop yield estimation |
| 14 | **Market Price Prediction** | Market price and trend estimates |
| 15 | **Profit Prediction** | Cost and revenue estimates |
| 16 | **Government Scheme Advisor** | Government scheme information |
| 17 | **Farm Risk Predictor** | Weather, market, pest, and financial risk |
| 18 | **Farm Record Manager** | Farm diary and records |
| 19 | **AI Agronomist Assistant** | Consolidated farming advisory |

---

## 🔐 Authentication & Profiles

### Registration Flow
```
1. POST /api/v1/auth/register
   → Phone, Password, Name
   ← JWT Token + Welcome SMS

2. POST /api/v1/profile
   → State, District, Farm Size, Soil Type, etc.
   ← Profile saved

3. POST /api/v1/crops/select
   → Crop Name, Variety, Season, Area
   ← Crop cycle created + Tracking started
```

### Profile Fields
- **Location**: State, District, Village, Pincode, GPS coordinates
- **Farm Details**: Size (owned/leased), Soil type, pH, Irrigation type/source
- **Farming Profile**: Experience, Type (organic/conventional), Equipment
- **Financial**: Annual income, KCC status, Insurance status
- **Preferences**: Language, Notification channels

---

## 🌱 Crop Lifecycle Tracking

### Complete Farming Journey

```
📋 PLANNING
   ↓ Select crop, variety, expected yield
   ↓ AI analysis: soil, weather, market
   ↓ Input planning: seeds, fertilizer, pesticide

🌱 SOWING
   ↓ Log sowing date, seed variety, quantity
   ↓ Basal fertilizer application
   ↓ First irrigation

💧 GROWTH PHASE
   ↓ Irrigation logging (date, method, hours)
   ↓ Fertilizer top-dressing logs
   ↓ Pest/disease monitoring
   ↓ Weather alerts

🌾 HARVEST
   ↓ Harvest date logging
   ↓ Actual yield recording
   ↓ Quality assessment

💰 SELLING
   ↓ Market selection (mandi/FPO/direct)
   ↓ Price per quintal
   ↓ Revenue calculation
   ↓ Profit per acre
```

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crops/select` | Start tracking a new crop |
| GET | `/api/v1/cycles` | List all crop cycles |
| GET | `/api/v1/cycles/{id}/summary` | Complete lifecycle summary |
| GET | `/api/v1/cycles/{id}/timeline` | Visual timeline |
| PATCH | `/api/v1/cycles/{id}` | Update status/milestones |
| POST | `/api/v1/cycles/{id}/log` | Log activity (irrigation, etc.) |

---

## 📱 SMS Alert System

### Alert Types
- **Weather**: Rain, heat wave, cold wave, frost warnings
- **Irrigation**: Reminders based on soil moisture and weather
- **Pest**: Early warnings based on weather conditions and crop stage
- **Harvest**: Readiness alerts with market price context
- **Market**: Price movement alerts for tracked commodities
- **Schemes**: Application deadline reminders for government schemes

### Configuration
Farmers can enable/disable alerts per category:
```json
{
  "notification_sms": true,
  "notification_whatsapp": true,
  "notification_push": true
}
```

---

## 🛒 E-Commerce Marketplace

### Product Categories (80+ Products)

**Seeds (20+)**
- Rice: Pusa Basmati 1121/1509, IR 64, MTU 1010
- Wheat: HD 2967, DBW 187, PBW 343
- Cotton: RCH 2 BG-II, Ankur 651
- Vegetables: Pusa Ruby Tomato, Arka Vikas, Kufri Jyoti
- Fruits: Grand Naine Banana, Dashehari Mango, Alphonso Mango

**Fertilizers (16+)**
- Chemical: Urea, DAP, MOP, NPK complexes
- Micronutrients: Zinc, Boron, Iron, Magnesium
- Organic: Vermicompost, Neem Cake, FYM
- Bio: Rhizobium, Azotobacter, PSB

**Crop Protection (18+)**
- Bio: Neem Oil, Bt, Trichoderma, Pseudomonas
- Insecticides: Spinosad, Emamectin, Chlorantraniliprole
- Fungicides: Mancozeb, Carbendazim, Tricyclazole
- Herbicides: Glyphosate, Pendimethalin

**Equipment (14+)**
- Sprayers, Drip kits, Sprinklers, Power weeders
- Soil testing kits, Moisture meters, Pruning shears
- Pheromone traps, Mulch films, Shade nets

### Payment Methods
- 💵 Cash on Delivery (COD)
- 📱 UPI / Google Pay / PhonePe
- 💳 Credit/Debit Card
- 🏦 Net Banking

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Auth** | JWT, bcrypt, python-jose |
| **AI Framework** | LangChain, LangGraph, OpenAI GPT-4o |
| **ML/CV** | PyTorch, Ultralytics YOLOv11, OpenCV |
| **Database** | SQLAlchemy, SQLite (dev), PostgreSQL (prod) |
| **Vector DB** | ChromaDB (for RAG) |
| **Weather** | Open-Meteo forecast/geocoding; optional OpenWeatherMap |
| **Market** | Local illustrative estimates until a verified live market provider is configured |
| **SMS** | Twilio / Fast2SMS / MSG91 |
| **Payments** | Razorpay |
| **Frontend** | Responsive HTML/CSS/JavaScript PWA |
| **Deployment** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### 1. Setup
```bash
unzip ai_farmer.zip
cd ai_farmer
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Or Manual Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python main.py
```

On Windows PowerShell, activate with `.\venv\Scripts\Activate.ps1` and copy the sample settings with `Copy-Item .env.example .env`.

### 3. Access
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8000/app`
- AI provider status: `http://localhost:8000/api/v1/ai/status` (authenticated)
- Location suggestions: `GET /api/v1/locations/search?query=Ludhiana` (authenticated)
- Automatic field recommendations: `POST /api/v1/farm/suggestions` (authenticated)
- Mobile web app: open the dashboard in a mobile browser and use its install option when available

### 4. Test Flow
```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","password":"farmer123","name":"Ram Singh"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543210","password":"farmer123"}'

# Create Profile
curl -X POST "http://localhost:8000/api/v1/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state":"Punjab","district":"Ludhiana","farm_size_acres":5}'

# Select Crop
curl -X POST "http://localhost:8000/api/v1/crops/select" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"crop_name":"wheat","variety":"HD 2967","season":"rabi","field_area_acres":5}'

# Analyze Farm
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"farmer_id":"YOUR_ID","state":"Punjab","district":"Ludhiana","target_crop":"wheat"}'
```

---

## 📚 API Documentation

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new farmer |
| POST | `/api/v1/auth/login` | Login and get JWT |
| GET | `/api/v1/auth/me` | Get current user |

### Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/profile` | Create/update profile |
| GET | `/api/v1/profile` | Get profile |

### Crop Lifecycle
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crops/select` | Start crop tracking |
| GET | `/api/v1/cycles` | List crop cycles |
| GET | `/api/v1/cycles/{id}/summary` | Lifecycle summary |
| GET | `/api/v1/cycles/{id}/timeline` | Visual timeline |
| PATCH | `/api/v1/cycles/{id}` | Update cycle |
| POST | `/api/v1/cycles/{id}/log` | Log activity |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze` | Full multi-agent analysis |
| POST | `/api/v1/analyze/stream` | Stream agent progress and final analysis as server-sent events |
| POST | `/api/v1/farm/suggestions` | Crop, seed, fertilizer, weather, and soil suggestions for a farm |
| GET | `/api/v1/locations/search` | Search place names and farm coordinates |
| GET | `/api/v1/ai/status` | Safe AI provider readiness |
| POST | `/api/v1/detect-disease` | Disease detection from image |

### E-Commerce
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/shop/search` | Search products |
| GET | `/api/v1/shop/categories` | Product categories |
| GET | `/api/v1/shop/recommendations` | Crop-specific inputs |
| POST | `/api/v1/shop/cart/add` | Add to cart |
| POST | `/api/v1/shop/order` | Place order |

### Dashboard & Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/summary` | Farmer dashboard |
| GET | `/api/v1/notifications` | Get notifications |
| GET | `/api/v1/records` | Farm records |

---

## 🗄️ Database Schema

### Core Tables
- **users** — Authentication (phone, password_hash, name, email)
- **farmer_profiles** — Complete farm profile with location, soil, irrigation
- **crop_cycles** — Full lifecycle tracking from sowing to selling
- **farm_records** — Activity logs (irrigation, fertilizer, pest, harvest)
- **orders** — E-commerce orders with payment tracking
- **notifications** — SMS, push, WhatsApp alerts
- **agent_execution_logs** — AI agent audit trail

---

## 🐳 Deployment

```bash
# Docker
docker-compose up --build

# Production checklist:
# - Set DEBUG=false
# - Use PostgreSQL
# - Configure Redis
# - Enable HTTPS
# - Set up monitoring
```

---

## 🗺️ Roadmap

### Current prototype
- Farmer login, sequential agent workflows, responsive PWA, crop tracking, and farm diary
- Review provider configuration, deployment security, data quality, and agronomic advice before production use

### Phase 2: Intelligence Enhancement (Q3 2026)
- 🔄 YOLOv11 disease detection
- 🔄 Agmarknet live prices
- 🔄 RAG with ChromaDB
- 🔄 UPI/Razorpay payments
- 🔄 SMS/WhatsApp alerts

### Phase 3: Mobile & Scale (Q4 2026)
- 🔄 React Native app
- 🔄 Hindi/Telugu/Tamil voice input
- 🔄 Offline-first architecture
- 🔄 Push notifications

### Phase 4: Ecosystem (2027)
- 🔄 FPO integration
- 🔄 Blockchain supply chain
- 🔄 Drone monitoring
- 🔄 Satellite imagery (NDVI)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**🌾 AI Farmer v3.0 — Empowering Indian Farmers with AI 🌾**

*Built with ❤️ for India's 150 million farmers*

</div>
# farmers
