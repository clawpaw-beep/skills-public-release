#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import subprocess
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from zhanfu_runtime import (
    close_browser,
    ensure_real_webdriver,
    get_browser_list,
    is_connection_error,
    open_browser,
)


OUTPUT_DIR = Path(r"C:\Users\9400\Documents")
TIMEOUT_SECONDS = 90
DEFAULT_PROBLEMATIC_IDS = {
    2376919,  # FMCG
    2276096,  # Pro
    2273435,  # Tools
    2280875,  # Sopami Trail (7-day view)
    2264045,  # US7 (7-day view)
    2276389,  # Amazon (error)
    2515382,  # US9 (should be ok but verify)
    2337386,  # Hardware (verify)
}

LABEL_DASHBOARD = "\u7ecf\u8425\u6570\u636e"
LABEL_VERIFY = "\u8bf7\u5b8c\u6210\u4e0b\u5217\u9a8c\u8bc1\u540e\u7ee7\u7eed:"

METRIC_LABELS = {
    "gmv": "GMV",
    "orders": "\u8ba2\u5355\u6570",
    "page_views": "\u9875\u9762\u6d4f\u89c8\u6570",
    "avg_visitors": "\u5e73\u5747\u8bbf\u5ba2\u6570",
}

# Tab labels to click to switch to "today" view
TODAY_TAB_LABELS = ["\u4eca\u5929", "Today", "\u4eca\u5929"]



def parse_dashboard_lines(lines):
    if LABEL_DASHBOARD not in lines:
        return None

    start = lines.index(LABEL_DASHBOARD)
    section = lines[start : start + 25]

    def read_metric(label):
        if label not in section:
            return "", ""
        idx = section.index(label)
        value = section[idx + 1] if idx + 1 < len(section) else ""
        change = section[idx + 2] if idx + 2 < len(section) else ""
        return value, change

    store_alias = lines[start - 1] if start > 0 else ""
    metrics = {"store_alias": store_alias}
    for key, label in METRIC_LABELS.items():
        value, change = read_metric(label)
        metrics[key] = value
        metrics[f"{key}_change"] = change
    return metrics


def try_click_today_tab(page):
    """Try to click the 'today' tab if page is showing a different time range."""
    strategies = [
        lambda: page.get_by_text("\u4eca\u5929", exact=True).first,
        lambda: page.get_by_text("Today", exact=True).first,
        lambda: page.get_by_text("\u4eca\u5929").first,
        lambda: page.get_by_text("Today").first,
        lambda: page.locator("button", has_text="\u4eca\u5929").first,
        lambda: page.locator("button", has_text="Today").first,
        lambda: page.locator('[role="tab"]', has_text="\u4eca\u5929").first,
        lambda: page.locator('[role="tab"]', has_text="Today").first,
    ]
    for strategy in strategies:
        try:
            el = strategy()
            if el.is_visible(timeout=2000):
                el.click(timeout=5000)
                time.sleep(3)
                return True
        except Exception:
            pass
    return False


def extract_dashboard_worker(ws_endpoint):
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(ws_endpoint)
        except Exception as exc:
            return {
                "page_url": "",
                "page_title": "",
                "captcha_present": False,
                "raw_text_excerpt": "",
                "status": "error",
                "note": f"cdp connect failed: {exc}",
            }
        deadline = time.time() + 40
        page = None
        while time.time() < deadline and page is None:
            for context in browser.contexts:
                for candidate in context.pages:
                    if not candidate.url.startswith("chrome-extension://"):
                        page = candidate
                        break
                if page is not None:
                    break
            if page is None:
                time.sleep(2)

        if page is None:
            return {
                "page_url": "",
                "page_title": "",
                "captcha_present": False,
                "raw_text_excerpt": "",
                "status": "error",
                "note": "no non-extension page found",
            }

        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(5000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # Try to click "today" tab before reading
        try:
            clicked = try_click_today_tab(page)
            if clicked:
                page.wait_for_timeout(2000)
        except Exception:
            pass

        body_text = page.locator("body").inner_text(timeout=15000)
        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        parsed = parse_dashboard_lines(lines)

        result = {
            "page_url": page.url,
            "page_title": page.title(),
            "captcha_present": LABEL_VERIFY in body_text,
            "raw_text_excerpt": "\n".join(lines[:60]),
        }
        if parsed is None:
            result["status"] = "no_dashboard"
            result["note"] = "dashboard labels not found in page text"
        else:
            result["status"] = "ok"
            result["note"] = ""
            result.update(parsed)
        return result


def extract_dashboard(ws_endpoint):
    command = [
        sys.executable,
        "-X",
        "utf8",
        str(Path(__file__).resolve()),
        "--extract-ws",
        ws_endpoint,
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "extract subprocess failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"json decode failed: {exc} | stdout: {result.stdout[:200]}")


def is_connection_error(exc_text):
    lower = (exc_text or "").lower()
    return "10061" in lower or "connection refused" in lower or "cannot connect" in lower


def parse_target_ids(argv):
    if "--all" in argv:
        return None

    if "--mall-id" in argv:
        idx = argv.index("--mall-id")
        if idx + 1 >= len(argv):
            raise SystemExit("--mall-id requires a value")
        raw = argv[idx + 1]
        return {int(part.strip()) for part in raw.split(",") if part.strip()}

    if "--limit" in argv:
        idx = argv.index("--limit")
        if idx + 1 >= len(argv):
            raise SystemExit("--limit requires a value")
        limit = int(argv[idx + 1])
        preferred_order = [2515382, 2376919, 2273435, 2337386, 2276096, 2280875, 2264045, 2276389]
        return set(preferred_order[:limit])

    return DEFAULT_PROBLEMATIC_IDS


def main():
    stores = get_browser_list()
    target_ids = parse_target_ids(sys.argv[1:])
    if target_ids is not None:
        stores = [s for s in stores if int(s["mall_id"]) in target_ids]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = OUTPUT_DIR / f"zhanfu_sales_{timestamp}.csv"
    json_path = OUTPUT_DIR / f"zhanfu_sales_{timestamp}.json"

    single_store_mode = "--mall-id" in sys.argv[1:] or len(stores) <= 2
    per_store_stabilize = 25 if single_store_mode else 15
    results = []

    def flush_results():
        fieldnames = [
            "mall_id", "mall_name", "platform_name", "ip_address", "webdriver_port", "kernel_number",
            "ws_endpoint", "store_alias", "gmv", "gmv_change", "orders", "orders_change", "page_views",
            "page_views_change", "avg_visitors", "avg_visitors_change", "page_url", "page_title",
            "captcha_present", "status", "note", "raw_text_excerpt", "extracted_at",
        ]
        with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        with json_path.open("w", encoding="utf-8") as json_file:
            json.dump(results, json_file, ensure_ascii=False, indent=2)
    for index, store in enumerate(stores, start=1):
        mall_id = store["mall_id"]
        mall_name = store["mall_name"]
        platform_name = store["platform_name"]
        print(f"[{index}/{len(stores)}] {mall_id} {mall_name} - opening...", file=sys.stderr)

        row = {
            "mall_id": mall_id,
            "mall_name": mall_name,
            "platform_name": platform_name,
            "ip_address": store.get("ip_address", ""),
            "webdriver_port": "",
            "kernel_number": "",
            "ws_endpoint": "",
            "store_alias": "",
            "gmv": "",
            "gmv_change": "",
            "orders": "",
            "orders_change": "",
            "page_views": "",
            "page_views_change": "",
            "avg_visitors": "",
            "avg_visitors_change": "",
            "page_url": "",
            "page_title": "",
            "captcha_present": "",
            "status": "",
            "note": "",
            "extracted_at": datetime.now().isoformat(timespec="seconds"),
        }

        try:
            open_response = open_browser(mall_id)
            if open_response.get("ret") != 200:
                row["status"] = "open_failed"
                row["note"] = json.dumps(open_response, ensure_ascii=False)
                results.append(row)
                flush_results()
                continue

            ready, wait_error = ensure_real_webdriver(mall_id, startup_wait=TIMEOUT_SECONDS, reopen_once=True)
            if not ready:
                row["status"] = "webdriver_unavailable"
                row["note"] = wait_error
                results.append(row)
                flush_results()
                continue

            row["webdriver_port"] = ready.port
            row["kernel_number"] = ready.kernel_number or ""
            row["ws_endpoint"] = ready.ws_endpoint
        except Exception as exc:
            row["status"] = "error"
            row["note"] = str(exc)
            results.append(row)
            flush_results()
            continue

        print(f"Store ready: {mall_id} port={row['webdriver_port']}. Waiting for page to stabilize...", file=sys.stderr)
        time.sleep(per_store_stabilize)

        extracted = None
        error_msg = ""
        try:
            extracted = extract_dashboard(row["ws_endpoint"])
        except Exception as exc:
            error_msg = str(exc)
            if is_connection_error(error_msg):
                print(f"  Connection error detected ({error_msg}), reopening store once...", file=sys.stderr)
                try:
                    close_browser(mall_id)
                    time.sleep(3)
                    open_browser(mall_id)
                    ready, retry_error = ensure_real_webdriver(mall_id, startup_wait=60, reopen_once=False)
                    if ready:
                        row["webdriver_port"] = ready.port
                        row["kernel_number"] = ready.kernel_number or ""
                        row["ws_endpoint"] = ready.ws_endpoint
                        time.sleep(max(10, per_store_stabilize - 5))
                        extracted = extract_dashboard(row["ws_endpoint"])
                        error_msg = ""
                    else:
                        error_msg = retry_error or "reopen failed: no ws endpoint"
                except Exception as retry_exc:
                    error_msg = str(retry_exc)

        if extracted:
            row.update(extracted)
        else:
            row["status"] = "error"
            row["note"] = error_msg

        results.append(row)
        flush_results()
        time.sleep(2)

    print(f"CSV={csv_path}")
    print(f"JSON={json_path}")
    print("SUMMARY")
    for item in results:
        print(
            json.dumps(
                {
                    "mall_id": item["mall_id"],
                    "mall_name": item["mall_name"],
                    "status": item["status"],
                    "gmv": item["gmv"],
                    "orders": item["orders"],
                    "page_views": item["page_views"],
                    "avg_visitors": item["avg_visitors"],
                    "note": item["note"],
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--extract-ws":
        with redirect_stdout(sys.stderr):
            result = extract_dashboard_worker(sys.argv[2])
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
    else:
        main()
