"""Optional external parser stub.
Replace these functions with your real parser logic.
"""
from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd


def parse_835(raw_bytes: bytes, filename: str | None = None) -> Dict[str, Any]:
    return {
        "file_name": filename or "unknown_835",
        "file_type": "835",
        "claims": [],
        "service_lines": [],
        "metrics": {},
    }


def parse_837p(raw_bytes: bytes, filename: str | None = None) -> Dict[str, Any]:
    return {
        "file_name": filename or "unknown_837p",
        "file_type": "837P",
        "claims": [],
        "service_lines": [],
        "metrics": {},
    }


def parse_837i(raw_bytes: bytes, filename: str | None = None) -> Dict[str, Any]:
    return {
        "file_name": filename or "unknown_837i",
        "file_type": "837I",
        "claims": [],
        "service_lines": [],
        "metrics": {},
    }


def claims_to_dataframe(parsed_results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in parsed_results:
        for claim in item.get("claims", []) or []:
            row = dict(claim)
            row.setdefault("file_name", item.get("file_name", ""))
            row.setdefault("file_type", item.get("file_type", ""))
            rows.append(row)
    return pd.DataFrame(rows)


def service_lines_to_dataframe(parsed_results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in parsed_results:
        for line in item.get("service_lines", []) or []:
            row = dict(line)
            row.setdefault("file_name", item.get("file_name", ""))
            row.setdefault("file_type", item.get("file_type", ""))
            rows.append(row)
    return pd.DataFrame(rows)


def upload_summary_to_dataframe(parsed_results: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in parsed_results:
        m = item.get("metrics", {}) or {}
        rows.append(
            {
                "File Name": item.get("file_name", ""),
                "Detected Type": item.get("file_type", "Unknown"),
                "Claims Parsed": m.get("claim_count", len(item.get("claims", []) or [])),
                "Service Lines Parsed": m.get("service_line_count", len(item.get("service_lines", []) or [])),
                "Billed Amount": m.get("billed_amount", 0.0),
                "Paid Amount": m.get("paid_amount", 0.0),
                "Denied Amount": m.get("denied_amount", 0.0),
                "Recoverable Amount": m.get("recoverable_amount", 0.0),
            }
        )
    return pd.DataFrame(rows)


def executive_metrics_to_dataframe(parsed_results: List[Dict[str, Any]]) -> pd.DataFrame:
    summary = upload_summary_to_dataframe(parsed_results)
    if summary.empty:
        return pd.DataFrame(columns=["Metric", "Value"])
    return pd.DataFrame(
        {
            "Metric": [
                "Files Processed",
                "Claims Parsed",
                "Service Lines Parsed",
                "Total Billed",
                "Total Paid",
                "Total Denied",
                "Total Recoverable",
            ],
            "Value": [
                len(summary),
                int(pd.to_numeric(summary["Claims Parsed"], errors="coerce").fillna(0).sum()),
                int(pd.to_numeric(summary["Service Lines Parsed"], errors="coerce").fillna(0).sum()),
                float(pd.to_numeric(summary["Billed Amount"], errors="coerce").fillna(0).sum()),
                float(pd.to_numeric(summary["Paid Amount"], errors="coerce").fillna(0).sum()),
                float(pd.to_numeric(summary["Denied Amount"], errors="coerce").fillna(0).sum()),
                float(pd.to_numeric(summary["Recoverable Amount"], errors="coerce").fillna(0).sum()),
            ],
        }
    )
