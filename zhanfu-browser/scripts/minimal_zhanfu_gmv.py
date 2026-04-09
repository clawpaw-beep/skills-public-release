#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from zhanfu_runtime import (
    connect_browser,
    diagnose_store_entry,
    ensure_zhanfu_ready,
    get_browser_list,
    wait_for_api_ready,
    start_zhanfu,
    is_api_ready,
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
    for anchor in ["Last 7 days", "经营数据", "Updated on"]:
        if anchor in lines:
            focus_start = max(0, lines.index(anchor))
            break
    focus_end = min(len(lines), focus_start + 40)
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


def extract_metrics(browser) -> dict[str, object]:
    diagnosis = diagnose_store_entry(browser, try_open_store=True, try_goto_home=True)
    tab, score = pick_best_tab(browser)
    if tab is None:
        return {
            "status": "error",
            "note": "没有找到可用页面标签",
            "diagnosis": diagnosis,
        }

    text = tab_body_text(tab)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
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
        "raw_text_excerpt": "\n".join(lines[:80]),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="最小可用站斧 GMV 读取脚本")
    parser.add_argument("--store-id", type=int, required=True, help="站斧 mall_id")
    parser.add_argument("--output", help="输出 JSON 路径")
    args = parser.parse_args()

    if not is_api_ready():
        if not start_zhanfu():
            raise SystemExit("站斧启动失败，无法拉起 WebDriver 模式")
        ok, elapsed = wait_for_api_ready(max_wait=60, poll_interval=2)
        if not ok:
            raise SystemExit(f"站斧 HTTP API 在 {elapsed}s 内未就绪")

    stores = get_browser_list()
    store = next((s for s in stores if int(s.get("mall_id", 0)) == int(args.store_id)), None)
    if not store:
        raise SystemExit(f"store_id {args.store_id} 不在 GetBrowserList 里")

    ensure = ensure_zhanfu_ready(args.store_id, startup_wait=60, cdp_wait=90, kill_first=False)
    payload: dict[str, object] = {
        "store_id": args.store_id,
        "store_name": store.get("mall_name") or store.get("shop_name") or "",
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "webdriver_ready": bool(ensure.ready),
        "webdriver_error": ensure.error,
    }

    if not ensure.ready:
        payload["status"] = "webdriver_unavailable"
    else:
        browser = connect_browser(ensure.ready.port)
        try:
            payload.update(extract_metrics(browser))
            payload["cdp_port"] = ensure.ready.port
            payload["ws_endpoint"] = ensure.ready.ws_endpoint
        finally:
            try:
                browser.quit()
            except Exception:
                pass

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
