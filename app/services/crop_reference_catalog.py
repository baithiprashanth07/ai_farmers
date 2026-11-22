"""Indian crop seasons and broad crop-use classifications."""
from typing import Any, Dict, List


_SEASONS = (
    {
        "name": "Kharif",
        "description": "Monsoon-season crops are commonly sown around June–July and harvested from autumn onward; local rainfall and crop duration change these windows.",
        "examples": "Rice, maize, cotton, jowar, bajra, tur, moong, urad, groundnut, and soybean",
    },
    {
        "name": "Rabi",
        "description": "Winter crops are commonly sown from October–December and harvested from spring into early summer, depending on the crop and region.",
        "examples": "Wheat, barley, chickpea (gram), peas, mustard, and linseed",
    },
    {
        "name": "Zaid",
        "description": "Short-duration summer crops are commonly grown between Rabi and Kharif, often where irrigation is available.",
        "examples": "Watermelon, muskmelon, cucumber, bitter gourd, pumpkin, and fodder crops",
    },
)

_CATEGORIES = (
    {
        "name": "Food grains and pulses",
        "purpose": "Staple foods and protein-rich pulses",
        "examples": "Rice, wheat, maize, jowar, bajra, ragi, chana, tur, moong, urad, and masoor",
    },
    {
        "name": "Commercial and fibre crops",
        "purpose": "Crops grown for sale or industrial processing",
        "examples": "Cotton, sugarcane, jute, and tobacco",
    },
    {
        "name": "Oilseeds",
        "purpose": "Edible and industrial oil production",
        "examples": "Groundnut, mustard, soybean, sunflower, sesame (til), and castor",
    },
    {
        "name": "Plantation crops",
        "purpose": "Long-duration crops often grown in tropical or hill regions",
        "examples": "Tea, coffee, rubber, coconut, and arecanut",
    },
    {
        "name": "Horticulture",
        "purpose": "Fruits, vegetables, flowers, and other high-value crops",
        "examples": "Mango, banana, citrus, pomegranate, potato, onion, tomato, and flowers",
    },
    {
        "name": "Spices and condiments",
        "purpose": "Crops grown for flavour, processing, and trade",
        "examples": "Pepper, cardamom, turmeric, chilli, ginger, and coriander",
    },
    {
        "name": "Fodder crops",
        "purpose": "Green or dry feed for livestock",
        "examples": "Fodder sorghum, maize, berseem, oats, and Napier grass",
    },
    {
        "name": "Medicinal and aromatic crops",
        "purpose": "Plants cultivated for medicinal, fragrance, or processing uses",
        "examples": "Aloe vera, lemongrass, ashwagandha, and mint",
    },
)


def get_crop_seasons() -> List[Dict[str, Any]]:
    """Return broad Indian crop seasons and indicative examples."""
    return [dict(season) for season in _SEASONS]


def get_crop_categories() -> List[Dict[str, Any]]:
    """Return broad crop-use categories; crops may belong to more than one."""
    return [dict(category) for category in _CATEGORIES]
