"""Names and locale tags for India's 22 constitutionally scheduled languages."""
from typing import Dict, List


INDIAN_LANGUAGES: List[Dict[str, str]] = [
    {"code": "as", "name": "Assamese", "native_name": "অসমীয়া"},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "brx", "name": "Bodo", "native_name": "बड़ो"},
    {"code": "doi", "name": "Dogri", "native_name": "डोगरी"},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "ks", "name": "Kashmiri", "native_name": "कॉशुर"},
    {"code": "kok", "name": "Konkani", "native_name": "कोंकणी"},
    {"code": "mai", "name": "Maithili", "native_name": "मैथिली"},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
    {"code": "mni", "name": "Manipuri (Meitei)", "native_name": "মেইতেই"},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
    {"code": "ne", "name": "Nepali", "native_name": "नेपाली"},
    {"code": "or", "name": "Odia", "native_name": "ଓଡ଼ିଆ"},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
    {"code": "sa", "name": "Sanskrit", "native_name": "संस्कृतम्"},
    {"code": "sat", "name": "Santali", "native_name": "ᱥᱟᱱᱛᱟᱲᱤ"},
    {"code": "sd", "name": "Sindhi", "native_name": "سنڌي"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "ur", "name": "Urdu", "native_name": "اردو"},
]
LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    **{item["code"]: item["name"] for item in INDIAN_LANGUAGES},
}
