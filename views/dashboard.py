"""Dashboard: your numbers, your recent activity and what is closing next."""
import streamlit as st

from core import auctions, auth, stats, ui
from core.utils import format_inr, format_local, now_utc, parse_iso

user = auth.require_login()
first = user["full_name"].split()[0]
ui.page_header(
    f"Welcome back, {first}",
    "Your auctions, your bids and what is closing next.",
    "banner_dashboard.jpg",
)

if user["role"] == "admin":
    n = stats.platform()
    cols = st.columns(4)
    cols[0].metric("Live auctions", n["live"])
    cols[1].metric("Bids placed", n["bids"])
    cols[2].metric("Members", n["members"])
    cols[3].metric("Payments to confirm", n["to_confirm"])
    if st.button("Open the admin panel", type="primary", icon=":material/admin_panel_settings:"):
        st.switch_page("views/admin_panel.py")
else:
    n = stats.for_user(user["id"])
    row1 = st.columns(4)
    row1[0].metric("Bids placed", n["total_bids"])
    row1[1].metric("Items listed", n["total_listed"])
    row1[2].metric("Leading right now", n["leading"])
    row1[3].metric("Auctions won", n["won"])
    row2 = st.columns(4)
    row2[0].metric("My live listings", n["my_live"])
    row2[1].metric("Auctions I am bidding on", n["bidding_on"])
    row2[2].metric("Payments due", n["to_pay"])

    st.write("")
    ui.quick_nav("views/dashboard.py")

    left, right = st.columns(2, gap="large")
    with left:
        ui.section_title("Your latest bids")
        bids = stats.recent_bids(user["id"])
        if bids:
            st.dataframe(
                [{"Item": b["title"], "Your bid": format_inr(b["amount"]), "Placed": format_local(b["created_at"])} for b in bids],
                hide_index=True, width="stretch",
            )
        else:
            st.write("You have not placed a bid yet.")
    with right:
        ui.section_title("Your latest listings")
        listings = stats.recent_listings(user["id"])

        def state(a):
            if a["status"] == "cancelled":
                return "Cancelled"
            if a["status"] == "active" and parse_iso(a["end_time"]) > now_utc():
                return "Live"
            return "Sold" if a["winner_id"] else "Ended"

        if listings:
            st.dataframe(
                [{"Item": a["title"], "Price": format_inr(a["current_price"]), "Bids": a["bid_count"], "Status": state(a)} for a in listings],
                hide_index=True, width="stretch",
            )
        else:
            st.write("You have not listed anything yet.")

ui.section_title("Closing soon")
soon = auctions.list_auctions(sort="Ending soonest", live=True, limit=3)
if not soon:
    st.write("There are no live auctions right now.")
else:
    for col, auction in zip(st.columns(3, gap="medium"), soon):
        with col:
            ui.auction_card(auction, key_prefix="dash")
