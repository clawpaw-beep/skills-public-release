#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
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


def parse_dashboard_lines(lines: list[str]) -> dict[str, str] | None:
    joined = "\n".join(lines)
    if not any(label in joined for labels in METRIC_LABELS.values() for label in labels):
        return None

    focus_start = 0
    for anchor in ["Last 7 days", "经营数据", "Updated on", "今天"]:
        if anchor in lines:
            focus_start = max(0, lines.index(anchor))
            break
    focus_end = min(len(lines), focus_start + 50)
    section = lines[focus_start:focus_end]

    def looks_like_value(text: str) -> bool:
        text = (text or "").strip()
        if not text:
            return False
        if text.startswith("$"):
            return True
        if any(ch.isdigit() for ch in text):
            return True
        if text.endswith("%"):
            return True
        if "/" in text and any(ch.isdigit() for ch in text):
            return True
        return False

    def read_metric(labels: list[str]) -> tuple[str, str]:
        for idx, line in enumerate(section):
            if line not in labels:
                continue
            value = section[idx + 1] if idx + 1 < len(section) else ""
            change = section[idx + 2] if idx + 2 < len(section) else ""
            if not looks_like_value(value):
                continue
            if change and not looks_like_value(change):
                change = ""
            return value, change
        return "", ""

    metrics: dict[str, str] = {}
    for key, labels in METRIC_LABELS.items():
        value, change = read_metric(labels)
        metrics[key] = value
        metrics[f"{key}_change"] = change
    return metrics


def try_click_today(tab) -> bool:
    for text in ["今天", "Today"]:
        try:
            ele = tab.ele(f"text:{text}", timeout=2)
            if ele:
                ele.click()
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def extract_sales_metrics(browser) -> dict[str, object]:
    diagnosis = diagnose_store_entry(browser, try_open_store=True, try_goto_home=True)
    tab, score = pick_best_tab(browser)
    if tab is None:
        return {"status": "error", "note": "没有找到可用页面标签", "diagnosis": diagnosis}

    text = tab_body_text(tab)
    try_click_today(tab)
    text = tab_body_text(tab)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    metrics = parse_dashboard_lines(lines)
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
    }

    if any(hint in lower for hint in LOGIN_HINTS):
        result["status"] = "login_required"
        result["note"] = "店铺已打开，但当前落在登录页，需要先手动登录"
        return result

    if metrics is None:
        result["status"] = "no_dashboard"
        result["note"] = "已进入 seller 页面，但没读到标准经营数据区块"
        return result

    result.update(metrics)
    result["note"] = ""
    return result


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
