"""Sell Product: list an item for auction."""
from datetime import timedelta
from math import ceil

import streamlit as st

from core import auctions, auth, db, images, ui
from core.config import PLACEHOLDER_DIR
from core.utils import now_utc

user = auth.require_login()
if user["role"] == "admin":
    st.info("Administrator accounts cannot list items. Use a member account to sell.")
    st.stop()

ui.page_header(
    "Sell a product",
    "List an item in a few minutes. Auctions can run from 1 minute to 30 days.",
    "banner_sell.jpg",
)

ui.quick_nav("views/sell.py")
attempt = st.session_state.setdefault("_sell_n", 0)

# ---- success screen after listing
listed_id = st.session_state.get("_listed_id")
if listed_id:
    st.success("Your item is live. Buyers can start bidding now.")
    c1, c2, c3 = st.columns(3)
    if c1.button("View listing", type="primary", icon=":material/gavel:", width="stretch"):
        ui.open_auction(listed_id)
    if c2.button("List another item", icon=":material/add:", width="stretch"):
        st.session_state.pop("_listed_id", None)
        st.session_state["_sell_n"] = attempt + 1
        st.rerun()
    if c3.button("My auctions", icon=":material/inventory_2:", width="stretch"):
        st.switch_page("views/my_auctions.py")
    st.stop()

categories = db.fetch_all("SELECT id, name FROM categories ORDER BY name")
category_ids = {c["name"]: c["id"] for c in categories}
floor_rupees = max(1, ceil(int(db.get_setting("min_increment_floor")) / 100))
DURATIONS = {
    "1 minute": timedelta(minutes=1),
    "2 minutes": timedelta(minutes=2),
    "5 minutes": timedelta(minutes=5),
    "10 minutes": timedelta(minutes=10),
    "15 minutes": timedelta(minutes=15),
    "30 minutes": timedelta(minutes=30),
    "1 hour": timedelta(hours=1),
    "6 hours": timedelta(hours=6),
    "1 day": timedelta(days=1),
    "3 days": timedelta(days=3),
    "7 days": timedelta(days=7),
    "14 days": timedelta(days=14),
}
CUSTOM = "Custom length"
UNITS = {"minutes": timedelta(minutes=1), "hours": timedelta(hours=1), "days": timedelta(days=1)}
MIN_LENGTH = timedelta(minutes=1)
MAX_LENGTH = timedelta(days=30)

photo_col, form_col = st.columns([1, 1.45], gap="large")

with photo_col:
    photo = st.file_uploader(
        "Product photo",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"photo_{attempt}",
        help="JPG, PNG or WebP up to 5 MB. It is cropped to a 4:3 frame so listings line up.",
    )
    if photo:
        st.image(photo, caption="This is how buyers will see your photo (cropped to 4:3).", width="stretch")
    else:
        st.image(str(PLACEHOLDER_DIR / images.PRODUCT_PLACEHOLDER), caption="No photo yet. Listings with a clear photo are easier to judge.", width="stretch")

with form_col:
    with st.form(f"sell_form_{attempt}"):
        title = st.text_input("Title", max_chars=100, placeholder="What are you selling?")
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", list(category_ids))
        condition = c2.selectbox("Condition", auctions.CONDITIONS, index=2)
        description = st.text_area(
            "Description",
            max_chars=2000,
            height=150,
            placeholder="Size, age, flaws, what is included, how it was used.",
        )

        c3, c4 = st.columns(2)
        start_price = c3.number_input("Starting price (rupees)", min_value=1, value=500, step=50)
        increment = c4.number_input(
            "Minimum bid increment (rupees)",
            min_value=floor_rupees,
            value=max(floor_rupees, 50),
            step=10,
            help="Each new bid must beat the current price by at least this amount.",
        )

        use_reserve = st.checkbox("Set a reserve price")
        reserve = st.number_input(
            "Reserve price (rupees)",
            min_value=0,
            value=0,
            step=100,
            help="A hidden minimum. If bidding ends below it, the item is not sold. Used only when the box above is ticked.",
        )

        duration = st.selectbox("Auction length", list(DURATIONS) + [CUSTOM], index=list(DURATIONS).index("7 days"))
        d1, d2 = st.columns(2)
        custom_amount = d1.number_input("Custom length", min_value=1, value=45, step=1)
        custom_unit = d2.selectbox("Custom unit", list(UNITS))
        st.caption("The custom length is used only when 'Custom length' is selected above. Auctions end exactly on time.")

        submitted = st.form_submit_button("List item", type="primary", icon=":material/sell:", width="stretch")

if submitted:
    errors = []
    title, description = title.strip(), description.strip()
    if len(title) < 5:
        errors.append("Give the item a title of at least 5 characters.")
    if len(description) < 10:
        errors.append("Add a description of at least 10 characters so buyers know what they are bidding on.")
    if use_reserve and reserve * 100 < start_price * 100:
        errors.append("The reserve price must be at least the starting price.")

    if duration == CUSTOM:
        length = custom_amount * UNITS[custom_unit]
        if length < MIN_LENGTH:
            errors.append("An auction must run for at least 1 minute.")
        elif length > MAX_LENGTH:
            errors.append("Auctions can run for at most 30 days.")
        end_utc = now_utc() + length
    else:
        end_utc = now_utc() + DURATIONS[duration]

    if errors:
        for message in errors:
            st.error(message)
    else:
        try:
            image_id = images.save_upload(photo, aspect=(4, 3)) if photo else None
            new_id = auctions.create_auction(
                seller_id=user["id"],
                title=title,
                category_id=category_ids[category],
                condition=condition,
                description=description,
                image_id=image_id,
                starting_price=int(start_price) * 100,
                min_increment=int(increment) * 100,
                reserve_price=int(reserve) * 100 if use_reserve else None,
                end_time_utc=end_utc,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["_listed_id"] = new_id
            st.rerun()
