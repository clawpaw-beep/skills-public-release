#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

API_URL = "http://127.0.0.1:45008"

def post(payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def get_browser_webdriver(browser_id):
    return post({
        "action": "GetBrowserWebDriver",
        "module": "WebDriverModule",
        "args": "",
        "browserId": str(browser_id),
    })

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def get_ws_endpoint(browser_id, timeout_seconds=60):
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            response = get_browser_webdriver(browser_id)
            info = response.get("returnObj") or {}
            port = info.get("WebDriverPort") or 0
            if port:
                version = fetch_json(f"http://127.0.0.1:{port}/json/version")
                ws_endpoint = version.get("webSocketDebuggerUrl", "")
                if ws_endpoint:
                    return ws_endpoint
        except Exception as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(last_error or "failed to get WebDriver endpoint")

# Test order lookup
TEST_ORDER_ID = "577330037834354834"  # From return orders

print(f"=== Lookup order: {TEST_ORDER_ID} ===")

# Get ZhanFu WebDriver
try:
    ws_endpoint = get_ws_endpoint("2376919")
    print(f"WebDriver endpoint: {ws_endpoint[:80]}")
except Exception as e:
    print(f"WebDriver error: {e}")
    ws_endpoint = "http://127.0.0.1:12627"  # fallback

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
    context = browser.contexts[0]
    page = context.new_page()

    detail_url = f"https://seller.us.tiktokshopglobalselling.com/order/detail?order_no={TEST_ORDER_ID}&shop_region=US"
    print(f"\nNavigating to: {detail_url}")

    page.goto(detail_url, timeout=60000, wait_until="domcontentloaded")
    time.sleep(6)

    body_text = page.locator("body").inner_text(timeout=30000)
    # Save full text
    out_file = os.path.join(OUTPUT_DIR, f"order_detail_{TEST_ORDER_ID}.txt")
    with open(out_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(body_text)
    print(f"\nBody text saved to: {out_file}")
    print(f"Body length: {len(body_text)} chars")

    page.screenshot(path=f"{OUTPUT_DIR}/order_detail_{TEST_ORDER_ID}.png", full_page=True)
    print("Screenshot saved")

    browser.close()
