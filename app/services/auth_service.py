"""Authentication service for AI Farmer."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings
from app.services.database import db_service
from app.utils import logger

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return payload
    except JWTError:
        return None


class AuthService:
    """Handles user authentication and registration."""

    def register(self, phone: str, password: str, name: str, email: str = None) -> Dict[str, Any]:
        """Register a new farmer."""
        # Check if user exists
        existing = db_service.get_user_by_phone(phone)
        if existing:
            return {"error": "Phone number already registered", "success": False}

        result = db_service.create_user(phone, password, name, email)
        if "error" in result:
            return {"error": result["error"], "success": False}

        # Generate token
        token = create_access_token({"sub": result["id"], "phone": phone})

        return {
            "success": True,
            "message": "Registration successful",
            "user_id": result["id"],
            "name": name,
            "phone": phone,
            "token": token,
            "token_type": "bearer"
        }

    def login(self, phone: str, password: str) -> Dict[str, Any]:
        """Login farmer and return JWT token."""
        user = db_service.get_user_by_phone(phone)
        if not user:
            return {"error": "Invalid phone or password", "success": False}

        if not db_service.verify_password(password, user.password_hash):
            return {"error": "Invalid phone or password", "success": False}

        if not user.is_active:
            return {"error": "Account is deactivated", "success": False}

        # Update last login
        db_service.update_last_login(user.id)

        # Generate token
        token = create_access_token({"sub": user.id, "phone": phone, "name": user.name})

        # Get profile if exists
        profile = db_service.get_profile(user.id)

        return {
            "success": True,
            "message": "Login successful",
            "user_id": user.id,
            "name": user.name,
            "phone": user.phone,
            "profile_complete": profile is not None,
            "token": token,
            "token_type": "bearer"
        }

    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token."""
        payload = verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        user = db_service.get_user_by_id(user_id)
        if not user:
            return None

        return {
            "id": user.id,
            "phone": user.phone,
            "name": user.name,
            "email": user.email,
            "user_type": user.user_type,
            "is_verified": user.is_verified
        }


auth_service = AuthService()
