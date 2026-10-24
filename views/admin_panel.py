"""Admin Panel: overview, auctions, users, categories, payments, payment QR and settings."""
from math import ceil

import streamlit as st

from core import auctions, auth, db, images, payments, sample_data, stats, ui
from core.config import PLACEHOLDER_DIR
from core.utils import format_inr, format_local

admin = auth.require_admin()
ui.page_header("Admin panel", "Oversee auctions, members and payments, and set the payment QR code.", "banner_admin.jpg")
ui.quick_nav("views/admin_panel.py")

flash = st.session_state.pop("_admin_flash", None)
if flash:
    (st.success if flash[0] == "ok" else st.error)(flash[1])


def done(kind, message):
    st.session_state["_admin_flash"] = (kind, message)
    st.rerun()


tab_over, tab_auc, tab_users, tab_cat, tab_pay, tab_qr, tab_set = st.tabs(
    ["Overview", "Auctions", "Users", "Categories", "Payments", "Payment QR", "Settings"]
)

# ---------------------------------------------------------------- overview
with tab_over:
    n = stats.platform()
    c = st.columns(5)
    c[0].metric("Live auctions", n["live"])
    c[1].metric("Items sold", n["sold"])
    c[2].metric("Bids placed", n["bids"])
    c[3].metric("Members", n["members"])
    c[4].metric("Payments to confirm", n["to_confirm"])
    ui.section_title("Latest bids")
    latest = db.fetch_all(
        "SELECT b.amount, b.created_at, u.username AS bidder, a.title FROM bids b "
        "JOIN users u ON u.id = b.bidder_id JOIN auctions a ON a.id = b.auction_id "
        "ORDER BY b.id DESC LIMIT 10"
    )
    if latest:
        st.dataframe(
            [{"Item": r["title"], "Bidder": r["bidder"], "Bid": format_inr(r["amount"]), "Placed": format_local(r["created_at"])} for r in latest],
            hide_index=True, width="stretch",
        )
    else:
        st.write("No bids have been placed yet.")

# ---------------------------------------------------------------- auctions
with tab_auc:
    f1, f2 = st.columns([2, 1], vertical_alignment="bottom")
    term = f1.text_input("Search by title or seller", key="adm_auc_search")
    state = f2.selectbox("Status", ["All", "Live", "Ended", "Cancelled"], key="adm_auc_status")
    rows_ = auctions.admin_auctions(term, state)
    if rows_:
        st.dataframe(
            [
                {
                    "ID": r["id"], "Title": r["title"], "Seller": r["seller_username"],
                    "Price": format_inr(r["current_price"]), "Bids": r["bid_count"],
                    "Status": "Live" if auctions.is_live(r) else ("Sold" if r["winner_id"] else r["status"].title()),
                    "Ends": format_local(r["end_time"]),
                }
                for r in rows_
            ],
            hide_index=True, width="stretch",
        )
        st.markdown("#### Remove an auction")
        st.caption("Removing hides the auction from everyone. Use it for listings that break the rules.")
        pick = st.selectbox("Auction", [r["id"] for r in rows_], format_func=lambda i: next(f'#{r["id"]} - {r["title"]}' for r in rows_ if r["id"] == i), key="adm_auc_pick")
        sure = st.checkbox("I understand this hides the auction and any bids on it", key="adm_auc_sure")
        if st.button("Remove auction", icon=":material/delete:", disabled=not sure):
            done("ok", "The auction was removed.") if auctions.remove_auction(pick) else done("error", "That auction was already removed.")
    else:
        st.write("No auctions match.")

# ------------------------------------------------------------------- users
with tab_users:
    people = db.fetch_all(
        "SELECT u.id, u.full_name, u.username, u.email, u.role, u.is_active, u.created_at, "
        "(SELECT COUNT(*) FROM auctions WHERE seller_id = u.id AND status != 'removed') AS listings, "
        "(SELECT COUNT(*) FROM bids WHERE bidder_id = u.id) AS bids "
        "FROM users u WHERE u.email NOT LIKE '%@example.invalid' ORDER BY u.id"
    )
    st.dataframe(
        [
            {"Name": p["full_name"], "Username": p["username"], "Email": p["email"],
             "Role": p["role"].title(), "Active": "Yes" if p["is_active"] else "No",
             "Listings": p["listings"], "Bids": p["bids"], "Joined": format_local(p["created_at"], "%d %b %Y")}
            for p in people
        ],
        hide_index=True, width="stretch",
    )
    others = [p for p in people if p["id"] != admin["id"] and p["role"] != "admin"]
    if others:
        st.markdown("#### Activate or deactivate a member")
        who = st.selectbox("Member", [p["id"] for p in others], format_func=lambda i: next(f'@{p["username"]} ({"active" if p["is_active"] else "deactivated"})' for p in others if p["id"] == i), key="adm_user_pick")
        target = next(p for p in others if p["id"] == who)
        label = "Deactivate member" if target["is_active"] else "Reactivate member"
        if st.button(label, icon=":material/person_off:" if target["is_active"] else ":material/person_check:"):
            db.execute("UPDATE users SET is_active = ? WHERE id = ?", (0 if target["is_active"] else 1, who))
            done("ok", f'@{target["username"]} was {"deactivated" if target["is_active"] else "reactivated"}.')

# -------------------------------------------------------------- categories
with tab_cat:
    cats = db.fetch_all(
        "SELECT c.id, c.name, (SELECT COUNT(*) FROM auctions WHERE category_id = c.id) AS used FROM categories c ORDER BY c.name"
    )
    st.dataframe([{"Category": c["name"], "Auctions": c["used"]} for c in cats], hide_index=True, width="stretch")
    a, b = st.columns(2, gap="large")
    with a:
        with st.form("cat_add"):
            new_name = st.text_input("New category name", max_chars=40)
            if st.form_submit_button("Add category", type="primary", icon=":material/add:", width="stretch"):
                name = new_name.strip()
                if len(name) < 2:
                    st.error("Enter a category name.")
                elif db.fetch_one("SELECT 1 AS x FROM categories WHERE name = ?", (name,)):
                    st.error("That category already exists.")
                else:
                    db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                    done("ok", f'Added the category "{name}".')
    with b:
        unused = [c for c in cats if c["used"] == 0]
        if unused:
            gone = st.selectbox("Delete an unused category", [c["id"] for c in unused], format_func=lambda i: next(c["name"] for c in unused if c["id"] == i), key="cat_del")
            if st.button("Delete category", icon=":material/delete:"):
                db.execute("DELETE FROM categories WHERE id = ?", (gone,))
                done("ok", "The category was deleted.")
        else:
            st.caption("Categories with auctions in them cannot be deleted.")

# ---------------------------------------------------------------- payments
with tab_pay:
    allp = payments.all_payments()
    STATE = {"pending": "Unpaid", "submitted": "Waiting for you", "confirmed": "Confirmed"}
    if not allp:
        st.write("No auction has been won yet, so there are no payments.")
    else:
        st.dataframe(
            [{"Item": p["title"], "Buyer": p["buyer_username"], "Seller": p["seller_username"],
              "Amount": format_inr(p["amount"]), "Reference": p["reference"] or "", "Status": STATE[p["status"]]}
             for p in allp],
            hide_index=True, width="stretch",
        )
        waiting = [p for p in allp if p["status"] == "submitted"]
        if waiting:
            st.markdown("#### Confirm a payment")
            pick = st.selectbox("Payment", [p["id"] for p in waiting], format_func=lambda i: next(f'{p["title"]} - @{p["buyer_username"]} - {format_inr(p["amount"])}' for p in waiting if p["id"] == i), key="adm_pay_pick")
            c1, c2 = st.columns(2)
            if c1.button("Confirm payment received", type="primary", icon=":material/check_circle:", width="stretch"):
                done("ok", "Payment confirmed.") if payments.confirm(pick) else done("error", "That payment changed. Reload and try again.")
            if c2.button("Mark as not received", icon=":material/undo:", width="stretch"):
                done("ok", "The payment was sent back to the buyer as unpaid.") if payments.reject(pick) else done("error", "That payment changed. Reload and try again.")
        else:
            st.caption("No payments are waiting for confirmation.")

# ---------------------------------------------------------------------- QR
with tab_qr:
    st.write("Buyers see this image on the Payment page. It is a demo, so no payment is processed by the app.")
    left, right = st.columns([1, 1.3], gap="large")
    qr_id = payments.qr_image_id()
    with left:
        st.markdown("#### Current image")
        has_qr = bool(qr_id and images.load_image(qr_id))
        st.image(images.product_image(qr_id) if has_qr else str(PLACEHOLDER_DIR / "qr_placeholder.jpg"), width=280)
        st.caption("Uploaded by you" if has_qr else "Sample image. Upload your own below.")
        if has_qr and st.button("Remove uploaded image", icon=":material/delete:"):
            payments.set_qr(None)
            done("ok", "The QR image was removed. Buyers will see the sample image.")
    with right:
        upload = st.file_uploader("Upload a QR code or payment image", type=["png", "jpg", "jpeg", "webp"], key="adm_qr_file")
        if upload:
            st.image(upload, caption="Preview", width=200)
        with st.form("qr_form"):
            payee = st.text_input("Payee name shown to buyers", value=db.get_setting("payment_payee_name"), max_chars=80)
            instructions = st.text_area("Instructions", value=db.get_setting("payment_instructions"), max_chars=500, height=110)
            save = st.form_submit_button("Save payment details", type="primary", icon=":material/save:", width="stretch")
        if save:
            try:
                if upload:
                    payments.set_qr(images.save_upload(upload, max_side=800))
                db.set_setting("payment_payee_name", payee.strip())
                db.set_setting("payment_instructions", instructions.strip())
            except ValueError as exc:
                st.error(str(exc))
            else:
                done("ok", "Payment details saved.")

# ---------------------------------------------------------------- settings
with tab_set:
    with st.form("settings_form"):
        st.markdown("#### Bidding rules")
        st.caption("Auctions always end exactly at their end time. Bids never extend the clock.")
        floor = st.number_input(
            "Smallest minimum bid increment sellers may set (rupees)", min_value=1, max_value=10000,
            value=max(1, ceil(int(db.get_setting("min_increment_floor")) / 100)),
        )
        saved = st.form_submit_button("Save settings", type="primary", icon=":material/save:", width="stretch")
    if saved:
        db.set_setting("min_increment_floor", str(int(floor) * 100))
        done("ok", "Settings saved.")
    st.markdown("#### Sample data")
    st.caption("Adds the demo listings again. They end within a few days, so use this to refill an empty site.")
    if st.button("Add sample auctions", icon=":material/library_add:"):
        done("ok", f"Added {sample_data.add_samples()} sample auctions.")
