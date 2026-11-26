from __future__ import annotations

from pathlib import Path

# Base paths
BASE_DIR: Path = Path(__file__).resolve().parent
DATABASE_DIR: Path = BASE_DIR / "database"
MODELS_DIR: Path = BASE_DIR / "models"
ASSETS_DIR: Path = BASE_DIR / "assets"
TRAINING_DIR: Path = BASE_DIR / "training"

# Data files
FOOD_NUTRITION_CSV: Path = DATABASE_DIR / "food_nutrition.csv"
PORTION_REFERENCE_CSV: Path = DATABASE_DIR / "portion_reference.csv"
MEAL_HISTORY_CSV: Path = DATABASE_DIR / "meal_history.csv"
CUSTOM_CSS_PATH: Path = ASSETS_DIR / "styles.css"

# Model weight paths (priority order: custom fine-tuned -> base pretrained)
CUSTOM_MODEL_PATH: Path = MODELS_DIR / "nutriscan_food_yolo.pt"
BASE_MODEL_PATH: Path = MODELS_DIR / "yolo11n.pt"
FALLBACK_BASE_MODEL_NAME: str = "yolo11n.pt"

# Detection settings
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.35
DEFAULT_IOU_THRESHOLD: float = 0.45
INFERENCE_IMAGE_SIZE: int = 640
UNCERTAIN_LABEL: str = "Uncertain Food Item"

# WebRTC STUN configuration for browser camera streaming
RTC_CONFIGURATION: dict = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
    ]
}

# Mobile-first camera constraints:
# "ideal": "environment" selects the rear camera on mobile devices
# while gracefully falling back to the default webcam on desktops/laptops.
MEDIA_STREAM_CONSTRAINTS: dict = {
    "video": {
        "facingMode": {"ideal": "environment"},
        "width": {"ideal": 1280},
        "height": {"ideal": 720},
    },
    "audio": False,
}

# Supported portion units
PORTION_UNITS: list[str] = [
    "Grams (g)",
    "Pieces",
    "Cups",
    "Katoris",
    "Millilitres (ml)",
    "Servings",
]

UNIT_KEY_MAP: dict[str, str] = {
    "Grams (g)": "grams",
    "Pieces": "piece",
    "Cups": "cup",
    "Katoris": "katori",
    "Millilitres (ml)": "ml",
    "Servings": "serving",
}

# Canonical 40 food classes supported by NutriScan AI
CANONICAL_FOOD_CLASSES: list[str] = [
    # Indian Foods (20)
    "Roti / Chapati",
    "Rice",
    "Dal",
    "Paneer",
    "Sabzi",
    "Idli",
    "Dosa",
    "Poha",
    "Chole",
    "Samosa",
    "Biryani",
    "Paratha",
    "Puri",
    "Rajma",
    "Khichdi",
    "Upma",
    "Dhokla",
    "Uttapam",
    "Pakora",
    "Aloo Gobi",
    # International Foods (20)
    "Apple",
    "Banana",
    "Orange",
    "Egg",
    "Grilled chicken",
    "Fish",
    "Burger",
    "Pizza",
    "French fries",
    "Sandwich",
    "Salad",
    "Oatmeal",
    "Yogurt",
    "Pasta",
    "Pancakes",
    "Bread",
    "Rice bowl",
    "Soup",
    "Cake",
    "Cookies",
]

# Honest mapping from COCO pretrained labels to NutriScan canonical classes.
# Generic containers (bowl, cup) or non-exact items are flagged as uncertain
# rather than inventing a dish label.
COCO_DIRECT_FOOD_MAP: dict[str, str] = {
    "apple": "Apple",
    "banana": "Banana",
    "orange": "Orange",
    "pizza": "Pizza",
    "sandwich": "Sandwich",
    "cake": "Cake",
}

COCO_UNCERTAIN_FOOD_HINTS: set[str] = {
    "bowl",
    "cup",
    "broccoli",
    "carrot",
    "hot dog",
    "donut",
    "wine glass",
    "fork",
    "knife",
    "spoon",
    "dining table",
}

# Product metadata
APP_NAME: str = "NutriScan AI"
APP_TAGLINE: str = "Real-Time Camera Food Recognition & Nutritional Intelligence"
APP_VERSION: str = "1.0.0"
