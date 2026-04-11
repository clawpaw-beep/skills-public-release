#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

from zhanfu_runtime import (
    close_browser,
    connect_browser,
    diagnose_store_entry,
    ensure_zhanfu_ready,
    get_browser_list,
    pick_best_tab,
    tab_body_text,
    tab_url,
    tab_title,
    classify_page,
)

LOGIN_HINTS = ["login", "登录", "sign in", "sign-in", "log in"]
METRIC_LABELS = {
    "gmv": ["GMV"],
    "customers": ["Customers", "客户数"],
    "sku_orders": ["SKU orders", "订单数"],
    "visitors": ["Visitors", "页面浏览数", "访客数"],
}


def parse_dashboard_lines(text: str) -> dict[str, str] | None:
    """
    Parse KPI metrics from dashboard page text using regex.
    Falls back to row-scan if regex fails.

    Handles:
    - GMV:  $12,345.67  12.3%
    - 订单数:  123  12.3%
    - Customers / 客户数
    - Visitors / 访客数 / 页面浏览数
    """
    if not any(label in text for labels in METRIC_LABELS.values() for label in labels):
        return None

    metrics: dict[str, str] = {}

    # Regex-based extraction: label on its own line, value + change on following lines
    # Patterns:
    #   GMV\n$1,234.56\n12.3%
    #   Customers\n5,288\n6.14%
    for key, labels in METRIC_LABELS.items():
        for label in labels:
            # Try: label line immediately followed by a number/currency line
            pattern = re.escape(label) + r"\s*\n\s*([^\n]+)"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                raw_value = m.group(1).strip()
                # Try to extract number + optional % change
                num_m = re.search(r'([^\d]*[\d,]+\.?\d*[^\s,%]*)(?:\s+([\d.]+%))?', raw_value)
                if num_m:
                    value = num_m.group(1).strip()
                    change = num_m.group(2).strip() if num_m.group(2) else ""
                    if value:
                        metrics[key] = value
                        metrics[f"{key}_change"] = change
                        break
        if key in metrics:
            continue

        # Fallback: row-scan (original logic) for this metric only
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if line.strip() not in labels:
                continue
            # Value is next non-empty line, change is line after that
            value, change = "", ""
            for offset in range(1, 5):
                if idx + offset >= len(lines):
                    break
                candidate = lines[idx + offset].strip()
                if not candidate:
                    continue
                if not value:
                    if re.search(r'[\d,]+\.?\d*', candidate):
                        value = candidate
                elif not change and re.search(r'%', candidate):
                    change = candidate
                    break
            if value:
                metrics[key] = value
                metrics[f"{key}_change"] = change
                break

    return metrics if metrics else None


def try_close_verification(tab, max_retries: int = 2) -> dict[str, object]:
    """
    Attempt to close dismiss a TikTok verification/security challenge overlay.
    Tries: X button, 关闭/Close/Cancel buttons, refreshing the page.

    Returns:
        {"closed": True/False, "attempts": N, "text_after": ...}
    """
    text_before = tab_body_text(tab)

    close_strategies = [
        lambda: tab.ele("@class:modal__close-btn", timeout=2),
        lambda: tab.ele("text:关闭", timeout=2),
        lambda: tab.ele("text:Close", timeout=2),
        lambda: tab.ele("text:取消", timeout=2),
        lambda: tab.ele("text:Cancel", timeout=2),
        lambda: tab.ele("@class:sec Verify-svg", timeout=2),
        lambda: tab.ele("@class:cap-back", timeout=2),
    ]

    for attempt in range(1, max_retries + 1):
        for strategy in close_strategies:
            try:
                ele = strategy()
                if ele:
                    ele.click()
                    time.sleep(3)
                    text_after = tab_body_text(tab)
                    # If the verification text is gone, we're good
                    verify_indicators = ["验证", "安全验证", "captcha", "challenge", "账户异常"]
                    if not any(v in text_after for v in verify_indicators):
                        return {"closed": True, "attempts": attempt, "text_before": text_before[:200], "text_after": text_after[:200]}
            except Exception:
                pass

        # Try refreshing the page as last resort
        try:
            tab.refresh()
            time.sleep(4)
        except Exception:
            pass

    text_after = tab_body_text(tab)
    verify_still_present = any(v in text_after for v in ["验证", "安全验证", "captcha", "challenge", "账户异常"])
    return {
        "closed": not verify_still_present,
        "attempts": max_retries * len(close_strategies),
        "text_before": text_before[:200],
        "text_after": text_after[:200],
    }


def try_click_today(tab, max_retries: int = 3) -> dict[str, object]:
    """
    Attempt to switch the dashboard to 'Today' view.

    TikTok Seller Center uses a two-step dropdown:
    1. Click the 'Last 7 days' / '今天' button to open the dropdown
    2. Click 'Today' option inside the dropdown

    Returns:
        {"clicked": True/False, "attempts": N, "text_before": ..., "text_after": ...}
    """
    text_before = tab_body_text(tab)

    for attempt in range(1, max_retries + 1):
        dropdown_opened = False

        # Step 1: Open the dropdown by clicking the 'Last 7 days' / '今天' button
        for dropdown_label in ["Last 7 days", "今天"]:
            try:
                dropdown_ele = tab.ele(f"text:{dropdown_label}", timeout=3)
                if dropdown_ele:
                    dropdown_ele.click()
                    time.sleep(2)  # Wait for dropdown animation
                    dropdown_opened = True
                    break
            except Exception:
                pass

        if not dropdown_opened:
            time.sleep(2)
            continue

        # Step 2: Click 'Today' inside the dropdown
        for today_label in ["Today", "今天"]:
            try:
                today_ele = tab.ele(f"text:{today_label}", timeout=3)
                if today_ele:
                    today_ele.click()
                    time.sleep(4)
                    text_after = tab_body_text(tab)
                    if text_after != text_before:
                        return {
                            "clicked": True,
                            "attempts": attempt,
                            "text_before": text_before[:200],
                            "text_after": text_after[:200],
                        }
            except Exception:
                pass

        time.sleep(2)

    text_after = tab_body_text(tab)
    has_today_anchor = "今天" in text_after or ("Today" in text_after and "Last 7" not in text_after)
    return {
        "clicked": has_today_anchor,
        "attempts": max_retries,
        "text_before": text_before[:200],
        "text_after": text_after[:200],
        "error": "could not switch to today filter after 3 attempts" if not has_today_anchor else "",
    }


def extract_sales_metrics(browser) -> dict[str, object]:
    diagnosis = diagnose_store_entry(browser, try_open_store=True, try_goto_home=True)
    tab, score = pick_best_tab(browser)
    if tab is None:
        return {"status": "error", "note": "没有找到可用页面标签", "diagnosis": diagnosis}

    text = tab_body_text(tab)
    click_result = try_click_today(tab)
    text = tab_body_text(tab)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    metrics = parse_dashboard_lines(text)
    lower = text.lower()
    page_url = tab_url(tab)
    page_title = tab_title(tab)
    page_kind = classify_page(page_url, page_title, text)

    result: dict[str, object] = {
        "status": "ok",
        "page_url": page_url,
        "page_title": page_title,
        "page_kind": page_kind,
        "page_score": score,
        "raw_text_excerpt": "\n".join(lines[:120]),
        "diagnosis": diagnosis,
        "today_filter": click_result,
    }

    if any(hint in lower for hint in LOGIN_HINTS):
        result["status"] = "login_required"
        result["note"] = "店铺已打开，但当前落在登录页，需要先手动登录"
        return result

    # Detect verification/security challenge page
    verify_hints = ["验证", "安全验证", " captcha", "challenge", "安全检查", "账户异常", "账号异常"]
    is_verification = page_kind == "verification" or any(h in lower for h in verify_hints)

    if is_verification:
        # Try to close the verification overlay and retry
        close_result = try_close_verification(tab)
        # Re-read metrics after closing
        text = tab_body_text(tab)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        metrics = parse_dashboard_lines(text)
        page_kind = classify_page(tab_url(tab), tab_title(tab), text)
        lower = text.lower()
        is_verification = page_kind == "verification" or any(h in lower for h in verify_hints)
        result["today_filter"] = try_click_today(tab)
        if is_verification:
            result["status"] = "verification_required"
            result["note"] = "页面持续在验证码/安全验证，已尽力关闭但仍存在"
            result["verification_close_result"] = close_result
            return result
        result["verification_close_result"] = close_result
        # Verification gone, continue with refreshed metrics

    if metrics is None:
        result["status"] = "no_dashboard"
        result["note"] = "已进入 seller 页面，但没读到标准经营数据区块"
        return result

    # Verify we actually got today's data, not 7-day data
    gmv_text = metrics.get("gmv", "")
    gmv_val = re.sub(r'[^\d.]', '', gmv_text)
    if not gmv_val:
        result["note"] = "WARNING: GMV value is empty — today filter may have failed"
    else:
        result["note"] = ""

    result.update(metrics)
    return result


def _save_diagnosis(store_id: int, attempt_records: list, extracted: dict) -> Path:
    """Save full diagnosis records to workspace for post-mortem analysis."""
    diag_dir = Path.home() / ".openclaw" / "workspace" / "zhanfu_diagnosis"
    diag_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = diag_dir / f"diagnosis_{store_id}_{ts}.json"
    payload = {
        "store_id": store_id,
        "ts": ts,
        "attempt_records": attempt_records,
        "extracted": extracted,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def flush_results(rows: list[dict[str, object]], output_json: Path, output_csv: Path) -> None:
    output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        fieldnames = [
            "store_id", "store_name", "platform_name", "ip_address", "status", "note",
            "page_url", "page_title", "page_kind", "gmv", "gmv_change", "customers", "customers_change",
            "sku_orders", "sku_orders_change", "visitors", "visitors_change", "cdp_port", "ws_endpoint",
        ]
        with output_csv.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})


def collect_store(store_id: int, output_dir: Path, flush_every: int = 1, max_attempts: int = 2, keep_open_on_success: bool = False):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"sales_store_{store_id}.json"
    output_csv = output_dir / f"sales_store_{store_id}.csv"
    rows: list[dict[str, object]] = []

    store_meta = next((item for item in get_browser_list() if int(item.get("mall_id", 0)) == int(store_id)), {})
    attempts: list[dict[str, object]] = []
    extracted: dict[str, object] | None = None
    last_ready = None

    for attempt in range(1, max_attempts + 1):
        ensure = ensure_zhanfu_ready(store_id, startup_wait=60, cdp_wait=120, kill_first=False)
        attempt_record = {
            "attempt": attempt,
            "webdriver_ready": bool(ensure.ready),
            "webdriver_error": ensure.error,
        }
        if not ensure.ready:
            attempt_record["status"] = "webdriver_unavailable"
            attempts.append(attempt_record)
            time.sleep(min(10, 2 + attempt * 2))
            continue

        last_ready = ensure.ready
        browser = connect_browser(ensure.ready.port)
        try:
            extracted = extract_sales_metrics(browser)
            attempt_record["status"] = extracted.get("status")
            attempt_record["note"] = extracted.get("note", "")
            # Include today filter result in record
            attempt_record["today_filter"] = extracted.get("today_filter", {})
            attempts.append(attempt_record)
        finally:
            try:
                browser.quit()
            except Exception:
                pass

        if extracted and extracted.get("status") in {"ok", "no_dashboard", "login_required"}:
            break
        time.sleep(min(10, 2 + attempt * 2))

    if extracted is None:
        extracted = {"status": "error", "note": "unknown failure after retries"}

    # Save full diagnosis if failed or suspicious
    if extracted.get("status") != "ok" or extracted.get("note", "").startswith("WARNING"):
        diag_path = _save_diagnosis(store_id, attempts, extracted)
        print(f"[DIAGNOSIS SAVED] {diag_path}", file=sys.stderr)

    row = {
        "store_id": store_id,
        "store_name": store_meta.get("mall_name", ""),
        "platform_name": store_meta.get("platform_name", ""),
        "ip_address": store_meta.get("ip_address", ""),
        "cdp_port": last_ready.port if last_ready else None,
        "ws_endpoint": last_ready.ws_endpoint if last_ready else None,
        "attempt_count": len(attempts),
        "attempts": attempts,
        **extracted,
    }
    rows.append(row)
    if flush_every:
        flush_results(rows, output_json, output_csv)
    if extracted.get("status") == "ok" and not keep_open_on_success:
        try:
            close_browser(store_id)
        except Exception:
            pass
    print(json.dumps({"progress": {"current": 1, "total": 1, "ok": 1 if row.get("status") == "ok" else 0, "error": 0 if row.get("status") == "ok" else 1, "item_id": store_id}}, ensure_ascii=False))
    return {"status": "ok", "count": len(rows), "json": str(output_json), "csv": str(output_csv)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Standard sales collector")
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--keep-open-on-success", action="store_true")
    args = parser.parse_args()

    result = collect_store(
        args.store_id,
        Path(args.output_dir),
        flush_every=args.flush_every,
        max_attempts=args.max_attempts,
        keep_open_on_success=args.keep_open_on_success,
    )
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
