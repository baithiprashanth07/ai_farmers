"""Indicative, date-based crop monitoring schedules."""
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional


_CROP_ALIASES = {
    "paddy": "rice",
    "chana": "chickpea",
    "gram": "chickpea",
}

_PHASES = (
    (0.10, "Establishment"),
    (0.60, "Vegetative growth"),
    (0.82, "Flowering and reproduction"),
    (0.97, "Produce or grain development"),
    (1.01, "Maturity and harvest preparation"),
)

_CROP_GROUPS = {
    "rice": "cereal",
    "wheat": "cereal",
    "maize": "cereal",
    "chickpea": "pulse",
    "cotton": "fibre",
    "groundnut": "oilseed",
    "soybean": "oilseed",
    "mustard": "oilseed",
    "potato": "vegetable",
    "tomato": "vegetable",
    "onion": "vegetable",
    "sugarcane": "sugarcane",
    "turmeric": "rhizome",
    "banana": "perennial",
    "mango": "perennial",
}

_GENERAL_GUIDANCE = (
    "Confirm planting material and field preparation with the local crop calendar; record the sowing date and field conditions.",
    "Check establishment, stand, moisture, and weeds. Compare observations with local crop guidance.",
    "Observe crop development and reproductive growth. Record stress or symptoms and seek local advice before treatment.",
    "Monitor crop development and field conditions; use soil-test and local advisories for any input decision.",
    "Use crop- and variety-specific maturity signs to plan harvest, drying, and storage.",
)

_GROUP_GUIDANCE = {
    "cereal": (
        "Use locally recommended seed and sowing method; note seed lot, spacing plan, and field conditions.",
        "Check crop stand and weeds; manage water according to crop stage and local recommendations.",
        "Watch for booting, flowering, tasselling, or ear/panicle development as relevant; note stress and pest symptoms.",
        "Monitor grain development and field moisture; verify any nutrient or pest action with local guidance.",
        "Check grain maturity and local harvest-moisture advice; prepare clean drying and storage space.",
    ),
    "pulse": (
        "Use locally recommended seed and sowing method; record seed lot and field conditions.",
        "Check plant stand, weeds, and drainage; follow local guidance for any seed or nutrient treatment.",
        "Observe flowering and pod set; monitor moisture stress and insect or disease symptoms.",
        "Check pod development and crop health; consult local advisories before any crop-protection action.",
        "Check pod and plant maturity for the variety; harvest and dry under locally recommended conditions.",
    ),
    "fibre": (
        "Use a locally suitable variety and planting method; record the seed lot and planned spacing.",
        "Check plant stand, weeds, and early pest symptoms; follow local integrated pest-management guidance.",
        "Scout squares and flowers for damage; record pest counts and seek local advice before treatment.",
        "Monitor boll development and crop health; follow local thresholds and product labels for any action.",
        "Pick only mature, dry produce as locally recommended; keep harvested fibre clean and dry.",
    ),
    "oilseed": (
        "Use certified or locally recommended seed and sowing method; record the seed lot and field conditions.",
        "Check emergence, weeds, and drainage; compare growth with the local crop calendar.",
        "Observe flowering and pod/seed set; note moisture stress and pest or disease symptoms.",
        "Monitor pod or seed filling and crop health; base any input action on local recommendations.",
        "Check crop-specific maturity signs and harvest during suitable conditions; dry and store safely.",
    ),
    "vegetable": (
        "Prepare the nursery or planting bed as appropriate; record seed or planting-material source and date.",
        "Check establishment, weeds, support needs, and moisture; monitor plants for visible symptoms.",
        "Observe flowering, tuber formation, or fruit set as relevant; record stress and damage.",
        "Check produce size and quality; follow local advice for irrigation, support, and safe crop protection.",
        "Harvest at the crop's market-maturity stage; handle gently and move produce to suitable storage.",
    ),
    "sugarcane": (
        "Use healthy planting material and the locally recommended planting method; record the source and date.",
        "Check sprouting, gaps, weeds, and field moisture; seek local advice before gap filling.",
        "Monitor tillering and stalk growth; keep field notes on weeds, water, and visible pest symptoms.",
        "Check stalk development and crop health; follow local nutrient and irrigation schedules.",
        "Confirm harvest maturity with local guidance and the intended mill or buyer; prepare transport.",
    ),
    "rhizome": (
        "Use healthy planting rhizomes and locally recommended spacing; record source and planting date.",
        "Check sprouting, weeds, soil moisture, and drainage; follow local mulching or earthing-up guidance.",
        "Monitor canopy, rhizome development, and disease symptoms; avoid waterlogging.",
        "Check crop health and rhizome development; base any input decision on local recommendations.",
        "Confirm maturity with crop- and variety-specific signs; harvest and cure/store as locally advised.",
    ),
    "perennial": (
        "Record planting-material source, plant age, spacing, and field or orchard conditions.",
        "Inspect young plants, moisture, weeds, and support needs; follow the local orchard calendar.",
        "Monitor flowering and fruit set when in season; record pests, diseases, and weather impacts.",
        "Track fruit growth and orchard health; use local extension guidance for pruning and crop protection.",
        "Harvest in stages at locally recommended maturity; record yield, quality, and post-harvest handling.",
    ),
}


@lru_cache(maxsize=1)
def _crop_durations() -> Dict[str, int]:
    from app.agents.crop_recommendation_agent import CropRecommendationAgent

    return {
        name.casefold(): int(details["duration_days"])
        for name, details in CropRecommendationAgent().crop_database.items()
        if details.get("duration_days")
    }


def get_crop_name_options() -> List[str]:
    """Return crop names for which the project has indicative duration data."""
    return sorted(name.title() for name in _crop_durations())


def get_crop_duration_days(crop: str) -> Optional[int]:
    """Return the indicative reference duration for a known crop, if available."""
    crop_name = crop.strip().casefold()
    crop_name = _CROP_ALIASES.get(crop_name, crop_name)
    return _crop_durations().get(crop_name)


def build_daily_crop_schedule(
    crop: str,
    sowing_date: date,
    expected_harvest_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Build one non-prescriptive monitoring entry per day until expected harvest."""
    if expected_harvest_date:
        duration_days = (expected_harvest_date - sowing_date).days
        if duration_days <= 0:
            raise ValueError("Expected harvest must be after the sowing date.")
        duration_source = "farmer-entered expected harvest date"
    else:
        duration_days = get_crop_duration_days(crop)
        if duration_days is None:
            raise ValueError(
                "Add an expected harvest date for this crop; no duration is available in the reference."
            )
        duration_source = "indicative crop reference; verify for the selected variety and region"

    if duration_days > 3650:
        raise ValueError("The daily schedule cannot exceed ten years.")

    normalized_crop = crop.strip().casefold()
    normalized_crop = _CROP_ALIASES.get(normalized_crop, normalized_crop)
    guidance = _GROUP_GUIDANCE.get(_CROP_GROUPS.get(normalized_crop), _GENERAL_GUIDANCE)
    daily_schedule = []
    for day_after_sowing in range(duration_days + 1):
        progress = day_after_sowing / max(duration_days, 1)
        phase_index, phase = next(
            (index, item)
            for index, item in enumerate(_PHASES)
            if progress < item[0]
        )
        date_for_day = sowing_date + timedelta(days=day_after_sowing)
        if day_after_sowing == 0:
            weekly_check = "Record sowing date, crop and variety, seed or planting material, and field conditions."
        elif day_after_sowing == duration_days:
            weekly_check = "Record harvest date, yield, quality, moisture, storage, and sale details in the farm diary."
        elif day_after_sowing % 7 == 0:
            weekly_check = "Compare representative plants with last week's notes; record rainfall, irrigation, field work, and any symptoms."
        else:
            weekly_check = ""
        daily_schedule.append({
            "date": date_for_day.isoformat(),
            "day_after_sowing": day_after_sowing,
            "growth_stage": phase[1],
            "daily_check": (
                "Observe the crop and field; check for visible stress, pests, disease symptoms, "
                "standing water, and soil moisture. Record what you observe."
            ),
            "stage_guidance": guidance[phase_index],
            "weekly_or_milestone_task": weekly_check,
        })

    return {
        "crop": crop.strip(),
        "sowing_date": sowing_date.isoformat(),
        "expected_harvest_date": (sowing_date + timedelta(days=duration_days)).isoformat(),
        "duration_days": duration_days,
        "duration_source": duration_source,
        "daily_schedule": daily_schedule,
        "caveat": (
            "This is a general monitoring calendar, not a crop-specific prescription. "
            "Growth stages and harvest timing vary by variety, state, weather, and field conditions. "
            "Confirm operations and input decisions with local agricultural extension advice."
        ),
    }
