#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from zhanfu_runtime import ensure_real_webdriver_detailed, get_browser_list
from collector_sales import (
    click_open_store_if_zhanfu_page,
    detect_page_kind,
    pick_any_non_extension_page,
    pick_best_page,
    safe_page_body,
    safe_page_title,
    snapshot_browser_pages,
    try_navigate_to_seller_home,
    wait_for_non_extension_page,
)


def capture_one(store_id: int, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure = ensure_real_webdriver_detailed(
        store_id,
        startup_wait=90,
        reopen_once=True,
        reuse_existing_first=False,
        cooldown_seconds=4,
        backoff_seconds=4,
        stable_checks=2,
    )
    result = {
        "store_id": store_id,
        "ensure_real_webdriver": {
            "error": ensure.error,
            "used_reopen": ensure.used_reopen,
            "reused_existing": ensure.reused_existing,
            "attempts": [
                {
                    "attempt": item.attempt,
                    "phase": item.phase,
                    "ok": item.ok,
                    "port": item.port,
                    "ws_endpoint": item.ws_endpoint,
                    "error": item.error,
                    "waited_seconds": item.waited_seconds,
                    "version_checks": item.version_checks,
                    "reused_existing": item.reused_existing,
                    "reopened_browser": item.reopened_browser,
                    "open_response_ret": item.open_response_ret,
                    "close_response_ret": item.close_response_ret,
                }
                for item in ensure.attempts
            ],
        },
    }
    if not ensure.ready:
        result["status"] = "webdriver_unavailable"
        return result

    ws_endpoint = ensure.ready.ws_endpoint
    result["webdriver_port"] = ensure.ready.port
    result["ws_endpoint"] = ws_endpoint

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(ws_endpoint)
        page = None
        best_score = -999
        initial_pages = snapshot_browser_pages(browser)
        deadline = time.time() + 60
        while time.time() < deadline:
            candidate, current_score = pick_best_page(browser)
            if candidate is not None:
                page = candidate
                best_score = current_score
                if current_score >= 80:
                    break
            time.sleep(2)

        click_result = None
        if page is None:
            page, best_score = pick_any_non_extension_page(browser)

        if page is None:
            click_result = click_open_store_if_zhanfu_page(browser)
            page, best_score = wait_for_non_extension_page(browser, timeout_seconds=45)

        if page is None:
            result.update(
                {
                    "status": "no_page",
                    "initial_pages": initial_pages,
                    "open_store_click": click_result,
                    "final_pages": snapshot_browser_pages(browser),
                }
            )
            return result

        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        pre_nav_url = page.url
        pre_nav_title = safe_page_title(page)
        pre_nav_body = safe_page_body(page, timeout=5000)
        pre_nav_kind = detect_page_kind(pre_nav_url, pre_nav_title, pre_nav_body)

        nav_result = None
        if best_score < 80 or pre_nav_kind not in {"dashboard", "verification", "login"}:
            nav_result = try_navigate_to_seller_home(page)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass

        page.wait_for_timeout(6000)
        body = safe_page_body(page, timeout=15000)
        title = safe_page_title(page)
        kind = detect_page_kind(page.url, title, body)

        shot_path = output_dir / f"store_{store_id}.png"
        try:
            page.screenshot(path=str(shot_path), full_page=True)
            screenshot_error = ""
        except Exception as exc:
            screenshot_error = str(exc)

        result.update(
            {
                "status": "ok",
                "page_url": page.url,
                "page_title": title,
                "page_kind": kind,
                "body_excerpt": "\n".join([line.strip() for line in body.splitlines() if line.strip()][:40]),
                "screenshot_path": str(shot_path) if shot_path.exists() else "",
                "screenshot_error": screenshot_error,
                "initial_pages": initial_pages,
                "pre_navigation": {
                    "url": pre_nav_url,
                    "title": pre_nav_title,
                    "page_kind": pre_nav_kind,
                    "body_excerpt": "\n".join([line.strip() for line in pre_nav_body.splitlines() if line.strip()][:20]),
                },
                "navigation_attempt": nav_result,
                "open_store_click": click_result,
                "final_pages": snapshot_browser_pages(browser),
            }
        )
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture screenshots for login-required stores")
    parser.add_argument("--stores", nargs="+", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    browser_list = get_browser_list()
    meta_map = {int(item.get("mall_id", 0)): item for item in browser_list if item.get("mall_id")}

    results = []
    for store_id in args.stores:
        item = capture_one(store_id, output_dir / f"store_{store_id}")
        meta = meta_map.get(int(store_id), {})
        item["store_name"] = meta.get("mall_name", "")
        item["platform_name"] = meta.get("platform_name", "")
        results.append(item)
        print(json.dumps({"store_id": store_id, "status": item.get("status"), "page_kind": item.get("page_kind", "")}, ensure_ascii=False))

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": str(summary_path), "count": len(results)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
