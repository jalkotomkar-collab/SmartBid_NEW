"""Administrator login."""
import streamlit as st

from core import auth, ui

form_col = ui.auth_layout("auth_admin.jpg")

with form_col:
    ui.form_heading("Admin login", "For marketplace administrators only.")

    status = st.session_state.get("admin_status")
    if status == "missing":
        st.warning(
            "No administrator account exists yet. Add ADMIN_USERNAME and ADMIN_PASSWORD to the "
            "app secrets (see the README), then restart the app. The built-in test admin is only "
            "created when the app is opened at localhost."
        )
    elif status == "dev":
        st.info("Local development account in use. See the README for its username and password, and change it before deploying.")

    with st.form("admin_login_form"):
        identifier = st.text_input("Admin username or email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Log in as admin", type="primary", icon=":material/admin_panel_settings:", width="stretch"
        )
    if submitted:
        ok, result = auth.attempt_login(identifier, password, role="admin")
        if ok:
            auth.login(result)
            st.rerun()
        else:
            st.error(result)

    ui.nav_button("Not an administrator? Member login", "views/login.py", icon=":material/login:", key="adm_to_login")
