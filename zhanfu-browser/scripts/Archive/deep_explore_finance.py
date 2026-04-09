#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_finance_full_20260407"
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_URL = "http://127.0.0.1:45008"

def do_post(payload):
    import urllib.request
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def get_browser_webdriver(browser_id):
    return do_post({"action": "GetBrowserWebDriver", "module": "WebDriverModule", "args": "", "browserId": str(browser_id)})

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

def explore_page(page, name, url):
    print(f"\n--- {name} ---")
    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        print("Wait 15s...")
        time.sleep(15)
        body_text = page.locator("body").inner_text(timeout=15000)
        final_url = page.url
        title = page.title()
        is_404 = "404" in title or (len(body_text) < 50)
        is_redirected = final_url != url
        print(f"Final URL: {final_url}")
        print(f"Title: {title}")
        print(f"Body length: {len(body_text)} chars")
        print(f"Status: {'OK' if not is_404 else '404/EMPTY'} {'(redirected)' if is_redirected else ''}")
        safe_name = name.replace("/", "_")
        with open(os.path.join(OUTPUT_DIR, f"{safe_name}_text.txt"), "w", encoding="utf-8", errors="replace") as f:
            f.write(body_text)
        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{safe_name}_screenshot.png"), full_page=True)
        print(f"Content (first 800 chars):\n{body_text[:800]}")
        return {"name": name, "url": url, "final_url": final_url, "title": title,
                "body_length": len(body_text), "is_404": is_404, "is_redirected": is_redirected,
                "body_preview": body_text[:800]}
    except Exception as e:
        print(f"Error: {e}")
        return {"name": name, "url": url, "error": str(e)}

print("=== Get ZhanFu WebDriver ===")
try:
    ws_endpoint = get_ws_endpoint("2376919")
except:
    ws_endpoint = "http://127.0.0.1:12627"
print("WebDriver OK")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_endpoint, timeout=30000)
    context = browser.contexts[0]
    page = context.new_page()

    # Correct finance URLs (seller.tiktokshopglobalselling.com domain)
    finance_pages = [
        ("finance-bills", "https://seller.tiktokshopglobalselling.com/finance/bills"),
        ("finance-deposit", "https://seller.tiktokshopglobalselling.com/deposit"),
        ("finance-analysis", "https://seller.tiktokshopglobalselling.com/finance/analysis"),
        ("finance-bill-payment", "https://seller.tiktokshopglobalselling.com/finance/bill-payment"),
        ("seller-wallet", "https://seller.tiktokshopglobalselling.com/seller-wallet"),
        # Also try US domain with correct paths
        ("finance-bills-us", "https://seller.us.tiktokshopglobalselling.com/finance/bills"),
        ("finance-overview-us", "https://seller.us.tiktokshopglobalselling.com/finance/overview"),
    ]

    results = []
    for page_key, url in finance_pages:
        r = explore_page(page, page_key, url)
        results.append(r)
        time.sleep(3)

    # Save results
    with open(os.path.join(OUTPUT_DIR, "finance_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    browser.close()

print(f"\n=== DONE ===")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  {f}")
