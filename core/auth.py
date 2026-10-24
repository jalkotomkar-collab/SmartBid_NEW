"""Authentication and session helpers (PBKDF2 hashing from the standard library)."""
import hashlib
import hmac
import os
import re
import secrets
import time

import streamlit as st

from . import db
from .config import (
    DEV_ADMIN_EMAIL,
    DEV_ADMIN_PASSWORD,
    DEV_ADMIN_USERNAME,
    get_secret,
)

ITERATIONS = 200_000
MAX_ATTEMPTS = 5
LOCK_SECONDS = 60

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------- hashing
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


def password_problem(password: str) -> str | None:
    if len(password) < 8:
        return "Use at least 8 characters for the password."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Include at least one letter and one number in the password."
    return None


# ------------------------------------------------------------------- accounts
def _create_user(full_name, username, email, password, role="user") -> int:
    pw_hash, salt = hash_password(password)
    return db.insert(
        "INSERT INTO users (full_name, username, email, password_hash, salt, role) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (full_name, username, email, pw_hash, salt, role),
    )


def register_user(full_name, username, email, password, confirm):
    """Validate and create a user account. Returns (ok, user_dict | error_message)."""
    full_name, username, email = (full_name or "").strip(), (username or "").strip(), (email or "").strip()
    if len(full_name) < 2:
        return False, "Enter your full name."
    if not USERNAME_RE.match(username):
        return False, "Usernames are 3 to 30 characters: letters, numbers, dots and underscores."
    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address."
    problem = password_problem(password or "")
    if problem:
        return False, problem
    if password != confirm:
        return False, "The two passwords do not match."
    if db.fetch_one("SELECT 1 AS x FROM users WHERE username = ?", (username,)):
        return False, "That username is already taken."
    if db.fetch_one("SELECT 1 AS x FROM users WHERE email = ?", (email,)):
        return False, "An account with that email already exists."
    user_id = _create_user(full_name, username, email, password)
    return True, get_user(user_id)


def get_user(user_id: int):
    return db.fetch_one(
        "SELECT id, full_name, username, email, role, is_active, created_at FROM users WHERE id = ?",
        (user_id,),
    )


def change_password(user_id: int, current: str, new: str, confirm: str):
    row = db.fetch_one("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
    if not row or not verify_password(current or "", row["password_hash"], row["salt"]):
        return False, "Your current password is incorrect."
    problem = password_problem(new or "")
    if problem:
        return False, problem
    if new != confirm:
        return False, "The two new passwords do not match."
    pw_hash, salt = hash_password(new)
    db.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pw_hash, salt, user_id))
    return True, "Password updated."


def _is_local_request() -> bool:
    """True only when the page was opened through localhost.

    The built-in development admin (see config.py) is a convenience for running the
    app on your own computer. It must never be created on a public deployment, so it
    is only allowed when the browser reached the app via localhost.
    Set ALLOW_DEV_ADMIN=1 in the environment to override this (not recommended).
    """
    if os.environ.get("ALLOW_DEV_ADMIN") == "1":
        return True
    try:
        raw = (st.context.headers.get("Host") or "").strip().lower()
    except Exception:
        return False
    host = raw[1:raw.index("]")] if raw.startswith("[") and "]" in raw else raw.split(":")[0]
    return host in ("localhost", "127.0.0.1", "::1")


def ensure_admin() -> str | None:
    """Create the first admin account if none exists.

    Returns a status string: 'dev' when the local development account was created,
    'missing' when there is no admin and no way to create one safely (no admin secrets
    set, and the app is hosted or not opened via localhost), otherwise None.
    """
    if db.fetch_one("SELECT 1 AS x FROM users WHERE role = 'admin' LIMIT 1"):
        return None
    username = get_secret("ADMIN_USERNAME")
    password = get_secret("ADMIN_PASSWORD")
    email = get_secret("ADMIN_EMAIL", "admin@example.com")
    status = None
    if not (username and password):
        if db.using_hosted_db() or not _is_local_request():
            return "missing"
        username, password, email, status = DEV_ADMIN_USERNAME, DEV_ADMIN_PASSWORD, DEV_ADMIN_EMAIL, "dev"
    try:
        _create_user("Administrator", username, email, password, role="admin")
    except Exception:
        # Another session created it first, or the username/email was taken.
        return None
    return status


# -------------------------------------------------------------------- sessions
def current_user():
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return current_user() is not None


def is_admin() -> bool:
    user = current_user()
    return bool(user and user["role"] == "admin")


def login(user: dict) -> None:
    st.session_state["user"] = {
        "id": user["id"],
        "full_name": user["full_name"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
    }
    st.session_state.pop("_lock_until", None)
    st.session_state["_failed"] = 0


def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_login() -> dict:
    user = current_user()
    if not user:
        st.warning("Log in to see this page.")
        if st.button("Go to log in", key="require_login_btn", icon=":material/login:"):
            st.switch_page("views/login.py")
        st.stop()
    return user


def require_admin() -> dict:
    user = require_login()
    if user["role"] != "admin":
        st.error("This page is for administrators only.")
        st.stop()
    return user


# --------------------------------------------------------------- login attempts
def _seconds_locked() -> int:
    return max(0, int(st.session_state.get("_lock_until", 0) - time.time()))


def _register_failure() -> None:
    failed = st.session_state.get("_failed", 0) + 1
    st.session_state["_failed"] = failed
    if failed >= MAX_ATTEMPTS:
        st.session_state["_lock_until"] = time.time() + LOCK_SECONDS
        st.session_state["_failed"] = 0


def attempt_login(identifier: str, password: str, role: str):
    """Check credentials for the given login page ('user' or 'admin').

    Returns (True, user_dict) or (False, error_message).
    """
    wait = _seconds_locked()
    if wait:
        return False, f"Too many failed attempts. Try again in {wait} seconds."
    identifier = (identifier or "").strip()
    if not identifier or not password:
        return False, "Enter your username or email and your password."

    row = db.fetch_one("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    if not row or not verify_password(password, row["password_hash"], row["salt"]):
        _register_failure()
        return False, "Incorrect username or password."
    if not row["is_active"]:
        return False, "This account has been deactivated. Contact the administrator."
    if role == "admin" and row["role"] != "admin":
        return False, "This account does not have administrator access."
    if role == "user" and row["role"] == "admin":
        return False, "This is an administrator account. Use Admin login instead."
    return True, get_user(row["id"])
