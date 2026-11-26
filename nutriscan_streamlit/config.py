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

# Food-group taxonomy used by NutriScan Meal Intelligence
FOOD_GROUP_CATALOG: list[str] = [
    "Grains & Staples",
    "Lentils & Legumes",
    "Vegetables & Greens",
    "Dairy & Paneer",
    "Eggs & Lean Proteins",
    "Fruits",
    "Fried & Indulgent Snacks",
]

FOOD_GROUP_MAP: dict[str, str] = {
    # Indian Foods
    "Roti / Chapati": "Grains & Staples",
    "Rice": "Grains & Staples",
    "Dal": "Lentils & Legumes",
    "Paneer": "Dairy & Paneer",
    "Sabzi": "Vegetables & Greens",
    "Idli": "Grains & Staples",
    "Dosa": "Grains & Staples",
    "Poha": "Grains & Staples",
    "Chole": "Lentils & Legumes",
    "Samosa": "Fried & Indulgent Snacks",
    "Biryani": "Grains & Staples",
    "Paratha": "Grains & Staples",
    "Puri": "Fried & Indulgent Snacks",
    "Rajma": "Lentils & Legumes",
    "Khichdi": "Grains & Staples",
    "Upma": "Grains & Staples",
    "Dhokla": "Lentils & Legumes",
    "Uttapam": "Grains & Staples",
    "Pakora": "Fried & Indulgent Snacks",
    "Aloo Gobi": "Vegetables & Greens",
    # International Foods
    "Apple": "Fruits",
    "Banana": "Fruits",
    "Orange": "Fruits",
    "Egg": "Eggs & Lean Proteins",
    "Grilled chicken": "Eggs & Lean Proteins",
    "Fish": "Eggs & Lean Proteins",
    "Burger": "Fried & Indulgent Snacks",
    "Pizza": "Grains & Staples",
    "French fries": "Fried & Indulgent Snacks",
    "Sandwich": "Grains & Staples",
    "Salad": "Vegetables & Greens",
    "Oatmeal": "Grains & Staples",
    "Yogurt": "Dairy & Paneer",
    "Pasta": "Grains & Staples",
    "Pancakes": "Grains & Staples",
    "Bread": "Grains & Staples",
    "Rice bowl": "Grains & Staples",
    "Soup": "Vegetables & Greens",
    "Cake": "Fried & Indulgent Snacks",
    "Cookies": "Fried & Indulgent Snacks",
}

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

# Botanical Soft-Green Brand Palette
BRAND_PALETTE: dict[str, str] = {
    "bg_primary": "#F3F7F0",
    "bg_secondary": "#E8F0E5",
    "card_bg": "#FFFFFF",
    "primary_green": "#527B60",
    "deep_forest": "#294C38",
    "muted_sage": "#A8BCA6",
    "soft_mint": "#DCEBDD",
    "accent_cream": "#F6F0E4",
    "text_primary": "#25352B",
    "text_secondary": "#758276",
    "border_soft": "#DCE4D9",
    "warm_ochre": "#B88446",
}

# Product metadata
APP_NAME: str = "NutriScan AI"
APP_TAGLINE: str = "Scan. Understand. Nourish."
APP_SUBTITLE: str = "What is on your plate, and what does it contain?"
APP_VERSION: str = "2.0.0"
