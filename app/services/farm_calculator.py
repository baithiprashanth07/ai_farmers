"""Transparent unit and budget calculations for farmer-entered estimates."""
from typing import Any, Dict, Optional


def calculate_fertilizer_requirement(
    area_acres: float,
    rate_kg_per_acre: float,
    price_inr_per_kg: Optional[float] = None,
) -> Dict[str, float]:
    """Scale a user-provided application rate to an area and estimate its cost."""
    if area_acres <= 0 or rate_kg_per_acre < 0:
        raise ValueError("Area must be positive and application rate cannot be negative.")
    if price_inr_per_kg is not None and price_inr_per_kg < 0:
        raise ValueError("Price cannot be negative.")
    quantity_kg = area_acres * rate_kg_per_acre
    result = {"quantity_kg": round(quantity_kg, 2)}
    if price_inr_per_kg is not None:
        result["estimated_cost_inr"] = round(quantity_kg * price_inr_per_kg, 2)
    return result


def estimate_crop_budget(
    area_acres: float,
    yield_quintal_per_acre: float,
    price_inr_per_quintal: float,
    cost_inr_per_acre: float,
) -> Dict[str, float]:
    """Estimate gross revenue and net return from farmer-entered figures."""
    if area_acres <= 0:
        raise ValueError("Area must be positive.")
    if min(yield_quintal_per_acre, price_inr_per_quintal, cost_inr_per_acre) < 0:
        raise ValueError("Yield, price, and cost cannot be negative.")
    total_yield = area_acres * yield_quintal_per_acre
    gross_revenue = total_yield * price_inr_per_quintal
    total_cost = area_acres * cost_inr_per_acre
    return {
        "total_yield_quintal": round(total_yield, 2),
        "gross_revenue_inr": round(gross_revenue, 2),
        "total_cost_inr": round(total_cost, 2),
        "estimated_net_inr": round(gross_revenue - total_cost, 2),
    }
