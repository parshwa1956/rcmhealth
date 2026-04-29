
"""
User Management backend helpers for Tuba RCM app.

This version adds:
- password hashing for local prototype use
- temporary password flow
- first-login password reset support
- user deletion
- migration of older users_store.json records
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from roles_access import ACCESS_MATRIX, ROLES, get_allowed_secondary_tabs, get_allowed_tabs

USER_STORE_PATH = Path("users_store.json")
DEFAULT_TEMP_PASSWORD = "Temp123!"

SEEDED_DEFAULT_PASSWORDS: Dict[str, str] = {
    "admin@tchealth.org": "Admin123!",
    "manager@tchealth.org": "Manager123!",
    "claims@tchealth.org": "Claims123!",
    "denials@tchealth.org": "Denials123!",
    "priorauth@tchealth.org": "PriorAuth123!",
    "integration@tchealth.org": "Integration123!",
    "executive@tchealth.org": "Executive123!",
}

DEFAULT_PHI_PERMISSIONS: Dict[str, bool] = {
    "can_view_phi": False,
    "can_export_phi": False,
    "can_view_patient_name": False,
    "can_view_visit_id": False,
    "can_view_mrn": False,
    "can_view_dob": False,
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _validate_role(role: str) -> None:
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def _default_overrides() -> Dict[str, Any]:
    return {
        "extra_tabs": [],
        "removed_tabs": [],
        "extra_secondary_tabs": [],
        "removed_secondary_tabs": [],
        "can_export_override": None,
        "can_manage_integration_override": None,
        "can_save_config_override": None,
        "phi_permissions": deepcopy(DEFAULT_PHI_PERMISSIONS),
    }


def _default_user_record(
    full_name: str,
    email: str,
    role: str,
    created_by: str = "System",
    department: str = "",
    password: str = DEFAULT_TEMP_PASSWORD,
    temp_password_required: bool = True,
) -> Dict[str, Any]:
    _validate_role(role)
    email = _normalize_email(email)
    return {
        "user_id": email,
        "username": email.split("@")[0],
        "full_name": (full_name or "").strip(),
        "email": email,
        "department": (department or "").strip(),
        "role": role,
        "active": True,
        "invite_status": "not_sent",
        "created_at": _now(),
        "created_by": created_by,
        "updated_at": _now(),
        "updated_by": created_by,
        "last_login": "",
        "password_hash": hash_password(password),
        "temp_password_required": bool(temp_password_required),
        "overrides": _default_overrides(),
    }


def default_store() -> Dict[str, Any]:
    seeded = [
        ("System Admin", "admin@tchealth.org", "Admin", "RCM", "Admin123!"),
        ("RCM Manager", "manager@tchealth.org", "RCM Manager", "RCM", "Manager123!"),
        ("Claims Analyst", "claims@tchealth.org", "Claims/Billing Analyst", "Claims", "Claims123!"),
        ("Denials Analyst", "denials@tchealth.org", "Denials Analyst", "Denials", "Denials123!"),
        ("Prior Auth User", "priorauth@tchealth.org", "Prior Auth User", "Prior Auth", "PriorAuth123!"),
        ("Integration Admin", "integration@tchealth.org", "Integration Admin", "IT", "Integration123!"),
        ("Executive Viewer", "executive@tchealth.org", "Executive Viewer", "Leadership", "Executive123!"),
    ]
    return {
        "users": [
            _default_user_record(
                full_name=name,
                email=email,
                role=role,
                created_by="System",
                department=dept,
                password=password,
                temp_password_required=False,
            )
            for name, email, role, dept, password in seeded
        ]
    }


def _normalize_user_record(user: Dict[str, Any]) -> Dict[str, Any]:
    email = _normalize_email(user.get("email", ""))
    if not email:
        return user

    user["user_id"] = email
    user["email"] = email
    user.setdefault("username", email.split("@")[0])
    user.setdefault("department", "")
    user.setdefault("role", "Executive Viewer")
    user.setdefault("active", True)
    user.setdefault("invite_status", "not_sent")
    user.setdefault("created_at", _now())
    user.setdefault("created_by", "System")
    user.setdefault("updated_at", user.get("created_at", _now()))
    user.setdefault("updated_by", user.get("created_by", "System"))
    user.setdefault("last_login", "")
    user.setdefault("overrides", _default_overrides())
    user["overrides"].setdefault("phi_permissions", deepcopy(DEFAULT_PHI_PERMISSIONS))
    for key, default in _default_overrides().items():
        user["overrides"].setdefault(key, deepcopy(default))

    if "password_hash" not in user or not user.get("password_hash"):
        seeded_password = SEEDED_DEFAULT_PASSWORDS.get(email)
        if seeded_password:
            user["password_hash"] = hash_password(seeded_password)
            user["temp_password_required"] = False
        else:
            user["password_hash"] = hash_password(DEFAULT_TEMP_PASSWORD)
            user.setdefault("temp_password_required", True)
    else:
        user.setdefault("temp_password_required", False)

    return user


def ensure_user_store() -> None:
    if not USER_STORE_PATH.exists():
        USER_STORE_PATH.write_text(json.dumps(default_store(), indent=2), encoding="utf-8")


def load_user_store() -> Dict[str, Any]:
    ensure_user_store()
    raw = USER_STORE_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        store = default_store()
        save_user_store(store)
        return store
    try:
        store = json.loads(raw)
    except json.JSONDecodeError:
        store = default_store()
        save_user_store(store)
        return store

    store.setdefault("users", [])
    normalized_users = []
    changed = False
    for user in store["users"]:
        before = json.dumps(user, sort_keys=True)
        norm = _normalize_user_record(user)
        after = json.dumps(norm, sort_keys=True)
        normalized_users.append(norm)
        if before != after:
            changed = True
    store["users"] = normalized_users
    if changed:
        save_user_store(store)
    return store


def save_user_store(store: Dict[str, Any]) -> None:
    USER_STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def list_users(active_only: bool = False) -> List[Dict[str, Any]]:
    users = load_user_store().get("users", [])
    return [u for u in users if bool(u.get("active", False))] if active_only else users


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    email = _normalize_email(email)
    for user in load_user_store().get("users", []):
        if _normalize_email(user.get("email", "")) == email:
            return user
    return None


def add_user(
    full_name: str,
    email: str,
    role: str,
    created_by: str,
    department: str = "",
) -> Dict[str, Any]:
    email = _normalize_email(email)
    if not email:
        raise ValueError("Email is required.")
    if get_user_by_email(email):
        raise ValueError("User already exists.")
    user = _default_user_record(
        full_name=full_name,
        email=email,
        role=role,
        created_by=created_by,
        department=department,
        password=DEFAULT_TEMP_PASSWORD,
        temp_password_required=True,
    )
    store = load_user_store()
    store["users"].append(user)
    save_user_store(store)
    return user


def delete_user(email: str) -> None:
    email = _normalize_email(email)
    store = load_user_store()
    users_before = len(store["users"])
    store["users"] = [u for u in store["users"] if _normalize_email(u.get("email", "")) != email]
    if len(store["users"]) == users_before:
        raise ValueError("User not found.")
    save_user_store(store)


def update_user_role(email: str, new_role: str, updated_by: str) -> Dict[str, Any]:
    _validate_role(new_role)
    email = _normalize_email(email)
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            user["role"] = new_role
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def set_user_active(email: str, active: bool, updated_by: str) -> Dict[str, Any]:
    email = _normalize_email(email)
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            user["active"] = bool(active)
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def set_last_login(email: str) -> None:
    email = _normalize_email(email)
    store = load_user_store()
    changed = False
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            user["last_login"] = _now()
            user["updated_at"] = _now()
            changed = True
            break
    if changed:
        save_user_store(store)


def set_invite_status(email: str, invite_status: str, updated_by: str) -> Dict[str, Any]:
    allowed = {"not_sent", "sent", "accepted", "expired"}
    if invite_status not in allowed:
        raise ValueError(f"Invalid invite status: {invite_status}")
    email = _normalize_email(email)
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            user["invite_status"] = invite_status
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def update_user_password(email: str, new_password: str, updated_by: str) -> Dict[str, Any]:
    email = _normalize_email(email)
    new_password = (new_password or "").strip()
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            user["password_hash"] = hash_password(new_password)
            user["temp_password_required"] = False
            user["invite_status"] = "accepted"
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def verify_user_password(user: Dict[str, Any], password: str) -> bool:
    expected_hash = (user.get("password_hash", "") or "").strip()
    return bool(expected_hash) and hash_password((password or "").strip()) == expected_hash


def is_temp_password_required(email: str) -> bool:
    user = get_user_by_email(email)
    return bool(user and user.get("temp_password_required", False))


def update_user_overrides(
    email: str,
    updated_by: str,
    *,
    extra_tabs: Optional[List[str]] = None,
    removed_tabs: Optional[List[str]] = None,
    extra_secondary_tabs: Optional[List[str]] = None,
    removed_secondary_tabs: Optional[List[str]] = None,
    can_export_override: Optional[bool] = None,
    can_manage_integration_override: Optional[bool] = None,
    can_save_config_override: Optional[bool] = None,
) -> Dict[str, Any]:
    email = _normalize_email(email)
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            overrides = user.setdefault("overrides", _default_overrides())
            if extra_tabs is not None:
                overrides["extra_tabs"] = sorted(set(extra_tabs))
            if removed_tabs is not None:
                overrides["removed_tabs"] = sorted(set(removed_tabs))
            if extra_secondary_tabs is not None:
                overrides["extra_secondary_tabs"] = sorted(set(extra_secondary_tabs))
            if removed_secondary_tabs is not None:
                overrides["removed_secondary_tabs"] = sorted(set(removed_secondary_tabs))
            if can_export_override is not None:
                overrides["can_export_override"] = bool(can_export_override)
            if can_manage_integration_override is not None:
                overrides["can_manage_integration_override"] = bool(can_manage_integration_override)
            if can_save_config_override is not None:
                overrides["can_save_config_override"] = bool(can_save_config_override)
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def update_user_phi_permissions(
    email: str,
    updated_by: str,
    *,
    can_view_phi: Optional[bool] = None,
    can_export_phi: Optional[bool] = None,
    can_view_patient_name: Optional[bool] = None,
    can_view_visit_id: Optional[bool] = None,
    can_view_mrn: Optional[bool] = None,
    can_view_dob: Optional[bool] = None,
) -> Dict[str, Any]:
    email = _normalize_email(email)
    store = load_user_store()
    for user in store["users"]:
        if _normalize_email(user.get("email", "")) == email:
            overrides = user.setdefault("overrides", _default_overrides())
            phi = overrides.setdefault("phi_permissions", deepcopy(DEFAULT_PHI_PERMISSIONS))
            updates = {
                "can_view_phi": can_view_phi,
                "can_export_phi": can_export_phi,
                "can_view_patient_name": can_view_patient_name,
                "can_view_visit_id": can_view_visit_id,
                "can_view_mrn": can_view_mrn,
                "can_view_dob": can_view_dob,
            }
            for key, value in updates.items():
                if value is not None:
                    phi[key] = bool(value)
            user["updated_at"] = _now()
            user["updated_by"] = updated_by
            save_user_store(store)
            return user
    raise ValueError("User not found.")


def _apply_list_overrides(base_items: List[str], extra_items: List[str], removed_items: List[str]) -> List[str]:
    resolved = list(base_items)
    for item in extra_items:
        if item not in resolved:
            resolved.append(item)
    return [item for item in resolved if item not in removed_items]


def resolve_user_access(email: str) -> Dict[str, Any]:
    user = get_user_by_email(email)
    if not user:
        raise ValueError("User not found.")

    role = user.get("role", "Executive Viewer")
    role_config = ACCESS_MATRIX.get(role, ACCESS_MATRIX["Executive Viewer"])
    overrides = user.get("overrides", _default_overrides())

    primary_tabs = _apply_list_overrides(
        list(get_allowed_tabs(role)),
        overrides.get("extra_tabs", []),
        overrides.get("removed_tabs", []),
    )
    secondary_tabs = _apply_list_overrides(
        list(get_allowed_secondary_tabs(role)),
        overrides.get("extra_secondary_tabs", []),
        overrides.get("removed_secondary_tabs", []),
    )

    can_export = role_config.get("can_export", False)
    can_manage_integration = role_config.get("can_manage_integration", False)
    can_save_config = role_config.get("can_save_config", False)

    if overrides.get("can_export_override") is not None:
        can_export = bool(overrides["can_export_override"])
    if overrides.get("can_manage_integration_override") is not None:
        can_manage_integration = bool(overrides["can_manage_integration_override"])
    if overrides.get("can_save_config_override") is not None:
        can_save_config = bool(overrides["can_save_config_override"])

    phi_permissions = deepcopy(DEFAULT_PHI_PERMISSIONS)
    phi_permissions.update(overrides.get("phi_permissions", {}))

    return {
        "email": user.get("email", ""),
        "full_name": user.get("full_name", ""),
        "role": role,
        "active": bool(user.get("active", False)),
        "primary_tabs": primary_tabs,
        "secondary_tabs": secondary_tabs,
        "can_export": bool(can_export),
        "can_manage_integration": bool(can_manage_integration),
        "can_save_config": bool(can_save_config),
        "phi_permissions": phi_permissions,
        "temp_password_required": bool(user.get("temp_password_required", False)),
    }


def apply_phi_column_filter(df_columns: List[str], phi_permissions: Dict[str, bool]) -> List[str]:
    blocked_columns = set()
    if not phi_permissions.get("can_view_phi", False):
        blocked_columns.update({"patient_name", "visit_id", "mrn", "dob"})
    else:
        if not phi_permissions.get("can_view_patient_name", False):
            blocked_columns.add("patient_name")
        if not phi_permissions.get("can_view_visit_id", False):
            blocked_columns.add("visit_id")
        if not phi_permissions.get("can_view_mrn", False):
            blocked_columns.add("mrn")
        if not phi_permissions.get("can_view_dob", False):
            blocked_columns.add("dob")
    return [col for col in df_columns if col not in blocked_columns]
