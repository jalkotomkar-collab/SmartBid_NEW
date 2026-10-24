"""SmartBid - online auction app. Entry point: streamlit run app.py"""
import streamlit as st

from core.config import APP_NAME, PLACEHOLDER_DIR

st.set_page_config(
    page_title=APP_NAME,
    page_icon=str(PLACEHOLDER_DIR / "favicon.png"),
    layout="wide",
)

from core import auctions, auth, db, sample_data, ui  # noqa: E402  (after set_page_config)


@st.cache_resource(show_spinner="Starting up...")
def bootstrap():
    """Create tables, the first admin and the demo listings once per server process."""
    db.init_db()
    status = auth.ensure_admin()
    try:
        sample_data.seed_if_empty()
    except Exception:  # demo data is optional; never block startup on it
        pass
    return status


try:
    st.session_state["admin_status"] = bootstrap()
except Exception as exc:  # bad database credentials, network problem, etc.
    st.error("The database could not be opened. Check your database settings and try again.")
    st.caption(f"Details: {exc}")
    st.stop()

try:
    auctions.close_expired_throttled()
except Exception:
    pass

user = auth.current_user()
ui.inject_css(hide_sidebar=user is None)

# (file, title, material icon, shown in the menu?)
GUEST = [
    ("views/home.py", "Home", ":material/home:", True),
    ("views/browse.py", "Browse Auctions", ":material/storefront:", True),
    ("views/login.py", "Login", ":material/login:", True),
    ("views/register.py", "Register", ":material/person_add:", True),
    ("views/admin_login.py", "Admin Login", ":material/admin_panel_settings:", True),
    ("views/auction_details.py", "Auction Details", ":material/gavel:", False),
]
MEMBER = [
    ("views/dashboard.py", "Dashboard", ":material/dashboard:", True),
    ("views/home.py", "Home", ":material/home:", True),
    ("views/browse.py", "Browse Auctions", ":material/storefront:", True),
    ("views/sell.py", "Sell Product", ":material/sell:", True),
    ("views/my_auctions.py", "My Auctions", ":material/inventory_2:", True),
    ("views/my_bids.py", "My Bids", ":material/receipt_long:", True),
    ("views/payment.py", "Payment", ":material/payments:", True),
    ("views/account.py", "My Account", ":material/account_circle:", True),
    ("views/auction_details.py", "Auction Details", ":material/gavel:", False),
]
ADMIN = [
    ("views/admin_panel.py", "Admin Panel", ":material/admin_panel_settings:", True),
    ("views/dashboard.py", "Dashboard", ":material/dashboard:", True),
    ("views/home.py", "Home", ":material/home:", True),
    ("views/browse.py", "Browse Auctions", ":material/storefront:", True),
    ("views/account.py", "My Account", ":material/account_circle:", True),
    ("views/auction_details.py", "Auction Details", ":material/gavel:", False),
]

if not user:
    spec, landing = GUEST, "views/home.py"
elif user["role"] == "admin":
    spec, landing = ADMIN, "views/admin_panel.py"
else:
    spec, landing = MEMBER, "views/dashboard.py"

pages = [
    st.Page(
        path,
        title=title,
        icon=icon,
        default=(path == landing),
        visibility="visible" if shown else "hidden",
    )
    for path, title, icon, shown in spec
    if ui.page_exists(path)
]

# Logged-out visitors get a top menu and no sidebar; the sidebar appears after login.
nav = st.navigation(pages, position="sidebar" if user else "top")
if user:
    ui.sidebar_account(user)
else:
    ui.brand_bar()
nav.run()
