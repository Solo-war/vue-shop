from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent

# Static data (seed products)
DATA_FILE = ROOT / "static" / "products.json"

# SQLite file for orders/payments/reviews
DB_FILE = ROOT / "mock_payments.db"

# Auth / JWT
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Users DB (SQLAlchemy)
DATABASE_URL = "sqlite:///./users.db"

# Images locations
FRONT_TEE_IMAGES_DIR = (
    Path(__file__).resolve().parents[2]
    / "vibe-shop-front"
    / "public"
    / "images"
    / "tees"
    / "images"
)

BACK_IMAGES_ROOT = ROOT / "public" / "images"
BACK_TEE_IMAGES_DIR = BACK_IMAGES_ROOT / "tees" / "images"

# Geo
NOVOSIB = (55.0084, 82.9357)

