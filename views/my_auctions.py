"""My Auctions: everything you have listed, with edit and cancel while there are no bids."""
from math import ceil

import streamlit as st

from core import auctions, auth, db, images, payments, ui
from core.utils import format_inr, format_local, mask_name, time_left_text
from html import escape

user = auth.require_login()
if user["role"] == "admin":
    st.info("Administrator accounts do not have listings. Use the Admin Panel to manage auctions.")
    st.stop()

ui.page_header("My auctions", "Everything you have listed, and how each one is doing.", "banner_my_auctions.jpg")
ui.quick_nav("views/my_auctions.py")

flash = st.session_state.pop("_my_flash", None)
if flash:
    (st.success if flash[0] == "ok" else st.error)(flash[1])

items = auctions.seller_auctions(user["id"])
categories = db.fetch_all("SELECT id, name FROM categories ORDER BY name")
category_ids = {c["name"]: c["id"] for c in categories}
floor_rupees = max(1, ceil(int(db.get_setting("min_increment_floor")) / 100))

live = [a for a in items if auctions.is_live(a)]
cancelled = [a for a in items if a["status"] == "cancelled"]
ended = [a for a in items if a not in live and a not in cancelled]
sold = [a for a in ended if a["winner_id"]]

m1, m2, m3 = st.columns(3)
m1.metric("Live", len(live))
m2.metric("Sold", len(sold))
m3.metric("Listed in total", len(items))

PAY_LABEL = {"pending": ("Awaiting payment", "amber"), "submitted": ("Payment sent, waiting for admin", "indigo"), "confirmed": ("Payment confirmed", "green")}


def edit_form(a):
    """Edit panel for a live listing that has no bids yet."""
    with st.expander("Edit listing"):
        photo = st.file_uploader("Replace photo (optional)", type=["jpg", "jpeg", "png", "webp"], key=f"edit_photo_{a['id']}")
        with st.form(f"edit_form_{a['id']}"):
            title = st.text_input("Title", value=a["title"], max_chars=100)
            c1, c2 = st.columns(2)
            names = list(category_ids)
            current = a["category_name"] if a["category_name"] in names else names[0]
            category = c1.selectbox("Category", names, index=names.index(current))
            condition = c2.selectbox("Condition", auctions.CONDITIONS, index=auctions.CONDITIONS.index(a["condition"]) if a["condition"] in auctions.CONDITIONS else 2)
            description = st.text_area("Description", value=a["description"], max_chars=2000, height=130)
            c3, c4 = st.columns(2)
            start = c3.number_input("Starting price (rupees)", min_value=1, value=max(1, a["starting_price"] // 100), step=50)
            inc = c4.number_input("Minimum bid increment (rupees)", min_value=floor_rupees, value=max(floor_rupees, a["min_increment"] // 100), step=10)
            has_reserve = st.checkbox("Reserve price", value=bool(a["reserve_price"]))
            reserve = st.number_input("Reserve (rupees)", min_value=0, value=(a["reserve_price"] or 0) // 100, step=100)
            save = st.form_submit_button("Save changes", type="primary", icon=":material/save:", width="stretch")
        if save:
            problems = []
            if len(title.strip()) < 5:
                problems.append("Give the item a title of at least 5 characters.")
            if len(description.strip()) < 10:
                problems.append("Add a description of at least 10 characters.")
            if has_reserve and reserve < start:
                problems.append("The reserve price must be at least the starting price.")
            if problems:
                for p in problems:
                    st.error(p)
                return
            try:
                new_image = images.save_upload(photo, aspect=(4, 3)) if photo else auctions._KEEP
            except ValueError as exc:
                st.error(str(exc))
                return
            ok = auctions.update_auction(
                a["id"], user["id"], title.strip(), category_ids[category], condition, description.strip(),
                int(start) * 100, int(inc) * 100, int(reserve) * 100 if has_reserve else None, new_image,
            )
            if ok:
                if photo and a["image_id"]:
                    images.delete_image(a["image_id"])
                st.session_state["_my_flash"] = ("ok", "Your listing was updated.")
            else:
                if photo and new_image is not auctions._KEEP:
                    images.delete_image(new_image)
                st.session_state["_my_flash"] = ("error", "This listing can no longer be edited. It may have received a bid or ended.")
            st.rerun()


def row(a, kind):
    with st.container(key=f"row_mya_{a['id']}"):
        c_img, c_main, c_side = st.columns([1.1, 3, 1.7], vertical_alignment="center")
        c_img.image(images.product_image(a["image_id"]), width="stretch")
        bids = f'{a["bid_count"]} bid{"" if a["bid_count"] == 1 else "s"}'
        with c_main:
            st.markdown(
                f'<div class="nl-row-title">{escape(a["title"])}</div>'
                f'<div class="nl-row-meta">{escape(a["category_name"] or "General")}, {escape(a["condition"])}<br>'
                f'Starts at {format_inr(a["starting_price"])}, minimum step {format_inr(a["min_increment"])}</div>'
                f'<div class="nl-row-price">{format_inr(a["current_price"])} '
                f'<span class="nl-row-meta" style="font-weight:400">{bids}</span></div>',
                unsafe_allow_html=True,
            )
        with c_side:
            if kind == "live":
                st.markdown(ui.pill(f'{time_left_text(a["end_time"])} left', tone="indigo"), unsafe_allow_html=True)
                st.caption(f'Ends {format_local(a["end_time"])}')
            elif kind == "ended":
                if a["winner_id"]:
                    label, tone = PAY_LABEL.get(a["payment_status"], ("Sold", "green"))
                    st.markdown(ui.pill("Sold", tone="green") + " " + ui.pill(label, tone=tone), unsafe_allow_html=True)
                    st.caption(f'To @{mask_name(a["winner_username"])} for {format_inr(a["winning_amount"])}')
                else:
                    st.markdown(ui.pill("Ended, not sold", amber=True), unsafe_allow_html=True)
                    st.caption("No bids" if not a["bid_count"] else "Reserve not met")
            else:
                st.markdown(ui.pill("Cancelled", tone="grey"), unsafe_allow_html=True)
            if st.button("View", key=f"mya_view_{a['id']}", icon=":material/gavel:", width="stretch"):
                ui.open_auction(a["id"])

        if kind == "live":
            if a["bid_count"]:
                st.caption("Editing and cancelling are locked because this listing has bids.")
            else:
                edit_form(a)
                if st.session_state.get("_confirm_cancel") == a["id"]:
                    st.warning("Cancel this listing? It will disappear from Browse.")
                    y, n = st.columns(2)
                    if y.button("Yes, cancel listing", key=f"mya_yes_{a['id']}", type="primary", width="stretch"):
                        done = auctions.cancel_auction(a["id"], user["id"])
                        st.session_state.pop("_confirm_cancel", None)
                        st.session_state["_my_flash"] = ("ok", "The listing was cancelled.") if done else ("error", "This listing can no longer be cancelled.")
                        st.rerun()
                    if n.button("Keep it", key=f"mya_no_{a['id']}", width="stretch"):
                        st.session_state.pop("_confirm_cancel", None)
                        st.rerun()
                elif st.button("Cancel listing", key=f"mya_cancel_{a['id']}", icon=":material/cancel:"):
                    st.session_state["_confirm_cancel"] = a["id"]
                    st.rerun()


tab_live, tab_ended, tab_cancelled = st.tabs([f"Live ({len(live)})", f"Ended ({len(ended)})", f"Cancelled ({len(cancelled)})"])
for tab, group, kind, empty in (
    (tab_live, live, "live", "You have no live listings."),
    (tab_ended, ended, "ended", "None of your auctions have ended yet."),
    (tab_cancelled, cancelled, "cancelled", "You have not cancelled any listings."),
):
    with tab:
        if not group:
            st.write(empty)
            if kind == "live":
                ui.nav_button("List an item", "views/sell.py", icon=":material/sell:", key="mya_to_sell")
        for a in group:
            row(a, kind)
