"""Central settings: branding, currency, paths and secrets access."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
PLACEHOLDER_DIR = ASSETS_DIR / "placeholders"
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "auction.db"

APP_NAME = "SmartBid"
APP_TAGLINE = "Live online auctions"

# All prices are stored as integer paise and shown in rupees.
CURRENCY_SYMBOL = "\u20b9"
DISPLAY_TIMEZONE = "Asia/Kolkata"

# Sample auctions are created once on first run so the app is not empty.
# Turn off with SEED_SAMPLE_DATA=false in secrets or the environment.
SEED_SAMPLE_DATA_DEFAULT = "true"

MAX_PRICE_RUPEES = 10_000_000  # sanity cap on any price or bid

# Local development admin, used ONLY when no admin secrets are set and the app
# is running on a local SQLite file (never when a hosted database is configured).
DEV_ADMIN_USERNAME = "admin"
DEV_ADMIN_PASSWORD = "Admin@12345"
DEV_ADMIN_EMAIL = "admin@localhost"


def get_secret(name, default=None):
    """Read a value from the environment first, then from Streamlit secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return default
