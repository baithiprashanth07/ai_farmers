"""Enhanced Database with Authentication, Profiles, and Crop Lifecycle."""
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import uuid
from passlib.context import CryptContext
from app.config import get_settings
from app.utils import logger

settings = get_settings()
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============ AUTHENTICATION ============
class User(Base):
    """User authentication table."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    user_type = Column(String(20), default="farmer")  # farmer, dealer, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    crop_cycles = relationship("CropCycle", back_populates="user")


class FarmerProfile(Base):
    """Extended farmer profile with complete details."""
    __tablename__ = "farmer_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # Location
    state = Column(String(50))
    district = Column(String(50))
    village = Column(String(100))
    pincode = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)

    # Farm Details
    farm_size_acres = Column(Float)
    total_land_acres = Column(Float)
    owned_land_acres = Column(Float)
    leased_land_acres = Column(Float)
    soil_type = Column(String(30))
    soil_ph = Column(Float)
    irrigation_type = Column(String(30))
    irrigation_source = Column(String(50))  # canal, tubewell, pond, rainfed

    # Farming Profile
    farming_experience_years = Column(Integer)
    farming_type = Column(String(30))  # organic, conventional, mixed
    crops_history = Column(Text)  # JSON array of past crops
    current_crops = Column(Text)  # JSON array of current crops
    preferred_crops = Column(Text)  # JSON array

    # Financial
    annual_income_inr = Column(Float)
    has_kcc = Column(Boolean, default=False)
    kcc_number = Column(String(50), nullable=True)
    has_insurance = Column(Boolean, default=False)
    insurance_type = Column(String(50), nullable=True)

    # Equipment
    equipment_owned = Column(Text)  # JSON array

    # Preferences
    language_preference = Column(String(20), default="en")
    notification_sms = Column(Boolean, default=True)
    notification_whatsapp = Column(Boolean, default=True)
    notification_push = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")


# ============ CROP LIFECYCLE ============
class CropCycle(Base):
    """Tracks complete crop lifecycle from sowing to selling."""
    __tablename__ = "crop_cycles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Crop Info
    crop_name = Column(String(50), nullable=False)
    variety = Column(String(100))
    season = Column(String(20))  # kharif, rabi, zaid
    year = Column(Integer)

    # Land & Input
    field_area_acres = Column(Float)
    soil_type = Column(String(30))
    seed_used = Column(String(100))
    seed_quantity_kg = Column(Float)
    seed_cost_inr = Column(Float)

    # Timeline
    sowing_date = Column(DateTime)
    germination_date = Column(DateTime)
    first_irrigation_date = Column(DateTime)
    first_fertilizer_date = Column(DateTime)
    flowering_date = Column(DateTime)
    fruiting_date = Column(DateTime)
    harvest_date = Column(DateTime)
    expected_harvest_date = Column(DateTime)

    # Inputs Log (JSON)
    irrigations_log = Column(Text, default="[]")  # [{date, method, hours, cost}]
    fertilizers_log = Column(Text, default="[]")  # [{date, type, quantity, cost}]
    pesticides_log = Column(Text, default="[]")  # [{date, pest/disease, chemical, quantity, cost}]
    labor_log = Column(Text, default="[]")  # [{date, activity, workers, hours, cost}]

    # Expenses
    total_input_cost_inr = Column(Float, default=0)
    total_labor_cost_inr = Column(Float, default=0)
    total_machinery_cost_inr = Column(Float, default=0)
    total_other_cost_inr = Column(Float, default=0)

    # Yield & Output
    expected_yield_quintal = Column(Float)
    actual_yield_quintal = Column(Float)
    yield_quality = Column(String(20))  # excellent, good, average, poor

    # Market & Profit
    market_sold_to = Column(String(100))  # mandi name, FPO, direct
    selling_price_per_quintal = Column(Float)
    total_revenue_inr = Column(Float)
    total_profit_inr = Column(Float)
    profit_per_acre_inr = Column(Float)

    # Status
    status = Column(String(20), default="planned")  # planned, sown, growing, flowering, harvesting, sold, completed
    progress_percent = Column(Integer, default=0)

    # AI Recommendations Applied
    ai_recommendations_applied = Column(Text, default="[]")  # JSON array
    ai_alerts_received = Column(Text, default="[]")  # JSON array

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="crop_cycles")


# ============ FARM RECORDS (Enhanced) ============
class FarmRecord(Base):
    """Farm activity and record keeping."""
    __tablename__ = "farm_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    crop_cycle_id = Column(String, ForeignKey("crop_cycles.id"), nullable=True)
    record_type = Column(String(30))  # sowing, irrigation, fertilization, pest_control, harvest, expense, income, weather_alert, market_alert
    crop_name = Column(String(50))
    date = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)
    amount_inr = Column(Float)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ E-COMMERCE ============
class Order(Base):
    """E-commerce orders."""
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(20), unique=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    items = Column(Text)  # JSON array of products
    total_amount = Column(Float)
    discount_amount = Column(Float, default=0)
    delivery_charge = Column(Float, default=0)
    final_amount = Column(Float)
    status = Column(String(20), default="pending")  # pending, confirmed, packed, shipped, delivered, cancelled, returned
    payment_method = Column(String(30))  # COD, UPI, CARD, WALLET
    payment_status = Column(String(20), default="pending")  # pending, paid, failed, refunded
    shipping_address = Column(Text)  # JSON
    tracking_number = Column(String(50), nullable=True)
    estimated_delivery = Column(DateTime)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")


# ============ NOTIFICATIONS ============
class Notification(Base):
    """SMS, Push, and WhatsApp notifications."""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String(20))  # sms, push, whatsapp, email
    category = Column(String(30))  # weather, pest, market, scheme, irrigation, harvest
    title = Column(String(200))
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)


# ============ AGENT LOGS ============
class AgentExecutionLog(Base):
    """Log of agent executions for auditing."""
    __tablename__ = "agent_execution_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    agent_name = Column(String(50))
    input_data = Column(Text)
    output_data = Column(Text)
    execution_time_ms = Column(Integer)
    status = Column(String(20))  # success, error, partial
    timestamp = Column(DateTime, default=datetime.utcnow)


class DatabaseService:
    """Enhanced database service for AI Farmer."""

    def __init__(self):
        self.engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
            pool_pre_ping=True,
            echo=settings.debug
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        logger.info("Enhanced database initialized with auth, profiles, crop cycles")

    def get_session(self) -> Session:
        return self.SessionLocal()

    # ============ USER AUTH ============
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, phone: str, password: str, name: str, email: str = None) -> Dict[str, Any]:
        session = self.get_session()
        try:
            user = User(
                phone=phone,
                password_hash=self.hash_password(password),
                name=name,
                email=email,
                user_type="farmer"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return {"id": user.id, "phone": user.phone, "name": user.name, "created": True}
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.phone == phone).first()
        finally:
            session.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def update_last_login(self, user_id: str):
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    # ============ FARMER PROFILE ============
    def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                profile = FarmerProfile(user_id=user_id)
                session.add(profile)

            for key, value in profile_data.items():
                if hasattr(profile, key) and (
                    value is not None or key in {"latitude", "longitude"}
                ):
                    if key in ["crops_history", "current_crops", "preferred_crops", "equipment_owned"]:
                        setattr(profile, key, json.dumps(value) if isinstance(value, list) else value)
                    else:
                        setattr(profile, key, value)

            profile.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(profile)
            return {"success": True, "profile_id": profile.id}
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating profile: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                return None
            return {
                "id": profile.id,
                "state": profile.state,
                "district": profile.district,
                "village": profile.village,
                "latitude": profile.latitude,
                "longitude": profile.longitude,
                "farm_size_acres": profile.farm_size_acres,
                "soil_type": profile.soil_type,
                "irrigation_type": profile.irrigation_type,
                "farming_type": profile.farming_type,
                "language_preference": profile.language_preference,
                "crops_history": json.loads(profile.crops_history) if profile.crops_history else [],
                "current_crops": json.loads(profile.current_crops) if profile.current_crops else [],
                "preferred_crops": json.loads(profile.preferred_crops) if profile.preferred_crops else [],
            }
        finally:
            session.close()

    def update_profile_language(self, user_id: str, language: str) -> bool:
        session = self.get_session()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                return False
            profile.language_preference = language
            profile.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating language preference: {e}")
            raise
        finally:
            session.close()

    # ============ CROP CYCLE ============
    def create_crop_cycle(self, user_id: str, crop_data: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session()
        try:
            cycle = CropCycle(
                user_id=user_id,
                crop_name=crop_data["crop_name"],
                variety=crop_data.get("variety"),
                season=crop_data.get("season"),
                year=crop_data.get("year", datetime.now().year),
                field_area_acres=crop_data.get("field_area_acres"),
                soil_type=crop_data.get("soil_type"),
                seed_used=crop_data.get("seed_used"),
                seed_quantity_kg=crop_data.get("seed_quantity_kg"),
                seed_cost_inr=crop_data.get("seed_cost_inr"),
                sowing_date=datetime.fromisoformat(crop_data["sowing_date"]) if "sowing_date" in crop_data else None,
                expected_harvest_date=datetime.fromisoformat(crop_data["expected_harvest_date"]) if "expected_harvest_date" in crop_data else None,
                expected_yield_quintal=crop_data.get("expected_yield_quintal"),
                status="planned"
            )
            session.add(cycle)
            session.commit()
            session.refresh(cycle)
            return {"success": True, "cycle_id": cycle.id, "crop": cycle.crop_name}
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating crop cycle: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def get_crop_cycles(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(CropCycle).filter(CropCycle.user_id == user_id)
            if status:
                query = query.filter(CropCycle.status == status)
            cycles = query.order_by(CropCycle.created_at.desc()).all()

            result = []
            for c in cycles:
                result.append({
                    "id": c.id,
                    "crop_name": c.crop_name,
                    "variety": c.variety,
                    "season": c.season,
                    "status": c.status,
                    "progress_percent": c.progress_percent,
                    "field_area_acres": c.field_area_acres,
                    "sowing_date": c.sowing_date.isoformat() if c.sowing_date else None,
                    "expected_harvest_date": c.expected_harvest_date.isoformat() if c.expected_harvest_date else None,
                    "actual_yield_quintal": c.actual_yield_quintal,
                    "total_revenue_inr": c.total_revenue_inr,
                    "total_profit_inr": c.total_profit_inr,
                    "created_at": c.created_at.isoformat()
                })
            return result
        finally:
            session.close()

    def get_crop_cycle_summary(self, cycle_id: str) -> Dict[str, Any]:
        """Get complete lifecycle summary for a crop cycle."""
        session = self.get_session()
        try:
            c = session.query(CropCycle).filter(CropCycle.id == cycle_id).first()
            if not c:
                return {"error": "Crop cycle not found"}

            total_expenses = (c.total_input_cost_inr or 0) + (c.total_labor_cost_inr or 0) + (c.total_machinery_cost_inr or 0) + (c.total_other_cost_inr or 0)

            return {
                "cycle_id": c.id,
                "crop_name": c.crop_name,
                "variety": c.variety,
                "season": c.season,
                "year": c.year,
                "status": c.status,
                "progress_percent": c.progress_percent,

                # Timeline
                "sowing_date": c.sowing_date.isoformat() if c.sowing_date else None,
                "germination_date": c.germination_date.isoformat() if c.germination_date else None,
                "flowering_date": c.flowering_date.isoformat() if c.flowering_date else None,
                "harvest_date": c.harvest_date.isoformat() if c.harvest_date else None,
                "expected_harvest_date": c.expected_harvest_date.isoformat() if c.expected_harvest_date else None,

                # Inputs
                "seed_used": c.seed_used,
                "seed_quantity_kg": c.seed_quantity_kg,
                "field_area_acres": c.field_area_acres,
                "irrigations": json.loads(c.irrigations_log) if c.irrigations_log else [],
                "fertilizers": json.loads(c.fertilizers_log) if c.fertilizers_log else [],
                "pesticides": json.loads(c.pesticides_log) if c.pesticides_log else [],
                "labor": json.loads(c.labor_log) if c.labor_log else [],

                # Financial
                "total_expenses_inr": total_expenses,
                "total_input_cost_inr": c.total_input_cost_inr,
                "total_labor_cost_inr": c.total_labor_cost_inr,
                "total_revenue_inr": c.total_revenue_inr,
                "total_profit_inr": c.total_profit_inr,
                "profit_per_acre_inr": c.profit_per_acre_inr,

                # Output
                "expected_yield_quintal": c.expected_yield_quintal,
                "actual_yield_quintal": c.actual_yield_quintal,
                "yield_quality": c.yield_quality,
                "selling_price_per_quintal": c.selling_price_per_quintal,
                "market_sold_to": c.market_sold_to,

                # AI
                "ai_recommendations_applied": json.loads(c.ai_recommendations_applied) if c.ai_recommendations_applied else [],
                "ai_alerts_received": json.loads(c.ai_alerts_received) if c.ai_alerts_received else [],
            }
        finally:
            session.close()

    def update_crop_cycle(self, cycle_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session()
        try:
            cycle = session.query(CropCycle).filter(CropCycle.id == cycle_id).first()
            if not cycle:
                return {"error": "Crop cycle not found"}

            for key, value in updates.items():
                if hasattr(cycle, key) and value is not None:
                    if key in ["irrigations_log", "fertilizers_log", "pesticides_log", "labor_log", "ai_recommendations_applied", "ai_alerts_received"]:
                        existing = json.loads(getattr(cycle, key) or "[]")
                        if isinstance(value, list):
                            existing.extend(value)
                        else:
                            existing.append(value)
                        setattr(cycle, key, json.dumps(existing))
                    elif key in ["sowing_date", "germination_date", "flowering_date", "harvest_date", "expected_harvest_date"]:
                        setattr(cycle, key, datetime.fromisoformat(value) if value else None)
                    else:
                        setattr(cycle, key, value)

            cycle.updated_at = datetime.utcnow()
            session.commit()
            return {"success": True, "cycle_id": cycle_id}
        except Exception as e:
            session.rollback()
            return {"error": str(e)}
        finally:
            session.close()

    # ============ FARM RECORDS ============
    def add_farm_record(self, record: Dict[str, Any]) -> str:
        session = self.get_session()
        try:
            db_record = FarmRecord(
                user_id=record.get("user_id", record.get("farmer_id", "")),
                crop_cycle_id=record.get("crop_cycle_id"),
                record_type=record["record_type"],
                crop_name=record.get("crop_name"),
                date=datetime.fromisoformat(record["date"]) if "date" in record else datetime.utcnow(),
                details=record.get("details", ""),
                amount_inr=record.get("amount_inr"),
                metadata_json=json.dumps(record.get("metadata", {}))
            )
            session.add(db_record)
            session.commit()
            return db_record.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding farm record: {e}")
            raise
        finally:
            session.close()

    def get_farm_records(self, user_id: str, record_type: str = None) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(FarmRecord).filter(FarmRecord.user_id == user_id)
            if record_type:
                query = query.filter(FarmRecord.record_type == record_type)
            records = query.order_by(FarmRecord.date.desc()).all()

            return [{
                "id": r.id,
                "record_type": r.record_type,
                "crop_name": r.crop_name,
                "date": r.date.isoformat(),
                "details": r.details,
                "amount_inr": r.amount_inr,
                "metadata": json.loads(r.metadata_json) if r.metadata_json else {}
            } for r in records]
        finally:
            session.close()

    # ============ NOTIFICATIONS ============
    def add_notification(self, user_id: str, notif_type: str, category: str, title: str, message: str) -> str:
        session = self.get_session()
        try:
            notif = Notification(
                user_id=user_id,
                type=notif_type,
                category=category,
                title=title,
                message=message
            )
            session.add(notif)
            session.commit()
            return notif.id
        finally:
            session.close()

    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(Notification).filter(Notification.user_id == user_id)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            notifs = query.order_by(Notification.sent_at.desc()).all()
            return [{
                "id": n.id,
                "type": n.type,
                "category": n.category,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "sent_at": n.sent_at.isoformat()
            } for n in notifs]
        finally:
            session.close()

    # ============ E-COMMERCE ============
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session()
        try:
            order = Order(
                order_number=f"AIF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                user_id=order_data["user_id"],
                items=json.dumps(order_data["items"]),
                total_amount=order_data["total_amount"],
                discount_amount=order_data.get("discount_amount", 0),
                delivery_charge=order_data.get("delivery_charge", 0),
                final_amount=order_data["final_amount"],
                payment_method=order_data.get("payment_method", "COD"),
                shipping_address=json.dumps(order_data["shipping_address"]),
                estimated_delivery=datetime.utcnow() + timedelta(days=7)
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return {"order_id": order.id, "order_number": order.order_number, "status": order.status}
        except Exception as e:
            session.rollback()
            return {"error": str(e)}
        finally:
            session.close()

    def get_orders(self, user_id: str) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            orders = session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
            return [{
                "order_number": o.order_number,
                "items": json.loads(o.items),
                "final_amount": o.final_amount,
                "status": o.status,
                "payment_status": o.payment_status,
                "created_at": o.created_at.isoformat()
            } for o in orders]
        finally:
            session.close()

    # ============ AGENT LOGS ============
    def log_agent_execution(self, log: Dict[str, Any]) -> None:
        session = self.get_session()
        try:
            db_log = AgentExecutionLog(
                request_id=log["request_id"],
                user_id=log.get("user_id"),
                agent_name=log["agent_name"],
                input_data=json.dumps(log.get("input", {})),
                output_data=json.dumps(log.get("output", {})),
                execution_time_ms=log.get("execution_time_ms", 0),
                status=log.get("status", "success")
            )
            session.add(db_log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging agent execution: {e}")
        finally:
            session.close()


db_service = DatabaseService()
