"""Auction Details: photo, description, live price and clock, bidding and bid history."""
from html import escape

import streamlit as st

from core import auctions, auth, images, ui
from core.utils import (
    format_inr,
    format_local,
    mask_name,
    md_escape,
    now_utc,
    parse_iso,
    time_left_text,
)

# Buttons inside the live panel ask for a page change this way (a full rerun, then switch).
_goto = st.session_state.pop("_goto", None)
if _goto:
    st.switch_page(_goto)


def _requested_id():
    raw = st.session_state.get("selected_auction_id") or st.query_params.get("auction")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _leave_details():
    """Forget the open auction so the Browse page starts clean."""
    st.session_state.pop("selected_auction_id", None)
    try:
        st.query_params.pop("auction", None)
    except Exception:
        pass


def _go(label, path, icon, key, primary=False):
    """A button that works inside the live panel (which reruns on its own)."""
    if st.button(label, key=key, icon=icon, type="primary" if primary else "secondary", width="stretch"):
        st.session_state["_goto"] = path
        st.rerun()


auction_id = _requested_id()
if auction_id is None:
    st.markdown("### Choose an auction")
    st.write("Open an auction from the browse page to see its photo, price, clock and bids.")
    ui.nav_button("Browse auctions", "views/browse.py", icon=":material/storefront:", primary=True, key="details_to_browse")
    st.stop()

auctions.close_expired()
auction = auctions.get_auction(auction_id)
if not auction or auction["status"] == "removed":
    st.error("That auction could not be found. It may have been removed.")
    ui.nav_button("All auctions", "views/browse.py", icon=":material/arrow_back:", key="details_missing_back", before=_leave_details)
    st.stop()

st.query_params["auction"] = str(auction_id)
user = auth.current_user()
live_at_load = auctions.is_live(auction)

ui.nav_button("All auctions", "views/browse.py", icon=":material/arrow_back:", key="details_back", before=_leave_details)
tags = ui.pill(auction["category_name"] or "General", tone="indigo") + " " + ui.pill(auction["condition"], tone="amber")
st.markdown(
    f'<div class="nl-detail-tags">{tags}</div><div class="nl-detail-title">{escape(auction["title"])}</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 1], gap="large")

# ---------------------------------------------------------------- left column
with left:
    st.image(images.product_image(auction["image_id"]), width="stretch")
    st.markdown("#### About this item")
    st.markdown(md_escape(auction["description"]) or "The seller did not add a description.")
    st.markdown(
        '<table class="nl-facts">'
        f'<tr><td>Seller</td><td>@{escape(auction["seller_username"])}</td></tr>'
        f'<tr><td>Condition</td><td>{escape(auction["condition"])}</td></tr>'
        f'<tr><td>Category</td><td>{escape(auction["category_name"] or "General")}</td></tr>'
        f'<tr><td>Starting price</td><td>{format_inr(auction["starting_price"])}</td></tr>'
        f'<tr><td>Minimum increment</td><td>{format_inr(auction["min_increment"])}</td></tr>'
        f'<tr><td>Listed on</td><td>{format_local(auction["start_time"], "%d %b %Y")}</td></tr>'
        "</table>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------- right column
# The live panel re-reads the auction every few seconds so price, clock and
# history stay current without the visitor refreshing the page.
@st.fragment(run_every=5 if live_at_load else None)
def live_panel():
    a = auctions.get_auction(auction_id)
    live = auctions.is_live(a)

    if live_at_load and not live:  # the clock just ran out: close it and redraw the page
        auctions.close_expired()
        st.rerun()

    flash = st.session_state.pop("_bid_flash", None)
    if flash:
        (st.success if flash[0] == "ok" else st.error)(flash[1])

    # ---- price and clock
    has_bids = a["bid_count"] > 0
    if live:
        price_label = "Current bid" if has_bids else "Starting price"
    else:
        price_label = "Sold for" if a["winner_id"] else ("Final bid" if has_bids else "Starting price")
    seconds_left = (parse_iso(a["end_time"]) - now_utc()).total_seconds()
    clock_class = "nl-time urgent" if live and seconds_left < 3600 else "nl-time"
    clock_text = time_left_text(a["end_time"]) if live else "Ended"
    bids_text = f'{a["bid_count"]} bid{"" if a["bid_count"] == 1 else "s"}'
    reserve_pill = ""
    if a["reserve_price"] and live:
        met = a["current_price"] >= a["reserve_price"] and has_bids
        reserve_pill = ui.pill("Reserve met" if met else "Reserve not met", tone="green" if met else "amber")

    st.markdown(
        '<div class="nl-panel"><div class="nl-panel-row">'
        f'<div><div class="nl-price-label">{price_label}</div><div class="nl-big-price">{format_inr(a["current_price"])}</div>'
        f'<div class="nl-muted" style="margin-top:.3rem">{bids_text} {reserve_pill}</div></div>'
        f'<div style="text-align:right"><div class="nl-price-label">{"Time left" if live else "Auction"}</div>'
        f'<div class="{clock_class}">{clock_text}</div>'
        f'<div class="nl-muted" style="font-size:.85rem">{"Ends" if live else "Ended"} {format_local(a["end_time"])}</div></div>'
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ---- bidding area (depends on who is looking and what state the auction is in)
    if live:
        minimum = auctions.min_next_bid(a)
        if user is None:
            st.info("Log in or create an account to place a bid.")
            c1, c2 = st.columns(2)
            with c1:
                _go("Log in", "views/login.py", ":material/login:", "det_login", primary=True)
            with c2:
                _go("Create account", "views/register.py", ":material/person_add:", "det_register")
        elif user["role"] == "admin":
            st.info("Administrator accounts can view auctions but cannot bid.")
        elif user["id"] == a["seller_id"]:
            st.info("This is your listing. Sellers cannot bid on their own items.")
        else:
            if user["id"] == a["leader_id"]:
                st.success("You are the highest bidder. You can raise your bid at any time.")
            st.caption(
                f"Minimum bid {format_inr(minimum)}. "
                f"Each bid must beat the current price by at least {format_inr(a['min_increment'])}."
            )
            min_rupees = -(-minimum // 100)
            with st.form(f"bid_form_{auction_id}"):
                amount = st.number_input(
                    "Your bid (rupees)",
                    min_value=min_rupees,
                    value=min_rupees,
                    step=max(1, a["min_increment"] // 100),
                    key=f"bid_amount_{auction_id}_{minimum}",
                )
                label = "Raise my bid" if user["id"] == a["leader_id"] else "Place bid"
                submitted = st.form_submit_button(label, type="primary", icon=":material/gavel:", width="stretch")
            if submitted:
                ok, message = auctions.place_bid(auction_id, user["id"], int(amount) * 100)
                st.session_state["_bid_flash"] = ("ok" if ok else "error", message)
                st.rerun(scope="fragment")
    else:
        if a["winner_id"]:
            st.markdown(
                f'<div class="nl-result">Sold to @{escape(mask_name(a["winner_username"]))} for {format_inr(a["winning_amount"])}.</div>',
                unsafe_allow_html=True,
            )
            if user and user["id"] == a["winner_id"]:
                st.success("You won this auction.")
                if ui.page_exists("views/payment.py"):
                    _go("Go to payment", "views/payment.py", ":material/payments:", "det_pay", primary=True)
        else:
            reason = "The reserve price was not met." if has_bids and a["reserve_price"] else "There were no bids."
            st.markdown(f'<div class="nl-result muted">This auction ended without a sale. {reason}</div>', unsafe_allow_html=True)

    # ---- bid history
    st.markdown("#### Bid history")
    history = auctions.bids_for(auction_id)
    if not history:
        st.caption("No bids yet. The first bid sets the price.")
    else:
        st.dataframe(
            [
                {
                    "Bidder": "You" if user and b["bidder_id"] == user["id"] else mask_name(b["username"]),
                    "Bid": format_inr(b["amount"]),
                    "Placed": format_local(b["created_at"]),
                }
                for b in history
            ],
            hide_index=True,
            width="stretch",
        )


with right:
    live_panel()
