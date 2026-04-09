#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, time, json
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_finance_retry_20260407"
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
    raise RuntimeError("failed to get WebDriver endpoint")

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
        print(f"Content (first 500 chars):\n{body_text[:500]}")
        return {"name": name, "url": url, "final_url": final_url, "title": title,
                "body_length": len(body_text), "is_404": is_404, "is_redirected": is_redirected,
                "body_preview": body_text[:500]}
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

    # First: go to homepage and find ALL finance-related links from sidebar
    print("\n=== Find finance links from homepage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(10)

    all_links = page.evaluate("""
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
    links = json.loads(all_links)
    finance_links = [l for l in links if 'finance' in l['href'].lower() or 'bill' in l['href'].lower() or 'wallet' in l['href'].lower() or 'deposit' in l['href'].lower() or 'earn' in l['href'].lower()]
    print(f"Found {len(finance_links)} finance links:")
    for l in finance_links:
        print(f"  [{l['text'][:30]}] {l['href']}")

    # Save all links
    with open(os.path.join(OUTPUT_DIR, "all_links.json"), "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)

    # Try various finance URL patterns
    print("\n=== Try various finance URL patterns ===")
    finance_patterns = [
        ("finance-overview", "https://seller.us.tiktokshopglobalselling.com/finance/overview?shop_region=US"),
        ("finance-bill", "https://seller.us.tiktokshopglobalselling.com/finance/bill?shop_region=US"),
        ("finance-wallet", "https://seller.us.tiktokshopglobalselling.com/finance/wallet?shop_region=US"),
        ("finance-earnings", "https://seller.us.tiktokshopglobalselling.com/finance/earnings?shop_region=US"),
        ("finance-deposit", "https://seller.us.tiktokshopglobalselling.com/finance/deposit?shop_region=US"),
        # Also try going through product page sidebar links
        ("finance-via-sidebar-1", ""),
        ("finance-via-sidebar-2", ""),
    ]

    results = []
    for name, url in finance_patterns:
        if url:
            r = explore_page(page, name, url)
            results.append(r)

    # Now try clicking on finance menu in sidebar
    print("\n=== Try clicking finance menu from product page ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list?shop_region=US",
              timeout=60000, wait_until="domcontentloaded")
    time.sleep(10)

    # Find and click finance link
    menu_result = page.evaluate("""
        () => {
            // Find all sidebar links
            var allLinks = document.querySelectorAll('a[href]');
            var financeLinks = [];
            for (var a of allLinks) {
                if ((a.href || '').includes('finance') || (a.href || '').includes('bill') ||
                    (a.href || '').includes('wallet') || (a.href || '').includes('deposit') ||
                    (a.href || '').includes('earn')) {
                    financeLinks.push({text: a.innerText.trim(), href: a.href});
                }
            }
            return JSON.stringify(financeLinks);
        }
    """)
    finance_from_menu = json.loads(menu_result)
    print(f"Finance links from product page: {len(finance_from_menu)}")
    for l in finance_from_menu:
        print(f"  [{l['text'][:30]}] {l['href']}")

    # Try clicking each finance link
    for link_info in finance_from_menu:
        href = link_info['href']
        text = link_info['text']
        if href and len(href) > 20:
            r = explore_page(page, f"clicked-{text[:20]}", href)
            results.append(r)
            time.sleep(3)

    # Save results
    with open(os.path.join(OUTPUT_DIR, "finance_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    browser.close()

print(f"\n=== DONE ===")
print(f"Output: {OUTPUT_DIR}")
for f in sorted(os.listdir(OUTPUT_DIR)):
    print(f"  {f}")
