#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any


def classify_error(stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "10061" in text or "connection refused" in text:
        return "webdriver_connection_refused"
    if "websocketdebuggerurl" in text or "failed to get real webdriver endpoint" in text:
        return "webdriver_endpoint_unavailable"
    if "proxy authentication required" in text or "407" in text:
        return "proxy_auth_required"
    if "timeout" in text:
        return "timeout"
    if "playwright" in text and "connect" in text:
        return "playwright_connect_failed"
    if "csv file not found" in text or "no such file" in text:
        return "input_missing"
    if "dashboard labels not found" in text:
        return "dashboard_not_ready"
    if "traceback" in text:
        return "python_exception"
    return "unknown_error"


def summarize_run(summary: dict[str, Any]) -> dict[str, Any]:
    sales_batches = summary.get("sales_batches", []) or []
    sales_retry_batches = summary.get("sales_retry_batches", []) or []
    fmcg_diagnose = summary.get("fmcg_diagnose")
    fmcg_order_lookup = summary.get("fmcg_order_lookup")

    report = {
        "stores_requested": summary.get("stores_requested", []),
        "sales_batch_total": len(sales_batches),
        "sales_batch_failed": 0,
        "sales_retry_total": len(sales_retry_batches),
        "sales_retry_failed": 0,
        "fmcg_diagnose_status": "skipped",
        "fmcg_order_lookup_status": "skipped",
        "error_buckets": {},
    }

    if fmcg_diagnose is not None:
        report["fmcg_diagnose_status"] = "ok" if fmcg_diagnose.get("returncode") == 0 else classify_error(
            fmcg_diagnose.get("stdout", ""), fmcg_diagnose.get("stderr", "")
        )

    if fmcg_order_lookup is not None:
        report["fmcg_order_lookup_status"] = "ok" if fmcg_order_lookup.get("returncode") == 0 else classify_error(
            fmcg_order_lookup.get("stdout", ""), fmcg_order_lookup.get("stderr", "")
        )

    for item in sales_batches:
        if item.get("returncode") != 0:
            report["sales_batch_failed"] += 1
            key = classify_error(item.get("stdout", ""), item.get("stderr", ""))
            report["error_buckets"][key] = report["error_buckets"].get(key, 0) + 1

    for item in sales_retry_batches:
        if item.get("returncode") not in (None, 0):
            report["sales_retry_failed"] += 1
            key = classify_error(item.get("stdout", ""), item.get("stderr", ""))
            report["error_buckets"][key] = report["error_buckets"].get(key, 0) + 1

    return report
