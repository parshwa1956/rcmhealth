"""
Role-based access helpers for Tuba RCM app.

Phase 2 scope:
- central role definitions
- module/tab visibility
- export permissions
- Integration Command Center permissions

This file is intentionally simple so it can be plugged into the current
single-file Streamlit app without changing the UI design.
"""

from typing import Dict, List

ROLES: List[str] = [
    "Admin",
    "Executive Viewer",
    "RCM Manager",
    "Claims/Billing Analyst",
    "Denials Analyst",
    "Prior Auth User",
    "Integration Admin",
]

ACCESS_MATRIX: Dict[str, Dict[str, object]] = {
    "Admin": {
        "tabs": [
            "Executive",
            "Claims",
            "Assurance",
            "DNFB Executive",
            "Recoverable",
            "Prior Auths",
            "Denials",
            "Integration Hub",
        ],
        "secondary_tabs": [
            "Action Center",
            "Payer Focus",
            "Appeals",
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": True,
        "can_save_config": True,
    },
    "Executive Viewer": {
        "tabs": [
            "Executive",
            "DNFB Executive",
        ],
        "secondary_tabs": [],
        "can_export": False,
        "can_manage_integration": False,
        "can_save_config": False,
    },
    "RCM Manager": {
        "tabs": [
            "Executive",
            "Claims",
            "Assurance",
            "DNFB Executive",
            "Recoverable",
            "Prior Auths",
            "Denials",
        ],
        "secondary_tabs": [
            "Action Center",
            "Payer Focus",
            "Appeals",
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": False,
        "can_save_config": False,
    },
    "Claims/Billing Analyst": {
        "tabs": [
            "Claims",
            "Assurance",
            "Recoverable",
        ],
        "secondary_tabs": [
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": False,
        "can_save_config": False,
    },
    "Denials Analyst": {
        "tabs": [
            "Denials",
            "Assurance",
        ],
        "secondary_tabs": [
            "Action Center",
            "Payer Focus",
            "Appeals",
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": False,
        "can_save_config": False,
    },
    "Prior Auth User": {
        "tabs": [
            "Prior Auths",
        ],
        "secondary_tabs": [
            "Action Center",
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": False,
        "can_save_config": False,
    },
    "Integration Admin": {
        "tabs": [
            "Integration Hub",
        ],
        "secondary_tabs": [
            "Exports",
        ],
        "can_export": True,
        "can_manage_integration": True,
        "can_save_config": True,
    },
}


def _get_role_config(role: str) -> Dict[str, object]:
    """Return role config, defaulting safely to Executive Viewer."""
    return ACCESS_MATRIX.get(role, ACCESS_MATRIX["Executive Viewer"])


def get_allowed_tabs(role: str) -> List[str]:
    """Primary sidebar tabs allowed for a role."""
    return list(_get_role_config(role).get("tabs", []))


def get_allowed_secondary_tabs(role: str) -> List[str]:
    """Operational/secondary sidebar tabs allowed for a role."""
    return list(_get_role_config(role).get("secondary_tabs", []))


def can_export(role: str) -> bool:
    """Whether the role can see/use exports/download actions."""
    return bool(_get_role_config(role).get("can_export", False))


def can_manage_integration(role: str) -> bool:
    """Whether the role can edit Integration Command Center fields."""
    return bool(_get_role_config(role).get("can_manage_integration", False))


def can_save_config(role: str) -> bool:
    """Whether the role can save production-impacting configuration."""
    return bool(_get_role_config(role).get("can_save_config", False))


def has_tab_access(role: str, tab_name: str) -> bool:
    """Check access for any tab name."""
    return tab_name in get_allowed_tabs(role) or tab_name in get_allowed_secondary_tabs(role)


def is_read_only_integration(role: str) -> bool:
    """Useful helper for showing Integration Hub in read-only mode."""
    return has_tab_access(role, "Integration Hub") and not can_manage_integration(role)


def get_default_role() -> str:
    """Recommended default role for testing in the app."""
    return "Admin"