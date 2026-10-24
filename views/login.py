"""Member login."""
import streamlit as st

from core import auth, ui

form_col = ui.auth_layout("auth_login.jpg")

with form_col:
    ui.form_heading("Log in", "Use your username or email and your password.")
    with st.form("login_form"):
        identifier = st.text_input("Username or email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Log in", type="primary", icon=":material/login:", width="stretch"
        )
    if submitted:
        ok, result = auth.attempt_login(identifier, password, role="user")
        if ok:
            auth.login(result)
            st.rerun()
        else:
            st.error(result)

    ui.nav_button("New here? Create an account", "views/register.py", icon=":material/person_add:", key="login_to_register")
    ui.nav_button("Administrator? Use admin login", "views/admin_login.py", icon=":material/admin_panel_settings:", key="login_to_admin")
