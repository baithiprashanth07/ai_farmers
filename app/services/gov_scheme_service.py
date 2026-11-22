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
                "coverage": "National",
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
                "coverage": "National",
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
                "coverage": "National; notified crops and enrollment windows vary by state",
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
                "coverage": "National; delivered through state and district agencies",
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
                "coverage": "National",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Financing facility for investment in viable projects for post-harvest management infrastructure.",
                "eligibility": ["Farmers", "FPOs", "PACS", "Marketing Cooperative Societies", "SHGs"],
                "benefits": ["Interest subvention of 3%", "Credit guarantee coverage", "Moratorium of 2 years"],
                "application_process": "Apply through participating banks with project proposal.",
                "deadline": "Check the official portal for current application status",
                "official_link": "https://agriinfra.dac.gov.in"
            },
            {
                "scheme_name": "Paramparagat Krishi Vikas Yojana (PKVY)",
                "coverage": "National; implementation details vary by state",
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
                "coverage": "National",
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
                "coverage": "National; crop and district eligibility varies",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Increases production of rice, wheat, pulses, coarse cereals through area expansion and productivity enhancement.",
                "eligibility": ["Farmers growing targeted crops", "Willing to adopt improved practices"],
                "benefits": ["Subsidized seeds", "Demonstration support", "Farm machinery subsidy"],
                "application_process": "Contact District Agriculture Officer during crop season.",
                "deadline": "Crop season specific",
                "official_link": "https://nfsm.gov.in"
            },
            {
                "scheme_name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
                "coverage": "National; component availability and support vary by state",
                "ministry": "Ministry of Agriculture & Farmers Welfare",
                "description": "Supports improved irrigation access and water-use efficiency through notified programme components.",
                "eligibility": ["Farmers in areas covered by an active state programme"],
                "benefits": ["Potential support for irrigation and water-use efficiency; check current state notifications"],
                "application_process": "Check with the state agriculture or irrigation department for active components and application windows.",
                "deadline": "State and component specific",
                "official_link": "https://pmksy.gov.in"
            },
            {
                "scheme_name": "PM-KUSUM",
                "coverage": "National; state implementation and application windows vary",
                "ministry": "Ministry of New and Renewable Energy",
                "description": "Supports eligible solar pumps and solarisation components through state implementing agencies.",
                "eligibility": ["Eligibility depends on the active component and state notification"],
                "benefits": ["Potential support for solar pumps or pump solarisation under active components"],
                "application_process": "Check the official portal and your state implementing agency for current availability.",
                "deadline": "State and component specific",
                "official_link": "https://pmkusum.mnre.gov.in"
            },
        ]

    def get_relevant_schemes(self, state: str, crop: str = None, farm_size: float = None) -> List[Dict[str, Any]]:
        """Get national schemes ranked for a profile; state rollout must be verified."""
        relevant = []
        crop_name = (crop or "").strip().lower()
        for source in self.schemes:
            scheme = dict(source)
            relevance = 50
            searchable_text = " ".join(
                [scheme["scheme_name"], scheme["description"], *scheme["eligibility"]]
            ).lower()
            if crop_name and crop_name in searchable_text:
                relevance += 20
            if (
                farm_size is not None
                and farm_size <= 2
                and any("small" in item.lower() or "marginal" in item.lower() for item in scheme["eligibility"])
            ):
                relevance += 15
            scheme["relevance_score"] = min(relevance, 100)
            scheme["farmer_state"] = state
            relevant.append(scheme)

        return sorted(relevant, key=lambda x: x["relevance_score"], reverse=True)

    def get_scheme_details(self, scheme_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific scheme."""
        for scheme in self.schemes:
            if scheme["scheme_name"].lower() == scheme_name.lower():
                return scheme
        return {"error": "Scheme not found"}


gov_scheme_service_instance = GovernmentSchemeService()
