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
except Exception as e:
    print(f"Error: {e}")
    ws_endpoint = "http://127.0.0.1:12627"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
    context = browser.contexts[0]
    page = context.new_page()

    # Go to homepage first
    print("\n=== Go to homepage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(5)

    # Find all sidebar links
    print("\n=== Get all sidebar links ===")
    sidebar_links = page.evaluate("""
        () => {
            var results = [];
            var sidebar = document.querySelector('[class*="sidebar"], aside, nav, [class*="menu"]');
            if (!sidebar) {
                // Try to find by text content
                var allLinks = document.querySelectorAll('a[href], [role="menuitem"], [class*="item"]');
                for (var l of allLinks) {
                    var href = l.href || l.getAttribute('href') || '';
                    var text = l.innerText ? l.innerText.trim() : '';
                    if (href && (href.includes('analytics') || href.includes('data') || text.includes('数据') || text.includes('分析'))) {
                        results.push({text: text, href: href});
                    }
                }
                return JSON.stringify({source: 'search', links: results.slice(0, 50)});
            }
            var links = sidebar.querySelectorAll('a[href]');
            for (var link of links) {
                results.push({text: link.innerText.trim(), href: link.href});
            }
            return JSON.stringify({source: 'sidebar', links: results});
        }
    """)
    print(f"Found links from: {json.loads(sidebar_links)['source']}")
    links_data = json.loads(sidebar_links)['links']
    print(f"Total: {len(links_data)}")

    # Show analytics/data related links
    analytics_links = [l for l in links_data if any(x in l['href'].lower() for x in ['analytics', 'data', 'stat', 'report'])]
    print(f"\nAnalytics/data links: {len(analytics_links)}")
    for l in analytics_links:
        print(f"  [{l['text'][:30]}] {l['href']}")

    # Also show ALL sidebar links (for context)
    print(f"\nAll sidebar links ({len(links_data)}):")
    for l in links_data[:30]:
        print(f"  [{l['text'][:30]}] {l['href'][:100]}")

    # Save all links
    out_file = os.path.join(OUTPUT_DIR, "sidebar_links.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(links_data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    browser.close()
