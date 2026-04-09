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

    # Go to the redirect target URL directly
    base_url = "https://seller.us.tiktokshopglobalselling.com/compass"

    sub_pages = [
        ("数据概览", f"{base_url}/data-overview"),
        ("直播数据", f"{base_url}/live-analytics"),
        ("视频数据", f"{base_url}/video-analytics"),
        ("商品数据", f"{base_url}/product-analytics"),
        ("运营数据", f"{base_url}/operations-analytics"),
        ("客户数据", f"{base_url}/consumer-analytics"),
        ("售后数据", f"{base_url}/aftersales-analytics"),
    ]

    all_links = {}

    for name, url in sub_pages:
        print(f"\n=== {name} ===")
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(8)

            body_text = page.locator("body").inner_text(timeout=15000)
            print(f"Body length: {len(body_text)} chars")
            print(f"Final URL: {page.url}")

            safe_name = name.replace("/", "_")
            text_file = os.path.join(OUTPUT_DIR, f"{safe_name}_text.txt")
            with open(text_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(body_text)

            screenshot_file = os.path.join(OUTPUT_DIR, f"{safe_name}.png")
            page.screenshot(path=screenshot_file, full_page=True)

            # Get sub-links on this page
            links_result = page.evaluate("""
                () => {
                    var links = [];
                    var all = document.querySelectorAll('a[href]');
                    for (var a of all) {
                        var href = a.href;
                        var text = (a.innerText || '').trim().substring(0, 60);
                        if (href && href.length > 10) {
                            links.push({text: text, href: href});
                        }
                    }
                    return JSON.stringify(links);
                }
            """)
            links = json.loads(links_result)
            all_links[name] = links
            print(f"Links on this page: {len(links)}")

            print(f"\nContent (first 1500 chars):\n{body_text[:1500]}")

        except Exception as e:
            print(f"Error: {e}")

    # Save all links
    out_file = os.path.join(OUTPUT_DIR, "compass_all_sub_links.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_links, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    browser.close()

print(f"\n=== Done ===")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  {f}")
