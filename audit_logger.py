"""
Simple audit logger for Tuba RCM app.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

AUDIT_LOG_PATH = Path("audit_log.jsonl")


def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_audit_event(
    action: str,
    status: str = "success",
    user_email: str = "",
    user_name: str = "",
    role: str = "",
    module: str = "",
    details: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "timestamp": get_timestamp(),
        "action": action,
        "status": status,
        "user_email": user_email,
        "user_name": user_name,
        "role": role,
        "module": module,
        "details": details,
    }
    if extra:
        event["extra"] = extra
    return event


def write_audit_event(event: Dict[str, Any]) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_event(
    action: str,
    status: str = "success",
    user_email: str = "",
    user_name: str = "",
    role: str = "",
    module: str = "",
    details: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    write_audit_event(build_audit_event(action, status, user_email, user_name, role, module, details, extra))


def log_login_success(user: Dict[str, Any]) -> None:
    log_event(
        action="login_success",
        status="success",
        user_email=user.get("email", ""),
        user_name=user.get("full_name", ""),
        role=user.get("role", ""),
        module="Authentication",
        details="User signed in successfully.",
    )


def log_login_failed(identifier: str) -> None:
    log_event(
        action="login_failed",
        status="failed",
        user_email=(identifier or "").strip(),
        module="Authentication",
        details="Failed login attempt.",
    )


def log_logout(user_email: str = "", user_name: str = "", role: str = "") -> None:
    log_event(
        action="logout",
        status="success",
        user_email=user_email,
        user_name=user_name,
        role=role,
        module="Authentication",
        details="User logged out.",
    )
