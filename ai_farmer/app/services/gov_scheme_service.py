"""Government scheme advisory service."""
from typing import List, Dict, Any
from app.utils import logger


class GovernmentSchemeService:
    """Provides information on government agricultural schemes."""

    def __init__(self):
        self.schemes = self._load_schemes()

    def _load_schemes(self) -> List[Dict[str, Any]]:
        """Load government scheme database."""
        return [
            {
                "scheme_name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Income support of Rs. 6000/- per year to all farmer families across the country in three equal installments.",
                "eligibility": ["Small and marginal farmers", "Landholding farmers", "Valid bank account"],
                "benefits": ["Rs. 6000/year direct benefit transfer", "Financial support for agricultural inputs"],
                "application_process": "Apply through CSC, Revenue Department, or PM-KISAN portal with land records and Aadhaar.",
                "deadline": "Ongoing",
                "official_link": "https://pmkisan.gov.in"
            },
            {
                "scheme_name": "Soil Health Card Scheme",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Provides soil health cards to farmers with crop-wise recommendations for nutrients and fertilizers.",
                "eligibility": ["All farmers", "Registered with local agriculture department"],
                "benefits": ["Free soil testing", "Personalized fertilizer recommendations", "Improved soil health"],
                "application_process": "Contact nearest soil testing laboratory or Krishi Vigyan Kendra.",
                "deadline": "Ongoing",
                "official_link": "https://soilhealth.dac.gov.in"
            },
            {
                "scheme_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Crop insurance scheme providing financial support to farmers suffering crop loss due to natural calamities.",
                "eligibility": ["All farmers growing notified crops", "Loanee and non-loanee farmers"],
                "benefits": ["Comprehensive risk coverage", "Low premium rates (1.5%-5%)", "Quick claim settlement"],
                "application_process": "Enroll through bank, CSC, or insurance company before sowing season.",
                "deadline": "Before sowing season",
                "official_link": "https://pmfby.gov.in"
            },
            {
                "scheme_name": "National Mission on Agricultural Extension & Technology (NMAET)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Promotes agricultural extension through ATMA, skill development, and demonstration farms.",
                "eligibility": ["Farmers", "Farmer Producer Organizations", "Self Help Groups"],
                "benefits": ["Training and capacity building", "Exposure visits", "Demonstration plots"],
                "application_process": "Contact District Agriculture Officer or ATMA committee.",
                "deadline": "Ongoing",
                "official_link": "https://extensionreforms.dac.gov.in"
            },
            {
                "scheme_name": "Agricultural Infrastructure Fund (AIF)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Financing facility for investment in viable projects for post-harvest management infrastructure.",
                "eligibility": ["Farmers", "FPOs", "PACS", "Marketing Cooperative Societies", "SHGs"],
                "benefits": ["Interest subvention of 3%", "Credit guarantee coverage", "Moratorium of 2 years"],
                "application_process": "Apply through participating banks with project proposal.",
                "deadline": "2025-2026",
                "official_link": "https://agriinfra.dac.gov.in"
            },
            {
                "scheme_name": "Paramparagat Krishi Vikas Yojana (PKVY)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Promotes organic farming through cluster approach with financial assistance.",
                "eligibility": ["Farmers willing to adopt organic farming", "Minimum 20 farmers per cluster"],
                "benefits": ["Rs. 50,000/ha for 3 years", "Training on organic practices", "Certification support"],
                "application_process": "Form cluster and apply through District Agriculture Officer.",
                "deadline": "Ongoing",
                "official_link": "https://pgsindia-ncof.gov.in"
            },
            {
                "scheme_name": "Kisan Credit Card (KCC)",
                "ministry": "Ministry of Finance",
                "description": "Provides farmers with timely access to credit for agricultural needs.",
                "eligibility": ["All farmers", "Tenant farmers", "Share croppers"],
                "benefits": ["Short-term credit up to Rs. 3 lakh", "Interest subvention at 7%", "Flexible repayment"],
                "application_process": "Apply at any bank with land documents and identity proof.",
                "deadline": "Ongoing",
                "official_link": "https://www.nabard.org"
            },
            {
                "scheme_name": "National Food Security Mission (NFSM)",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Increases production of rice, wheat, pulses, coarse cereals through area expansion and productivity enhancement.",
                "eligibility": ["Farmers growing targeted crops", "Willing to adopt improved practices"],
                "benefits": ["Subsidized seeds", "Demonstration support", "Farm machinery subsidy"],
                "application_process": "Contact District Agriculture Officer during crop season.",
                "deadline": "Crop season specific",
                "official_link": "https://nfsm.gov.in"
            }
        ]

    def get_relevant_schemes(self, state: str, crop: str = None, farm_size: float = None) -> List[Dict[str, Any]]:
        """Get government schemes relevant to farmer profile."""
        relevant = self.schemes.copy()

        # In a real system, filter by state-specific schemes
        # For now, return all with relevance scoring
        for scheme in relevant:
            relevance = 50
            if crop and any(c in scheme["description"].lower() for c in [crop.lower(), "crop", "agriculture"]):
                relevance += 20
            if farm_size and farm_size < 5 and "small" in scheme["scheme_name"].lower():
                relevance += 15
            scheme["relevance_score"] = min(relevance, 100)

        return sorted(relevant, key=lambda x: x["relevance_score"], reverse=True)

    def get_scheme_details(self, scheme_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific scheme."""
        for scheme in self.schemes:
            if scheme["scheme_name"].lower() == scheme_name.lower():
                return scheme
        return {"error": "Scheme not found"}


gov_scheme_service_instance = GovernmentSchemeService()
