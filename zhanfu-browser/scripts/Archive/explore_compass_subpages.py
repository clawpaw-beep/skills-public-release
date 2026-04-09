#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_data_analytics_20260407"

API_URL = "http://127.0.0.1:45008"

def post(payload):
    import urllib.request
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
    import urllib.request
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

def get_ws_endpoint(browser_id, timeout_seconds=60):
    deadline = time.time() + timeout_seconds
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
        except Exception:
            time.sleep(2)
    raise RuntimeError("failed")

print("=== Get ZhanFu WebDriver ===")
try:
    ws_endpoint = get_ws_endpoint("2376919")
except:
    ws_endpoint = "http://127.0.0.1:12627"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
    context = browser.contexts[0]
    page = context.new_page()

    # From data-overview page, find ALL sub-links
    print("\n=== Data Overview - find all sub-links ===")
    page.goto("https://seller.tiktokshopglobalselling.com/compass/data-overview",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(8)

    result = page.evaluate("""
        () => {
            var links = [];
            var all = document.querySelectorAll('a[href]');
            for (var a of all) {
                var href = a.href;
                var text = (a.innerText || '').trim().substring(0, 60);
                if (href && href.length > 10 && (href.includes('compass') || href.includes('analytics'))) {
                    links.push({text: text, href: href});
                }
            }
            return JSON.stringify(links);
        }
    """)
    links = json.loads(result)
    print(f"Found {len(links)} compass links:")
    for l in links:
        print(f"  [{l['text'][:40]}] {l['href']}")

    # Save
    out_file = os.path.join(OUTPUT_DIR, "compass_sub_links.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)

    # Now explore each sub-page
    # From the page text we saw these sub-tabs:
    sub_pages = [
        ("数据概览-全部", "https://seller.tiktokshopglobalselling.com/compass/data-overview"),
        ("直播数据", "https://seller.tiktokshopglobalselling.com/compass/live-analytics"),
        ("视频数据", "https://seller.tiktokshopglobalselling.com/compass/video-analytics"),
        ("商品数据", "https://seller.tiktokshopglobalselling.com/compass/product-analytics"),
        ("运营数据", "https://seller.tiktokshopglobalselling.com/compass/operations-analytics"),
        ("客户数据", "https://seller.tiktokshopglobalselling.com/compass/consumer-analytics"),
        ("售后数据", "https://seller.tiktokshopglobalselling.com/compass/aftersales-analytics"),
    ]

    for name, url in sub_pages:
        print(f"\n=== {name} ===")
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(8)

            body_text = page.locator("body").inner_text(timeout=15000)
            print(f"Body length: {len(body_text)} chars")
            print(f"URL: {page.url}")

            safe_name = name.replace("/", "_")
            text_file = os.path.join(OUTPUT_DIR, f"{safe_name}_text.txt")
            with open(text_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(body_text)

            screenshot_file = os.path.join(OUTPUT_DIR, f"{safe_name}.png")
            page.screenshot(path=screenshot_file, full_page=True)

            print(f"\nContent (first 2000 chars):\n{body_text[:2000]}")

        except Exception as e:
            print(f"Error: {e}")

    browser.close()

print(f"\n=== Done ===")
for f in os.listdir(OUTPUT_DIR):
    print(f"  {f}")
