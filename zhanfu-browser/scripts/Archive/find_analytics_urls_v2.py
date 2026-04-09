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
        except Exception as exc:
            print(f"  retry: {exc}")
        time.sleep(2)
    raise RuntimeError("failed to get WebDriver endpoint")

print("=== Get ZhanFu WebDriver ===")
try:
    ws_endpoint = get_ws_endpoint("2376919")
    print(f"OK")
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

    # Try multiple ways to find sidebar
    print("\n=== Find sidebar links ===")
    result = page.evaluate("""
        () => {
            var results = [];

            // Method 1: Find all links with partial URL or text
            var allElements = document.querySelectorAll('[role="menuitem"], [role="menu"] a, [class*="sidebar"] a, [class*="menu"] a, [class*="nav"] a, [class*="item"] a');
            for (var el of allElements) {
                var href = el.href || el.getAttribute('href') || '';
                var text = (el.innerText || '').trim().substring(0, 50);
                if (href || text) {
                    results.push({text: text, href: href, tag: el.tagName, className: el.className.substring(0, 50)});
                }
            }

            return JSON.stringify(results.slice(0, 100));
        }
    """)
    links = json.loads(result)
    print(f"Found {len(links)} elements")

    # Show unique URLs
    hrefs = list(set([l['href'] for l in links if l['href']]))
    print(f"Unique hrefs: {len(hrefs)}")

    # Analytics related
    analytics = [h for h in hrefs if 'analytics' in h.lower() or 'data' in h.lower() or 'stat' in h.lower()]
    print(f"\nAnalytics URLs: {len(analytics)}")
    for h in analytics[:20]:
        print(f"  {h}")

    # Show all
    print(f"\nAll hrefs ({len(hrefs)}):")
    for h in hrefs[:50]:
        print(f"  {h}")

    # Also get body text to see sidebar structure
    print("\n=== Sidebar text (first 2000 chars) ===")
    body_text = page.evaluate("""
        () => {
            // Find sidebar
            var sidebar = document.querySelector('[class*="sidebar"]');
            if (sidebar) return sidebar.innerText.substring(0, 2000);

            // Try to find by role
            var menu = document.querySelector('[role="menu"]');
            if (menu) return menu.innerText.substring(0, 2000);

            // Try to find left-side nav
            var nav = document.querySelector('nav');
            if (nav) return nav.innerText.substring(0, 2000);

            return "no sidebar found";
        }
    """)
    print(body_text[:2000])

    # Save
    out_file = os.path.join(OUTPUT_DIR, "sidebar_links.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"hrefs": hrefs, "elements": links}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    browser.close()
