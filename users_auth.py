
"""
Authentication helpers backed by users_store.json.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from audit_logger import log_login_failed, log_login_success, log_logout
from user_management import (
    get_user_by_email,
    is_temp_password_required,
    list_users,
    resolve_user_access,
    set_last_login,
    verify_user_password,
)


def init_auth_state() -> None:
    defaults = {
        "logged_in": False,
        "user_email": "",
        "user_name": "",
        "user_role": "Executive Viewer",
        "user_permissions": {},
        "force_password_reset": False,
        "pending_password_reset_email": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _normalize_identifier(identifier: str) -> str:
    return (identifier or "").strip().lower()


def _find_user(identifier: str) -> Optional[Dict[str, Any]]:
    identifier = _normalize_identifier(identifier)
    if not identifier:
        return None

    user = get_user_by_email(identifier)
    if user:
        return user

    for candidate in list_users(active_only=False):
        username = (candidate.get("username", "") or "").strip().lower()
        if username and username == identifier:
            return candidate
    return None


def authenticate_user(identifier: str, password: str) -> Optional[Dict[str, Any]]:
    identifier = _normalize_identifier(identifier)
    password = (password or "").strip()

    if not identifier or not password:
        log_login_failed(identifier)
        return None

    user = _find_user(identifier)
    if not user or not bool(user.get("active", False)):
        log_login_failed(identifier)
        return None

    if not verify_user_password(user, password):
        log_login_failed(identifier)
        return None

    return user


def login_user(user: Dict[str, Any]) -> None:
    resolved_access = resolve_user_access(user.get("email", ""))
    email = user.get("email", "")

    st.session_state["logged_in"] = True
    st.session_state["user_email"] = email
    st.session_state["user_name"] = user.get("full_name", "")
    st.session_state["user_role"] = resolved_access.get("role", user.get("role", "Executive Viewer"))
    st.session_state["user_permissions"] = resolved_access
    st.session_state["force_password_reset"] = is_temp_password_required(email)
    st.session_state["pending_password_reset_email"] = email if st.session_state["force_password_reset"] else ""

    set_last_login(email)
    log_login_success(user)


def logout_user() -> None:
    log_logout(
        user_email=st.session_state.get("user_email", ""),
        user_name=st.session_state.get("user_name", ""),
        role=st.session_state.get("user_role", ""),
    )
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = ""
    st.session_state["user_name"] = ""
    st.session_state["user_role"] = "Executive Viewer"
    st.session_state["user_permissions"] = {}
    st.session_state["force_password_reset"] = False
    st.session_state["pending_password_reset_email"] = ""
