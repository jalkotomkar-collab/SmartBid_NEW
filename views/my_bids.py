"""My Bids: every auction you have bid on and where you stand."""
from html import escape

import streamlit as st

from core import auctions, auth, images, ui
from core.utils import format_inr, format_local, time_left_text

user = auth.require_login()
if user["role"] == "admin":
    st.info("Administrator accounts cannot bid. Use a member account to see bids.")
    st.stop()

ui.page_header("My bids", "Auctions you are bidding on, the ones you won, and what you still owe.", "banner_my_bids.jpg")
ui.quick_nav("views/my_bids.py")

items = auctions.user_bids(user["id"])
active = [a for a in items if a["standing"] in ("Leading", "Outbid")]
won = [a for a in items if a["standing"] == "Won"]
closed = [a for a in items if a["standing"] in ("Lost", "Cancelled")]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Active bids", len(active))
m2.metric("Leading", sum(1 for a in active if a["standing"] == "Leading"))
m3.metric("Won", len(won))
m4.metric("Payments due", sum(1 for a in won if a["payment_status"] == "pending"))

PILL = {"Leading": ("Leading", "green"), "Outbid": ("Outbid", "amber"), "Won": ("Won", "indigo"), "Lost": ("Lost", "grey"), "Cancelled": ("Cancelled", "grey")}
PAY_TONE = {"pending": "amber", "submitted": "indigo", "confirmed": "green"}
PAY = {"pending": "Payment due", "submitted": "Payment sent", "confirmed": "Payment confirmed"}


def row(a):
    label, tone = PILL[a["standing"]]
    with st.container(key=f"row_myb_{a['id']}"):
        c_img, c_main, c_side = st.columns([1.1, 3, 1.7], vertical_alignment="center")
        c_img.image(images.product_image(a["image_id"]), width="stretch")
        with c_main:
            st.markdown(
                f'<div class="nl-row-title">{escape(a["title"])}</div>'
                f'<div class="nl-row-meta">Your best bid {format_inr(a["my_best"])}<br>'
                f'{"Current price" if auctions.is_live(a) else "Final price"} {format_inr(a["current_price"])}</div>',
                unsafe_allow_html=True,
            )
        with c_side:
            pills = ui.pill(label, tone=tone)
            if a["standing"] == "Won" and a["payment_status"]:
                pills += " " + ui.pill(PAY[a["payment_status"]], tone=PAY_TONE[a["payment_status"]])
            st.markdown(pills, unsafe_allow_html=True)
            if auctions.is_live(a):
                st.caption(f'{time_left_text(a["end_time"])} left, ends {format_local(a["end_time"])}')
            if st.button("View auction", key=f"myb_view_{a['id']}", icon=":material/gavel:", width="stretch"):
                ui.open_auction(a["id"])
            if a["standing"] == "Won" and a["payment_status"] == "pending" and ui.page_exists("views/payment.py"):
                if st.button("Pay now", key=f"myb_pay_{a['id']}", type="primary", icon=":material/payments:", width="stretch"):
                    st.session_state["pay_auction_id"] = a["id"]
                    st.switch_page("views/payment.py")


tab_active, tab_won, tab_closed = st.tabs([f"Active ({len(active)})", f"Won ({len(won)})", f"Closed ({len(closed)})"])
for tab, group, empty in (
    (tab_active, active, "You are not bidding on any live auctions."),
    (tab_won, won, "You have not won an auction yet."),
    (tab_closed, closed, "Nothing here yet."),
):
    with tab:
        if not group:
            st.write(empty)
            if group is active:
                ui.nav_button("Browse auctions", "views/browse.py", icon=":material/storefront:", key="myb_to_browse")
        for a in group:
            row(a)
