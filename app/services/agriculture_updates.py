"""Daily, general-purpose farm reminders and official information sources."""
from datetime import date
from typing import Any, Dict, Optional


_DAILY_CHECKLISTS = (
    ("Scout crops", "Check several plants in each field for new spots, wilting, or insect damage; note where symptoms begin."),
    ("Check the forecast", "Review your local weather advisory before irrigation, spraying, or field work."),
    ("Check soil moisture", "Inspect the root zone before watering and account for recent rainfall and the crop's growth stage."),
    ("Review field records", "Record today's labour, input use, harvest, and expenses while the details are fresh."),
    ("Inspect water flow", "Look for blocked channels, leaks, and standing water, especially after rain."),
    ("Check stored produce", "Look for moisture, pests, and damaged packaging in stored grain or produce."),
    ("Review input labels", "Before using any farm input, check its label, crop approval, dose, protective equipment, and waiting period."),
)

_SEASONAL_FOCUSES = {
    1: "Cool-season crops: check local advisories for frost or cold stress before taking protective action.",
    2: "Changing temperatures: inspect crop water needs and field conditions rather than relying on a fixed schedule.",
    3: "Warmer days: monitor soil moisture and crop stress; follow local water guidance.",
    4: "Hot-weather period: check crops during the day for heat stress and plan water use around local conditions.",
    5: "Pre-monsoon period: clear drainage routes and check local forecasts before field operations.",
    6: "Monsoon period: monitor drainage and avoid field operations when soil is waterlogged.",
    7: "Rainy period: scout for crop damage after heavy rain and use local advisories before spraying.",
    8: "Rainy period: check field drainage and inspect crops after storms.",
    9: "Season transition: review local sowing advisories and prepare fields only when conditions are suitable.",
    10: "Harvest period in many regions: check crop maturity and local weather before harvest and storage.",
    11: "Cool-season sowing in many regions: use state and district crop calendars for timing and varieties.",
    12: "Cool-season crops: monitor moisture and check local advisories for cold-weather risks.",
}

_OFFICIAL_SOURCES = (
    {
        "name": "India Meteorological Department",
        "url": "https://mausam.imd.gov.in/",
    },
    {
        "name": "e-NAM market information",
        "url": "https://www.enam.gov.in/web/",
    },
    {
        "name": "myScheme government scheme finder",
        "url": "https://www.myscheme.gov.in/",
    },
)


def get_daily_agriculture_update(today: Optional[date] = None) -> Dict[str, Any]:
    """Return a date-keyed farm checklist, seasonal reminder, and official sources."""
    current_date = today or date.today()
    checklist = _DAILY_CHECKLISTS[current_date.toordinal() % len(_DAILY_CHECKLISTS)]
    return {
        "date": current_date.isoformat(),
        "checklist_title": checklist[0],
        "checklist": checklist[1],
        "seasonal_focus": _SEASONAL_FOCUSES[current_date.month],
        "official_sources": [dict(source) for source in _OFFICIAL_SOURCES],
        "is_live_news": False,
    }
