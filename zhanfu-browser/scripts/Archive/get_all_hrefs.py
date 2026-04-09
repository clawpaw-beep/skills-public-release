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
    raise RuntimeError("failed to get WebDriver endpoint")

print("=== Get ZhanFu WebDriver ===")
try:
    ws_endpoint = get_ws_endpoint("2376919")
except:
    ws_endpoint = "http://127.0.0.1:12627"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
    context = browser.contexts[0]
    page = context.new_page()

    print("\n=== Go to homepage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(10)

    # Get ALL hrefs from the page
    print("\n=== Get ALL hrefs ===")
    result = page.evaluate("""
        () => {
            var links = [];
            var all = document.querySelectorAll('a[href]');
            for (var a of all) {
                var href = a.href;
                var text = (a.innerText || '').trim().substring(0, 50);
                if (href && href.length > 10) {
                    links.push({text: text, href: href});
                }
            }
            return JSON.stringify(links);
        }
    """)
    links = json.loads(result)
    print(f"Total links found: {len(links)}")

    # Unique hrefs
    unique_hrefs = list({l['href']: l for l in links}.values())
    print(f"Unique hrefs: {len(unique_hrefs)}")

    # Show analytics/data URLs
    analytics = [l for l in unique_hrefs if any(x in l['href'].lower() for x in ['analytics', 'data', 'stat', 'report', 'seller', 'order'])]
    print(f"\nAnalytics/order URLs ({len(analytics)}):")
    for l in analytics[:30]:
        print(f"  [{l['text'][:30]}] {l['href']}")

    # Save all
    out_file = os.path.join(OUTPUT_DIR, "all_page_links.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(unique_hrefs, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Now go to product list page and find analytics links there
    print("\n=== Go to product list ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list?shop_region=US",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(8)

    result2 = page.evaluate("""
        () => {
            var links = [];
            var all = document.querySelectorAll('a[href]');
            for (var a of all) {
                var href = a.href;
                var text = (a.innerText || '').trim().substring(0, 50);
                if (href && href.length > 10) {
                    links.push({text: text, href: href});
                }
            }
            return JSON.stringify(links);
        }
    """)
    links2 = json.loads(result2)
    unique2 = list({l['href']: l for l in links2}.values())
    analytics2 = [l for l in unique2 if any(x in l['href'].lower() for x in ['analytics', 'data', 'stat', 'report'])]
    print(f"Product page analytics links ({len(analytics2)}):")
    for l in analytics2[:20]:
        print(f"  [{l['text'][:30]}] {l['href']}")

    # Show all product page links
    print(f"\nAll product page links ({len(unique2)}):")
    for l in unique2[:40]:
        print(f"  [{l['text'][:30]}] {l['href']}")

    browser.close()
