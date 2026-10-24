"""Payment (demo): shows the QR image the administrator set. No money is processed."""
from html import escape

import streamlit as st

from core import auth, db, images, payments, ui
from core.config import PLACEHOLDER_DIR
from core.utils import format_inr, format_local

user = auth.require_login()
if user["role"] == "admin":
    st.info("Administrator accounts do not make payments. Set the payment QR code in the Admin Panel.")
    st.stop()

ui.page_header("Payment", "Pay for the auctions you won. This is a demonstration page, so no real money moves.", "banner_payment.jpg")
ui.quick_nav("views/payment.py")

flash = st.session_state.pop("_pay_flash", None)
if flash:
    (st.success if flash[0] == "ok" else st.error)(flash[1])

owed = payments.for_buyer(user["id"])
if not owed:
    st.markdown("### Nothing to pay")
    st.write("When you win an auction it will appear here with the amount due.")
    ui.nav_button("Find an auction to win", "views/browse.py", icon=":material/storefront:", primary=True, key="pay_to_browse")
    st.stop()

STATUS = {"pending": ("Payment due", "amber"), "submitted": ("Waiting for confirmation", "indigo"), "confirmed": ("Payment confirmed", "green")}
labels = {p["auction_id"]: f'{p["title"]} - {format_inr(p["amount"])} ({STATUS[p["status"]][0]})' for p in owed}
ids = list(labels)
wanted = st.session_state.get("pay_auction_id")
if wanted not in ids:
    pending = [p["auction_id"] for p in owed if p["status"] == "pending"]
    wanted = pending[0] if pending else ids[0]

chosen = st.selectbox("Purchase", ids, index=ids.index(wanted), format_func=lambda i: labels[i], key="pay_select")
st.session_state["pay_auction_id"] = chosen
pay = next(p for p in owed if p["auction_id"] == chosen)
label, tone = STATUS[pay["status"]]

left, right = st.columns([1, 1], gap="large")

with left:
    st.image(images.product_image(pay["image_id"]), width="stretch")
    st.markdown(
        f'<div class="nl-row-title" style="font-size:1.4rem">{escape(pay["title"])}</div>'
        f'<div class="nl-row-meta">Sold by @{escape(pay["seller_username"])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="nl-panel"><div class="nl-price-label">Amount due</div>'
        f'<div class="nl-big-price">{format_inr(pay["amount"])}</div>'
        f'<div style="margin-top:.6rem">{ui.pill(label, tone=tone)}</div></div>',
        unsafe_allow_html=True,
    )

with right:
    qr_id = payments.qr_image_id()
    payee = db.get_setting("payment_payee_name")
    instructions = db.get_setting("payment_instructions")
    st.markdown("#### Scan to pay")
    st.image(images.product_image(qr_id) if qr_id and images.load_image(qr_id) else str(PLACEHOLDER_DIR / "qr_placeholder.jpg"), width=300)
    if not (qr_id and images.load_image(qr_id)):
        st.caption("The administrator has not uploaded a QR code yet. This is a sample image.")
    if payee:
        st.markdown(f"**Pay to:** {escape(payee)}")
    if instructions:
        st.write(instructions)

    if pay["status"] == "pending":
        with st.form(f"pay_form_{chosen}"):
            reference = st.text_input("Transaction reference (optional)", max_chars=60, placeholder="For example the UPI reference number")
            done = st.form_submit_button("I have paid", type="primary", icon=":material/check_circle:", width="stretch")
        if done:
            ok, message = payments.submit(chosen, user["id"], reference)
            st.session_state["_pay_flash"] = ("ok" if ok else "error", message)
            st.rerun()
    elif pay["status"] == "submitted":
        st.info("Your payment is waiting for the administrator to confirm it." + (f' Reference: {pay["reference"]}.' if pay["reference"] else ""))
    else:
        st.success(f'Payment confirmed on {format_local(pay["confirmed_at"], "%d %b %Y")}. Thank you.')
