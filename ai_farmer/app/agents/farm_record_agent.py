"""Farm Record Manager Agent - Manages farm records and generates reports."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services.database import db_service
from app.utils import logger
from datetime import datetime

class FarmRecordManagerAgent(BaseAgent):
    """Manages digital farm records, tracks expenses, and generates compliance reports."""

    def __init__(self):
        super().__init__("FarmRecordManagerAgent", "Manages farm records and digital diary")

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        farmer_id = context.get("farmer_id", "unknown")

        # Fetch existing records
        records = db_service.get_farm_records(farmer_id)

        # Generate summary
        summary = self._generate_summary(records)

        state["farm_records"] = {
            "farmer_id": farmer_id,
            "total_records": len(records),
            "records": records[:10],  # Last 10 records
            "summary": summary,
            "compliance_status": self._check_compliance(records),
            "recommended_entries": self._suggest_entries(context)
        }

        self._add_message(state, f"Farm records retrieved: {len(records)} total records. Compliance: {summary['compliance_status']}.", {"records": len(records)}, "medium")
        return state

    def _generate_summary(self, records: list) -> dict:
        expenses = [r for r in records if r.get("record_type") == "expense"]
        income = [r for r in records if r.get("record_type") == "income"]

        total_expense = sum(float(r.get("metadata", {}).get("amount", 0)) for r in expenses)
        total_income = sum(float(r.get("metadata", {}).get("amount", 0)) for r in income)

        return {
            "total_expenses_inr": total_expense,
            "total_income_inr": total_income,
            "net_profit": total_income - total_expense,
            "expense_count": len(expenses),
            "income_count": len(income),
            "compliance_status": "Good" if len(records) > 5 else "Needs more records"
        }

    def _check_compliance(self, records: list) -> dict:
        has_sowing = any(r.get("record_type") == "sowing" for r in records)
        has_harvest = any(r.get("record_type") == "harvest" for r in records)
        has_pesticide = any(r.get("record_type") == "pest_control" for r in records)

        return {
            "sowing_recorded": has_sowing,
            "harvest_recorded": has_harvest,
            "pesticide_recorded": has_pesticide,
            "insurance_eligible": has_sowing and has_harvest,
            "organic_cert_eligible": not has_pesticide
        }

    def _suggest_entries(self, context: dict) -> list:
        suggestions = []
        crop = context.get("target_crop")
        if crop:
            suggestions.append(f"Record sowing date for {crop}")
            suggestions.append(f"Log fertilizer application for {crop}")
            suggestions.append(f"Track irrigation schedule for {crop}")
        return suggestions
