"""Market intelligence service for crop price prediction."""
import requests
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import get_settings
from app.utils import logger

settings = get_settings()


class MarketService:
    """Provides market price data and price predictions."""

    def __init__(self):
        self.api_key = settings.market_api_key
        self.mock_mode = True  # Most Indian agri APIs require registration

    def get_market_prices(self, commodity: str, state: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get current market prices for a commodity."""
        if self.mock_mode:
            return self._generate_mock_prices(commodity, state)

        # Real integration would call Agmarknet or similar APIs
        return self._generate_mock_prices(commodity, state)

    def _generate_mock_prices(self, commodity: str, state: str) -> List[Dict[str, Any]]:
        """Generate realistic mock market prices for Indian commodities."""
        base_prices = {
            "rice": 2200, "wheat": 2100, "maize": 1800, "cotton": 6500,
            "sugarcane": 340, "pulses": 5500, "mustard": 5200, "groundnut": 5800,
            "soybean": 4200, "potato": 1200, "tomato": 2500, "onion": 1800,
            "chili": 8000, "turmeric": 9000, "banana": 2200, "mango": 4500
        }

        markets_by_state = {
            "punjab": ["Ludhiana", "Amritsar", "Patiala"],
            "haryana": ["Karnal", "Hisar", "Ambala"],
            "uttar pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi"],
            "maharashtra": ["Pune", "Nagpur", "Nashik", "Mumbai"],
            "karnataka": ["Bangalore", "Mysore", "Hubli"],
            "tamil nadu": ["Chennai", "Coimbatore", "Madurai"],
            "andhra pradesh": ["Vijayawada", "Visakhapatnam", "Guntur"],
            "gujarat": ["Ahmedabad", "Surat", "Rajkot"],
            "rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
            "west bengal": ["Kolkata", "Howrah", "Siliguri"],
        }

        base = base_prices.get(commodity.lower(), 3000)
        markets = markets_by_state.get(state.lower(), ["Main Market"])
        prices = []

        for market in markets:
            variation = random.uniform(0.85, 1.15)
            modal = base * variation
            prices.append({
                "commodity": commodity.title(),
                "market": market,
                "min_price_inr_per_quintal": round(modal * 0.9, 2),
                "max_price_inr_per_quintal": round(modal * 1.1, 2),
                "modal_price_inr_per_quintal": round(modal, 2),
                "price_trend": random.choice(["rising", "falling", "stable"]),
                "forecast_next_30_days": random.choice(["Expected to rise 5-10%", "Expected to remain stable", "May decline slightly"]),
                "date": datetime.now().strftime("%Y-%m-%d")
            })

        return prices

    def predict_profit(self, crop: str, yield_quintal: float, state: str, cost_per_acre: float) -> Dict[str, Any]:
        """Predict profit based on yield and market prices."""
        prices = self.get_market_prices(crop, state)
        avg_price = sum(p["modal_price_inr_per_quintal"] for p in prices) / len(prices)

        revenue = yield_quintal * avg_price
        profit = revenue - cost_per_acre
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0

        return {
            "crop": crop,
            "projected_yield_quintal": yield_quintal,
            "avg_market_price_per_quintal": round(avg_price, 2),
            "projected_revenue_per_acre": round(revenue, 2),
            "estimated_cost_per_acre": round(cost_per_acre, 2),
            "projected_profit_per_acre": round(profit, 2),
            "profit_margin_percent": round(profit_margin, 2),
            "break_even_yield": round(cost_per_acre / avg_price, 2) if avg_price > 0 else 0,
            "risk_level": "low" if profit_margin > 30 else "medium" if profit_margin > 15 else "high",
            "recommendation": "Highly profitable" if profit_margin > 40 else "Profitable" if profit_margin > 20 else "Marginal" if profit_margin > 0 else "Loss expected"
        }


market_service_instance = MarketService()
