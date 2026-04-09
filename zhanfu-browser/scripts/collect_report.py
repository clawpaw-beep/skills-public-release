#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

CANONICAL_FAILURES = {
    "login_required",
    "verification_required",
    "timeout",
    "missing",
    "webdriver_unavailable",
    "connection_error",
    "extension_only",
    "no_dashboard",
    "extract_error",
    "extract_exception",
    "error",
    "empty",
}


def classify_error(stdout: str, stderr: str) -> str:
    text = f"{stdout}\n{stderr}".lower()
    if "请完成下列验证后继续:" in text or "captcha_present" in text or "verification_required" in text:
        return "verification_required"
    if "login_required" in text or "landed on login page" in text or "sign in" in text or "登录" in text:
        return "login_required"
    if "10061" in text or "connection refused" in text:
        return "connection_error"
    if "websocketdebuggerurl" in text or "failed to get real webdriver endpoint" in text:
        return "webdriver_unavailable"
    if "no non-extension page found" in text or "seller page never appeared" in text:
        return "missing"
    if "proxy authentication required" in text or "407" in text:
        return "proxy_auth_required"
    if "timeout" in text:
        return "timeout"
    if "playwright" in text and "connect" in text:
        return "connection_error"
    if "csv file not found" in text or "no such file" in text:
        return "missing"
    if "dashboard labels not found" in text:
        return "missing"
    if "traceback" in text:
        return "error"
    return "error"



def normalize_status(status: str | None, note: str = "", stdout: str = "", stderr: str = "") -> str:
    raw = (status or "").strip().lower()
    if raw in {"ok", "success"}:
        return "ok"
    if raw in CANONICAL_FAILURES:
        return raw
    if raw in {"webdriver_connection_refused", "webdriver_endpoint_unavailable", "playwright_connect_failed", "proxy_auth_required"}:
        return classify_error(stdout or raw, stderr)
    if raw in {"store_page_not_opened", "dashboard_not_ready", "input_missing", "unknown_error"}:
        return classify_error(stdout or raw, stderr)
    combined = f"{raw}\n{note}".lower()
    if "verification" in combined or "验证码" in combined or "验证" in combined:
        return "verification_required"
    if "login" in combined or "登录" in combined or "sign in" in combined:
        return "login_required"
    if "timeout" in combined:
        return "timeout"
    if "missing" in combined or "not found" in combined or "never appeared" in combined:
        return "missing"
    if raw:
        return raw
    return classify_error(stdout, stderr)



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
        stores = item.get("stores") or []
        if stores:
            batch_failed = False
            for store in stores:
                store_result = store.get("store_result") or {}
                key = normalize_status(
                    store.get("error_type") or store_result.get("final_failure_type") or store_result.get("status"),
                    note=store_result.get("note", ""),
                    stdout=store.get("stdout", ""),
                    stderr=store.get("stderr", ""),
                )
                if key != "ok":
                    batch_failed = True
                    report["error_buckets"][key] = report["error_buckets"].get(key, 0) + 1
            if batch_failed:
                report["sales_batch_failed"] += 1
        elif item.get("returncode") != 0:
            report["sales_batch_failed"] += 1
            key = classify_error(item.get("stdout", ""), item.get("stderr", ""))
            report["error_buckets"][key] = report["error_buckets"].get(key, 0) + 1

    for item in sales_retry_batches:
        key = normalize_status(item.get("error_type"), stdout=item.get("stdout", ""), stderr=item.get("stderr", ""))
        if key != "ok":
            report["sales_retry_failed"] += 1
            report["error_buckets"][key] = report["error_buckets"].get(key, 0) + 1

    return report
