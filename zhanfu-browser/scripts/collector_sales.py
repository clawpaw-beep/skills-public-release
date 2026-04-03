#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from playwright.sync_api import sync_playwright

from zhanfu_runtime import close_browser, ensure_real_webdriver, is_connection_error, open_browser

LABEL_DASHBOARD = "经营数据"
LABEL_VERIFY = "请完成下列验证后继续:"
METRIC_LABELS = {
    "gmv": "GMV",
    "orders": "订单数",
    "page_views": "页面浏览数",
    "avg_visitors": "平均访客数",
}


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

    metrics = {}
    for key, label in METRIC_LABELS.items():
        value, change = read_metric(label)
        metrics[key] = value
        metrics[f"{key}_change"] = change
    return metrics


def try_click_today_tab(page):
    for text in ["今天", "Today"]:
        try:
            el = page.get_by_text(text, exact=True).first
            if el.is_visible(timeout=2000):
                el.click(timeout=5000)
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def extract_dashboard_worker(ws_endpoint):
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(ws_endpoint)
        page = None
        deadline = time.time() + 40
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
            return {"status": "error", "note": "no non-extension page found", "raw_text_excerpt": ""}
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(5000)
        try_click_today_tab(page)
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
    command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--extract-ws", ws_endpoint]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "extract subprocess failed")
    return json.loads(result.stdout)


def flush_results(rows, output_json: Path, output_csv: Path):
    output_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if rows:
        with output_csv.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def collect_store(store_id: int, output_dir: Path, flush_every: int = 1):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"sales_store_{store_id}.json"
    output_csv = output_dir / f"sales_store_{store_id}.csv"
    rows = []

    open_response = open_browser(store_id)
    if open_response.get("ret") != 200:
        raise RuntimeError(json.dumps(open_response, ensure_ascii=False))
    ready, wait_error = ensure_real_webdriver(store_id, startup_wait=90, reopen_once=True)
    if not ready:
        raise RuntimeError(wait_error or "webdriver unavailable")

    try:
        extracted = extract_dashboard(ready.ws_endpoint)
    except Exception as exc:
        if is_connection_error(str(exc)):
            close_browser(store_id)
            time.sleep(3)
            open_browser(store_id)
            ready, wait_error = ensure_real_webdriver(store_id, startup_wait=60, reopen_once=False)
            if not ready:
                raise RuntimeError(wait_error or "reopen failed")
            extracted = extract_dashboard(ready.ws_endpoint)
        else:
            raise

    row = {
        "store_id": store_id,
        "webdriver_port": ready.port,
        "ws_endpoint": ready.ws_endpoint,
        **extracted,
    }
    rows.append(row)
    if flush_every:
        flush_results(rows, output_json, output_csv)
    print(json.dumps({"progress": {"current": 1, "total": 1, "ok": 1 if row.get('status') == 'ok' else 0, "error": 0 if row.get('status') == 'ok' else 1, "item_id": store_id}}, ensure_ascii=False))
    return {"status": "ok", "count": len(rows), "json": str(output_json), "csv": str(output_csv)}


def main():
    parser = argparse.ArgumentParser(description="Standard sales collector")
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--ws-endpoint")
    args = parser.parse_args()
    result = collect_store(args.store_id, Path(args.output_dir), flush_every=args.flush_every)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--extract-ws":
        with redirect_stdout(sys.stderr):
            result = extract_dashboard_worker(sys.argv[2])
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
    else:
        main()
