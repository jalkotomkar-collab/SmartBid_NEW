"""Shared look and feel. All styling is injected from Python (no .css files).

Palette: teal (primary), indigo (bids and highlights), amber (time and warnings),
green (success), rose (problems), on a soft teal-tinted light background.
"""
from html import escape

import streamlit as st

from . import auth, images
from .config import APP_NAME, APP_TAGLINE, BASE_DIR, PLACEHOLDER_DIR

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700&family=Public+Sans:wght@400;500;600&display=swap');

:root {
  --bg: #F2F7F7;
  --tint: #E3F0EE;
  --surface: #FFFFFF;
  --line: #D3E2E0;
  --ink: #12262B;
  --muted: #4A6363;
  --teal: #0F766E;
  --teal-dark: #0B5753;
  --teal-soft: #D6F0EC;
  --indigo: #4338CA;
  --indigo-soft: #E4E3FB;
  --amber: #D97706;
  --amber-dark: #8A5204;
  --amber-soft: #FDEBC8;
  --green: #146C36;
  --green-soft: #DCF3E3;
  --rose: #BE123C;
  --rose-soft: #FDE3E8;
  --grad: linear-gradient(115deg, #0F766E 0%, #0E5E6F 55%, #3730A3 125%);
  --radius: 16px;
  --shadow: 0 6px 20px rgba(15, 80, 75, .10);
  --head: 'Bricolage Grotesque', 'Segoe UI', system-ui, sans-serif;
  --body: 'Public Sans', 'Segoe UI', system-ui, sans-serif;
}

html, body, .stApp { font-family: var(--body); color: var(--ink); }
.stApp { background: linear-gradient(180deg, #D9ECE9 0%, #F2F7F7 420px) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main { background: transparent !important; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }
h1, h2, h3, h4 { font-family: var(--head); color: var(--ink); letter-spacing: -0.01em; font-weight: 700; }
p, li, label, .stMarkdown { line-height: 1.6; }
a { color: var(--teal); }
:focus-visible { outline: 3px solid rgba(15, 118, 110, .45); outline-offset: 2px; }
footer, #MainMenu { visibility: hidden; }

/* Top bar */
[data-testid="stHeader"] { background: rgba(255, 255, 255, .94); border-bottom: 3px solid var(--teal); backdrop-filter: blur(6px); }

/* Sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #E6F3F1 0%, #CFE8E4 100%); border-right: 1px solid var(--line); }
[data-testid="stSidebarNav"]::before {
  content: "__APP_NAME__"; display: block; font-family: var(--head); font-weight: 700;
  font-size: 1.7rem; color: var(--teal-dark); padding: 1.2rem 1.1rem .5rem; letter-spacing: -0.02em;
}
[data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--teal) !important; border-radius: 10px; }
[data-testid="stSidebarNavLink"][aria-current="page"] * { color: #FFFFFF !important; }
.nl-user { background: var(--surface); border: 1px solid var(--line); border-left: 5px solid var(--indigo); border-radius: 12px; padding: .7rem .85rem; margin-bottom: .6rem; }
.nl-user-name { font-weight: 600; }
.nl-user-meta { color: var(--muted); font-size: .875rem; margin-top: 2px; }

/* Buttons */
button[data-testid^="stBaseButton-secondary"], button[kind^="secondary"],
[data-testid="stBaseLinkButton-secondary"] {
  background: var(--surface); color: var(--teal-dark); border: 1.5px solid #8CCBC3; border-radius: 11px;
  font-weight: 600; padding: .5rem 1.1rem; transition: background-color .15s ease, border-color .15s ease, transform .15s ease;
}
button[data-testid^="stBaseButton-secondary"]:hover, button[kind^="secondary"]:hover {
  background: var(--teal-soft); border-color: var(--teal); color: var(--teal-dark);
}
button[data-testid^="stBaseButton-primary"], button[kind^="primary"] {
  background: linear-gradient(135deg, #0F766E 0%, #0B5753 100%); color: #FFFFFF; border: none; border-radius: 11px;
  font-weight: 600; padding: .55rem 1.2rem; box-shadow: 0 6px 14px rgba(15, 118, 110, .28);
  transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
}
button[data-testid^="stBaseButton-primary"]:hover, button[kind^="primary"]:hover {
  filter: brightness(1.08); transform: translateY(-1px); box-shadow: 0 9px 18px rgba(15, 118, 110, .34); color: #FFFFFF;
}
button[data-testid^="stBaseButton"] p { color: inherit; }

/* Forms, inputs, tabs, tables */
[data-testid="stForm"] { background: var(--surface); border: 1px solid var(--line); border-top: 5px solid var(--teal); border-radius: var(--radius); padding: 1.4rem 1.4rem 1.2rem; box-shadow: var(--shadow); }
[data-testid="stImage"] img { border-radius: 16px; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stExpander"] { background: var(--surface); border-radius: 12px; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--line); }
button[role="tab"] { font-weight: 600; color: var(--muted); }
button[role="tab"][aria-selected="true"] { color: var(--teal-dark); }
[data-testid="stCaptionContainer"] { color: var(--muted); }

/* Metric cards: each column gets its own accent colour */
[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--teal);
  border-radius: var(--radius); padding: 1rem 1.15rem; box-shadow: var(--shadow);
}
[data-testid="stColumn"]:nth-child(4n+2) [data-testid="stMetric"] { border-left-color: var(--indigo); }
[data-testid="stColumn"]:nth-child(4n+3) [data-testid="stMetric"] { border-left-color: var(--amber); }
[data-testid="stColumn"]:nth-child(4n+4) [data-testid="stMetric"] { border-left-color: var(--green); }
[data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
[data-testid="stMetricValue"] { font-family: var(--head); font-weight: 700; color: var(--teal-dark); }

/* Page banner */
.nl-banner {
  display: flex; align-items: stretch; justify-content: space-between; overflow: hidden;
  background: var(--grad); border-radius: 20px; margin-bottom: 1.6rem; box-shadow: var(--shadow);
}
.nl-banner-text { padding: 1.7rem 2rem; align-self: center; max-width: 640px; }
.nl-banner-text h1 { font-size: 2rem; margin: 0 0 .35rem; padding: 0; color: #FFFFFF; }
.nl-banner-text p { color: rgba(255, 255, 255, .9); margin: 0; }
.nl-banner img {
  width: 38%; min-height: 150px; object-fit: cover; display: block; border-radius: 0;
  -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 30%); mask-image: linear-gradient(to right, transparent 0%, #000 30%);
}

/* Home hero */
.st-key-hero { background: var(--grad); border-radius: 24px; padding: 2.2rem 2.4rem; box-shadow: var(--shadow); }
.st-key-hero .nl-hero-title { color: #FFFFFF; }
.st-key-hero .nl-lead { color: rgba(255, 255, 255, .9); }
.st-key-hero button[data-testid^="stBaseButton-primary"], .st-key-hero button[kind^="primary"] {
  background: #F59E0B; color: #1B1B1B; box-shadow: 0 6px 14px rgba(0, 0, 0, .22);
}
.st-key-hero button[data-testid^="stBaseButton-secondary"], .st-key-hero button[kind^="secondary"] {
  background: rgba(255, 255, 255, .14); color: #FFFFFF; border: 1.5px solid rgba(255, 255, 255, .7);
}
.st-key-hero button[data-testid^="stBaseButton-secondary"]:hover, .st-key-hero button[kind^="secondary"]:hover { background: rgba(255, 255, 255, .26); color: #FFFFFF; }
.nl-hero-title { font-family: var(--head); font-weight: 700; font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.06; letter-spacing: -0.025em; margin: 0 0 1rem; }
.nl-lead { color: var(--muted); font-size: 1.1rem; max-width: 34rem; margin-bottom: 1.4rem; }
.nl-section { font-family: var(--head); font-size: 1.45rem; font-weight: 700; margin: 2.4rem 0 1rem; padding-left: .8rem; border-left: 6px solid var(--amber); color: var(--ink); }

/* Forms headings */
.nl-form-title { font-family: var(--head); font-size: 1.85rem; font-weight: 700; margin: .4rem 0 .2rem; color: var(--teal-dark); }
.nl-form-sub { color: var(--muted); margin-bottom: 1.1rem; }

/* Pills */
.nl-pill { display: inline-block; padding: 2px 11px; border-radius: 999px; font-size: .78rem; font-weight: 600; background: var(--teal-soft); color: var(--teal-dark); }
.nl-pill.amber { background: var(--amber-soft); color: var(--amber-dark); }
.nl-pill.red { background: var(--rose-soft); color: var(--rose); }
.nl-pill.green { background: var(--green-soft); color: var(--green); }
.nl-pill.indigo { background: var(--indigo-soft); color: var(--indigo); }
.nl-pill.grey { background: #E7ECEC; color: var(--muted); }
.nl-muted { color: var(--muted); }

/* Auction cards and list rows (styled through container keys) */
[class*="st-key-card_"] {
  background: var(--surface); border: 1px solid var(--line); border-top: 5px solid var(--teal);
  border-radius: var(--radius); padding: 12px 12px 14px; box-shadow: var(--shadow);
  transition: transform .18s ease, box-shadow .18s ease;
}
[class*="st-key-card_"]:hover { transform: translateY(-3px); box-shadow: 0 12px 26px rgba(15, 80, 75, .18); }
[class*="st-key-row_"] {
  background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--indigo);
  border-radius: var(--radius); padding: 14px 16px; box-shadow: var(--shadow); margin-bottom: .4rem;
}
.nl-card-cat { color: var(--indigo); font-size: .85rem; font-weight: 600; margin-top: .35rem; }
.nl-card-title { font-family: var(--head); font-weight: 600; font-size: 1.12rem; line-height: 1.25; margin: .1rem 0 .7rem; min-height: 2.8rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.nl-card-row { display: flex; justify-content: space-between; align-items: flex-end; gap: .75rem; margin-bottom: .75rem; }
.nl-card-right { text-align: right; font-size: .85rem; line-height: 1.6; }
.nl-price-label { color: var(--muted); font-size: .82rem; }
.nl-price { font-family: var(--head); font-weight: 700; font-size: 1.4rem; letter-spacing: -0.01em; color: var(--teal-dark); }
.nl-row-title { font-family: var(--head); font-weight: 600; font-size: 1.12rem; line-height: 1.25; margin-bottom: .2rem; }
.nl-row-meta { color: var(--muted); font-size: .9rem; line-height: 1.6; }
.nl-row-price { font-family: var(--head); font-weight: 700; font-size: 1.2rem; color: var(--teal-dark); }

/* Auction details */
.nl-detail-tags { display: flex; gap: .5rem; flex-wrap: wrap; margin-bottom: .4rem; }
.nl-detail-title { font-family: var(--head); font-weight: 700; font-size: clamp(1.7rem, 3.2vw, 2.4rem); line-height: 1.12; letter-spacing: -0.02em; margin: .3rem 0 .6rem; }
.nl-panel { background: linear-gradient(135deg, #FFFFFF 0%, #E6F5F2 100%); border: 1px solid var(--line); border-left: 7px solid var(--teal); border-radius: var(--radius); padding: 1.3rem 1.4rem; margin-bottom: 1rem; box-shadow: var(--shadow); }
.nl-big-price { font-family: var(--head); font-weight: 700; font-size: 2.6rem; line-height: 1.05; letter-spacing: -0.02em; color: var(--teal-dark); }
.nl-panel-row { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; flex-wrap: wrap; }
.nl-time { font-family: var(--head); font-weight: 600; font-size: 1.55rem; color: var(--indigo); }
.nl-time.urgent { color: var(--amber-dark); }
.nl-facts { width: 100%; border-collapse: collapse; margin-top: .4rem; background: var(--surface); border-radius: 12px; overflow: hidden; }
.nl-facts td { padding: .6rem .9rem; border-bottom: 1px solid var(--line); font-size: .95rem; }
.nl-facts td:first-child { color: var(--muted); width: 38%; background: #F0F7F6; }
.nl-result { border-radius: 12px; padding: .95rem 1.1rem; background: var(--green-soft); color: var(--green); font-weight: 600; }
.nl-result.muted { background: #E7ECEC; color: var(--muted); }
.nl-qr-frame { background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 1rem; text-align: center; }

/* Logged-out brand bar */
.nl-brandbar { display: flex; align-items: center; gap: .65rem; margin: 0 0 1.4rem; }
.nl-brandbar img { width: 36px; height: 36px; border-radius: 10px; }
.nl-brandname { font-family: var(--head); font-weight: 700; font-size: 1.55rem; letter-spacing: -0.02em; background: linear-gradient(90deg, #0F766E, #4338CA); -webkit-background-clip: text; background-clip: text; color: transparent; }
.nl-brandtag { color: var(--muted); font-size: .95rem; padding-left: .65rem; border-left: 2px solid var(--line); }

@media (max-width: 720px) {
  .nl-banner { flex-direction: column-reverse; }
  .nl-banner img { width: 100%; height: 130px; -webkit-mask-image: none; mask-image: none; }
  .nl-banner-text { padding: 1.2rem; }
  .st-key-hero { padding: 1.4rem 1.2rem; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""

HIDE_SIDEBAR = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] { display: none !important; }
</style>
"""


def inject_css(hide_sidebar: bool = False) -> None:
    st.markdown(CSS.replace("__APP_NAME__", escape(APP_NAME)), unsafe_allow_html=True)
    if hide_sidebar:
        st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)


def brand_bar() -> None:
    """Logo and name shown at the top of every logged-out page."""
    st.markdown(
        f'<div class="nl-brandbar"><img src="{images.data_uri("favicon.png")}" alt="">'
        f'<span class="nl-brandname">{escape(APP_NAME)}</span>'
        f'<span class="nl-brandtag">{escape(APP_TAGLINE)}</span></div>',
        unsafe_allow_html=True,
    )


def page_exists(path: str) -> bool:
    return (BASE_DIR / path).exists()


def page_header(title: str, subtitle: str, banner: str) -> None:
    """Top-of-page banner: text on the left, a relevant illustration on the right."""
    st.markdown(
        f'<div class="nl-banner"><div class="nl-banner-text"><h1>{escape(title)}</h1>'
        f"<p>{escape(subtitle)}</p></div>"
        f'<img src="{images.data_uri(banner)}" alt=""></div>',
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f'<div class="nl-section">{escape(text)}</div>', unsafe_allow_html=True)


def form_heading(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="nl-form-title">{escape(title)}</div><div class="nl-form-sub">{escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def auth_layout(image_name: str):
    """Two-column layout for Login / Register / Admin Login. Returns the form column."""
    left, right = st.columns([1, 1.05], gap="large")
    with left:
        st.image(str(PLACEHOLDER_DIR / image_name), width="stretch")
    return right


def sidebar_account(user) -> None:
    """Account block in the sidebar. Logged-out visitors get no sidebar at all."""
    if not user:
        return
    with st.sidebar:
        role = "Administrator" if user["role"] == "admin" else "Member"
        st.markdown(
            f'<div class="nl-user"><div class="nl-user-name">{escape(user["full_name"])}</div>'
            f'<div class="nl-user-meta">@{escape(user["username"])} '
            f'{pill(role, tone="amber" if user["role"] == "admin" else "indigo")}</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            auth.logout()
            st.rerun()


def pill(text: str, amber: bool = False, tone: str | None = None) -> str:
    """A small coloured label. tone: teal (default), amber, red, green, indigo, grey."""
    tone = tone or ("amber" if amber else "teal")
    return f'<span class="nl-pill {tone}">{escape(text)}</span>'


# ------------------------------------------------------------------ navigation
def nav_button(label, path, icon=None, key=None, primary=False, stretch=False, before=None) -> None:
    """A real button (the whole button is clickable) that opens another page."""
    clicked = st.button(
        label,
        key=key or f"nav_{path}_{label}",
        icon=icon,
        type="primary" if primary else "secondary",
        width="stretch" if stretch else "content",
    )
    if clicked:
        if before:
            before()
        st.switch_page(path)


def quick_nav(current: str) -> None:
    """A row of buttons to the other main pages, so nobody has to use the sidebar."""
    user = auth.current_user()
    if not user:
        return
    if user["role"] == "admin":
        items = [
            ("views/admin_panel.py", "Admin Panel", ":material/admin_panel_settings:"),
            ("views/dashboard.py", "Dashboard", ":material/dashboard:"),
            ("views/browse.py", "Browse Auctions", ":material/storefront:"),
        ]
    else:
        items = [
            ("views/dashboard.py", "Dashboard", ":material/dashboard:"),
            ("views/browse.py", "Browse Auctions", ":material/storefront:"),
            ("views/sell.py", "Sell Product", ":material/sell:"),
            ("views/my_auctions.py", "My Auctions", ":material/inventory_2:"),
            ("views/my_bids.py", "My Bids", ":material/receipt_long:"),
            ("views/payment.py", "Payment", ":material/payments:"),
        ]
    items = [i for i in items if i[0] != current and page_exists(i[0])]
    for col, (path, label, icon) in zip(st.columns(len(items)), items):
        with col:
            if st.button(label, key=f"qn_{current}_{path}", icon=icon, width="stretch"):
                st.switch_page(path)


def open_auction(auction_id: int) -> None:
    """Remember which auction to show, then go to its detail page."""
    st.session_state["selected_auction_id"] = int(auction_id)
    st.query_params["auction"] = str(int(auction_id))
    st.switch_page("views/auction_details.py")


def auction_card(a: dict, key_prefix: str = "card") -> None:
    """One auction as a card: photo, title, price, time left and a button to open it."""
    from .auctions import is_live
    from .utils import format_inr, now_utc, parse_iso, time_left_text

    live = is_live(a)
    if live:
        label = "Current bid" if a["bid_count"] else "Starting price"
        remaining = (parse_iso(a["end_time"]) - now_utc()).total_seconds()
        badge = pill(time_left_text(a["end_time"]), tone="amber" if remaining < 3600 else "indigo")
    else:
        label = "Sold for" if a.get("winner_id") else ("Closed at" if a["bid_count"] else "Starting price")
        badge = pill("Sold", tone="green") if a.get("winner_id") else pill("Closed", tone="grey")
    bids = f'{a["bid_count"]} bid{"" if a["bid_count"] == 1 else "s"}'

    with st.container(key=f"card_{key_prefix}_{a['id']}"):
        st.image(images.product_image(a["image_id"]), width="stretch")
        st.markdown(
            f'<div class="nl-card-cat">{escape(a.get("category_name") or "General")}</div>'
            f'<div class="nl-card-title">{escape(a["title"])}</div>'
            f'<div class="nl-card-row"><div><div class="nl-price-label">{label}</div>'
            f'<div class="nl-price">{format_inr(a["current_price"])}</div></div>'
            f'<div class="nl-card-right">{badge}<div class="nl-muted">{bids}</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("View auction", key=f"{key_prefix}_open_{a['id']}", type="primary", icon=":material/gavel:", width="stretch"):
            open_auction(a["id"])
