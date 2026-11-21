"""Indicative state-wise crop reference for Indian farm-planning workflows."""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "india_state_crops.json"
_STATE_ALIASES = {
    "andaman": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "nct of delhi": "Delhi",
    "jammu & kashmir": "Jammu and Kashmir",
    "jammu kashmir": "Jammu and Kashmir",
    "pondicherry": "Puducherry",
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


@lru_cache(maxsize=1)
def _load_reference() -> Dict[str, Any]:
    with _DATA_PATH.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def list_indian_regions() -> List[Dict[str, Any]]:
    """Return all states and union territories and the languages used in that region."""
    return _load_reference()["states"]


def get_state_crop_reference(state: str) -> Optional[Dict[str, Any]]:
    """Resolve a state/UT name and return its indicative crop reference."""
    normalized = _normalize(state)
    canonical = _STATE_ALIASES.get(normalized, state)
    normalized_canonical = _normalize(canonical)
    for region in _load_reference()["states"]:
        if _normalize(region["name"]) == normalized_canonical:
            return region
    return None


def get_crop_reference_note() -> str:
    return _load_reference()["source_note"]
