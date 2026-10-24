"""Home: a short welcome. After login it shows your own bids and listings."""
from html import escape

import streamlit as st

from core import auth, stats, ui
from core.config import APP_NAME, PLACEHOLDER_DIR

user = auth.current_user()

with st.container(key="hero"):
    left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")

    with left:
        if user:
            title = f"Welcome back, {escape(user['full_name'].split()[0])}."
            lead = "Here is where you stand. Open the dashboard for the full picture."
        else:
            title = "Buy and sell through live auctions."
            lead = (
                f"{escape(APP_NAME)} lets you list an item in minutes, set a starting price and a "
                "minimum bid step, and let buyers compete until the clock runs out."
            )
        st.markdown(
            f'<div class="nl-hero-title">{title}</div><div class="nl-lead">{lead}</div>',
            unsafe_allow_html=True,
        )

        if not user:
            c1, c2, c3 = st.columns(3)
            if c1.button("Create account", type="primary", icon=":material/person_add:", width="stretch"):
                st.switch_page("views/register.py")
            if c2.button("Log in", icon=":material/login:", width="stretch"):
                st.switch_page("views/login.py")
            if c3.button("Admin login", icon=":material/admin_panel_settings:", width="stretch"):
                st.switch_page("views/admin_login.py")
        else:
            targets = (
                [("views/admin_panel.py", "Admin panel", ":material/admin_panel_settings:"),
                 ("views/dashboard.py", "Dashboard", ":material/dashboard:")]
                if user["role"] == "admin"
                else [("views/dashboard.py", "Dashboard", ":material/dashboard:"),
                      ("views/browse.py", "Browse auctions", ":material/storefront:"),
                      ("views/sell.py", "Sell a product", ":material/sell:")]
            )
            for i, (col, (path, label, icon)) in enumerate(zip(st.columns(len(targets)), targets)):
                if col.button(label, key=f"home_go_{i}", icon=icon, width="stretch", type="primary" if i == 0 else "secondary"):
                    st.switch_page(path)

    with right:
        st.image(str(PLACEHOLDER_DIR / "hero_home.jpg"), width="stretch")

# ---- your own status (members only)
if user and user["role"] == "user":
    n = stats.for_user(user["id"])
    ui.section_title("Your activity")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.metric("Bids placed", n["total_bids"])
        st.caption(f"Bidding on {n['bidding_on']} live auction{'' if n['bidding_on'] == 1 else 's'}, leading in {n['leading']}.")
        if st.button("View my bids", key="home_my_bids", icon=":material/receipt_long:", width="stretch"):
            st.switch_page("views/my_bids.py")
    with c2:
        st.metric("Items listed", n["total_listed"])
        st.caption(f"{n['my_live']} live right now.")
        if st.button("View my listings", key="home_my_listings", icon=":material/inventory_2:", width="stretch"):
            st.switch_page("views/my_auctions.py")
