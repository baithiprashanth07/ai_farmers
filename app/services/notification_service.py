"""Notification service for SMS, Push, and WhatsApp alerts."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.database import db_service
from app.utils import logger


class NotificationService:
    """Sends agricultural alerts via SMS, WhatsApp, and Push notifications."""

    def __init__(self):
        self.sms_enabled = True  # Integrate with Twilio/Exotel/Fast2SMS
        self.whatsapp_enabled = True  # Integrate with WhatsApp Business API

    def send_weather_alert(self, user_id: str, phone: str, weather_data: Dict[str, Any]) -> bool:
        """Send weather-based farming alert."""
        forecast = weather_data.get("forecast", [])
        if not forecast:
            return False

        alerts = []
        for day in forecast[:3]:
            if day.get("rainfall_mm", 0) > 20:
                alerts.append(f"🌧️ Heavy rain ({day['rainfall_mm']}mm) expected on {day['date']}. Avoid spraying.")
            if day.get("temp_max_c", 0) > 40:
                alerts.append(f"🌡️ Heat wave alert: {day['temp_max_c']}°C on {day['date']}. Increase irrigation.")
            if day.get("temp_min_c", 0) < 10:
                alerts.append(f"❄️ Cold wave alert: {day['temp_min_c']}°C on {day['date']}. Protect crops.")

        if alerts:
            message = "\n".join(alerts)
            self._send_sms(phone, message)
            db_service.add_notification(user_id, "sms", "weather", "Weather Alert", message)
            logger.info(f"Weather alert sent to {phone}")
            return True
        return False

    def send_pest_alert(self, user_id: str, phone: str, crop: str, pest_data: Dict[str, Any]) -> bool:
        """Send pest monitoring alert."""
        pests = pest_data.get("common_pests", [])
        if not pests:
            return False

        high_risk = [p for p in pests if any("bollworm" in p["pest_name"].lower() or "borer" in p["pest_name"].lower() for p in pests)]

        if high_risk:
            message = f"⚠️ Pest Alert for {crop.title()}: High-risk pests detected. Check fields immediately. Install pheromone traps."
            self._send_sms(phone, message)
            db_service.add_notification(user_id, "sms", "pest", "Pest Alert", message)
            return True
        return False

    def send_irrigation_reminder(self, user_id: str, phone: str, crop: str, days_since_last: int) -> bool:
        """Send irrigation reminder."""
        message = f"💧 Irrigation Reminder: Your {crop.title()} crop needs watering. Last irrigation was {days_since_last} days ago. Check soil moisture."
        self._send_sms(phone, message)
        db_service.add_notification(user_id, "sms", "irrigation", "Irrigation Reminder", message)
        return True

    def send_harvest_reminder(self, user_id: str, phone: str, crop: str, expected_date: str) -> bool:
        """Send harvest readiness alert."""
        message = f"🌾 Harvest Alert: Your {crop.title()} crop is approaching harvest window ({expected_date}). Prepare labor and storage. Check market prices before selling."
        self._send_sms(phone, message)
        db_service.add_notification(user_id, "sms", "harvest", "Harvest Reminder", message)
        return True

    def send_market_price_alert(self, user_id: str, phone: str, crop: str, price: float, trend: str) -> bool:
        """Send market price movement alert."""
        emoji = "📈" if trend == "rising" else "📉" if trend == "falling" else "➡️"
        message = f"{emoji} Market Update: {crop.title()} price is Rs.{price}/quintal ({trend}). Consider selling if price is favorable."
        self._send_sms(phone, message)
        db_service.add_notification(user_id, "sms", "market", "Market Price Alert", message)
        return True

    def send_scheme_alert(self, user_id: str, phone: str, scheme_name: str, deadline: str) -> bool:
        """Send government scheme deadline alert."""
        message = f"🏛️ Scheme Alert: {scheme_name} application deadline is {deadline}. Apply now to avail benefits. Visit nearest CSC or KVK."
        self._send_sms(phone, message)
        db_service.add_notification(user_id, "sms", "scheme", "Government Scheme Alert", message)
        return True

    def send_welcome_message(self, phone: str, name: str) -> bool:
        """Send welcome SMS to new user."""
        message = f"🌾 Welcome to AI Farmer, {name}! Your smart farming assistant is ready. Select your crop to get personalized recommendations. Call 1800-180-1551 for help."
        self._send_sms(phone, message)
        return True

    def _send_sms(self, phone: str, message: str) -> bool:
        """Send SMS via gateway (placeholder for Twilio/Fast2SMS integration)."""
        # TODO: Integrate with actual SMS provider
        # Example: Twilio, Fast2SMS, Exotel, MSG91
        logger.info(f"[SMS TO {phone}]: {message[:100]}...")
        return True

    def _send_whatsapp(self, phone: str, message: str) -> bool:
        """Send WhatsApp message (placeholder for WhatsApp Business API)."""
        logger.info(f"[WHATSAPP TO {phone}]: {message[:100]}...")
        return True

    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get all notifications for a user."""
        return db_service.get_notifications(user_id, unread_only)


notification_service = NotificationService()
