"""Create a member account."""
import streamlit as st

from core import auth, ui

form_col = ui.auth_layout("auth_register.jpg")

with form_col:
    ui.form_heading("Create your account", "Free to join. You can bid and sell right away.")
    with st.form("register_form"):
        full_name = st.text_input("Full name")
        c1, c2 = st.columns(2)
        username = c1.text_input("Username", help="3 to 30 characters: letters, numbers, dots, underscores.")
        email = c2.text_input("Email")
        c3, c4 = st.columns(2)
        password = c3.text_input("Password", type="password", help="At least 8 characters with a letter and a number.")
        confirm = c4.text_input("Confirm password", type="password")
        submitted = st.form_submit_button(
            "Create account", type="primary", icon=":material/person_add:", width="stretch"
        )
    if submitted:
        ok, result = auth.register_user(full_name, username, email, password, confirm)
        if ok:
            auth.login(result)
            st.rerun()
        else:
            st.error(result)

    ui.nav_button("Already have an account? Log in", "views/login.py", icon=":material/login:", key="reg_to_login")
