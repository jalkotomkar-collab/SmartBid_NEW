"""Account details and password change."""
import streamlit as st

from core import auth, ui
from core.utils import format_local

user = auth.require_login()
ui.page_header("My account", "Your details and sign-in settings.", "banner_account.jpg")
ui.quick_nav("views/account.py")

record = auth.get_user(user["id"])

c1, c2, c3 = st.columns(3)
c1.metric("Name", record["full_name"])
c2.metric("Username", record["username"])
c3.metric("Member since", format_local(record["created_at"], "%d %b %Y"))
st.caption(f"Signed in with {record['email']}")

ui.section_title("Change password")
with st.form("password_form"):
    current = st.text_input("Current password", type="password")
    c1, c2 = st.columns(2)
    new = c1.text_input("New password", type="password", help="At least 8 characters with a letter and a number.")
    confirm = c2.text_input("Confirm new password", type="password")
    submitted = st.form_submit_button("Update password", type="primary", icon=":material/lock_reset:")
if submitted:
    ok, message = auth.change_password(user["id"], current, new, confirm)
    (st.success if ok else st.error)(message)
