#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep exploration of Compass analytics sub-pages - screenshot + text analysis."""
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

    base = "https://seller.us.tiktokshopglobalselling.com/compass"

    # Sub-pages to explore - use the correct base
    pages = [
        ("data-overview", f"{base}/data-overview", "数据概览"),
        ("video-analytics", f"{base}/video-analytics", "视频数据"),
        ("product-analytics", f"{base}/product-analytics", "商品数据"),
        ("live-analytics", f"{base}/live-analytics", "直播数据"),
        ("operations-analytics", f"{base}/operations-analytics", "运营数据"),
        ("consumer-analytics", f"{base}/consumer-analytics", "客户数据"),
        ("aftersales-analytics", f"{base}/aftersales-analytics", "售后数据"),
        ("promotion-analytics", f"{base}/promotion-analytics", "推广分析"),
        ("analytics-rankings", f"{base}/analytics-rankings", "分析排行"),
    ]

    results = {}

    for page_key, url, name in pages:
        print(f"\n{'='*50}")
        print(f"=== {name} ({page_key}) ===")
        print(f"URL: {url}")

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            # Wait longer for ZhanFu
            print("Waiting 12s for page to load...")
            time.sleep(12)

            body_text = page.locator("body").inner_text(timeout=15000)
            final_url = page.url
            title = page.title()

            print(f"Final URL: {final_url}")
            print(f"Title: {title}")
            print(f"Body length: {len(body_text)} chars")

            # Determine if page actually loaded (not 404 redirect)
            is_404 = "404" in title or (len(body_text) < 50)
            is_redirected = final_url != url and "data-overview" in final_url

            print(f"Status: {'404/Empty' if is_404 else 'OK'} {'(redirected)' if is_redirected else ''}")

            # Save screenshot
            screenshot_file = os.path.join(OUTPUT_DIR, f"{page_key}_screenshot.png")
            page.screenshot(path=screenshot_file, full_page=True)

            # Save text
            text_file = os.path.join(OUTPUT_DIR, f"{page_key}_text.txt")
            with open(text_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(body_text)

            # Get page structure
            page_info = page.evaluate("""
                () => {
                    // Get all text content split by lines
                    var body = document.body.innerText || '';
                    var lines = body.split('\\n').filter(l => l.trim()).slice(0, 50);

                    // Get all headings
                    var headings = [];
                    ['h1','h2','h3','h4'].forEach(function(tag) {
                        document.querySelectorAll(tag).forEach(function(el) {
                            var t = el.innerText.trim();
                            if (t) headings.push({tag: tag, text: t.substring(0, 80)});
                        });
                    });

                    // Get all visible text blocks that look like KPIs (contain numbers and $ or %)
                    var kpis = [];
                    var allSpans = document.querySelectorAll('span, div');
                    allSpans.forEach(function(el) {
                        var text = el.innerText || '';
                        if ((text.includes('$') || text.includes('%') || text.match(/\\d+\\.\\d+/)) &&
                            text.trim().length < 100 && text.trim().length > 1) {
                            var style = window.getComputedStyle(el);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                kpis.push(text.trim().substring(0, 50));
                            }
                        }
                    });

                    // Get tables
                    var tables = [];
                    document.querySelectorAll('table').forEach(function(t) {
                        var headers = [];
                        t.querySelectorAll('th').forEach(function(th) {
                            headers.push(th.innerText.trim().substring(0, 30));
                        });
                        var rows = [];
                        t.querySelectorAll('tbody tr').forEach(function(tr) {
                            var cells = [];
                            tr.querySelectorAll('td').forEach(function(td) {
                                cells.push(td.innerText.trim().substring(0, 30));
                            });
                            if (cells.length > 0) rows.push(cells);
                        });
                        if (rows.length > 0) tables.push({headers: headers, rows: rows.slice(0, 10)});
                    });

                    // Get sub-nav tabs
                    var tabs = [];
                    document.querySelectorAll('[class*="tab"], [class*="Tab"], [role="tab"]').forEach(function(el) {
                        var t = el.innerText.trim();
                        if (t) tabs.push(t.substring(0, 30));
                    });

                    // Get sidebar structure
                    var sidebar = '';
                    var sideNav = document.querySelector('[class*="sidebar"], aside, nav');
                    if (sideNav) sidebar = sideNav.innerText.substring(0, 500);

                    return JSON.stringify({
                        lines: lines,
                        headings: headings.slice(0, 20),
                        kpis: [...new Set(kpis)].slice(0, 30),
                        tables: tables.slice(0, 5),
                        tabs: [...new Set(tabs)].slice(0, 20),
                        sidebar: sidebar,
                        body_preview: body.substring(0, 2000)
                    });
                }
            """)

            page_data = json.loads(page_info)

            print(f"\n--- Headings ({len(page_data['headings'])}) ---")
            for h in page_data['headings'][:10]:
                print(f"  [{h['tag']}] {h['text']}")

            print(f"\n--- KPIs ({len(page_data['kpis'])}) ---")
            for k in page_data['kpis'][:15]:
                print(f"  {k}")

            print(f"\n--- Tabs ({len(page_data['tabs'])}) ---")
            for t in page_data['tabs'][:10]:
                print(f"  {t}")

            print(f"\n--- Tables ({len(page_data['tables'])}) ---")
            for i, t in enumerate(page_data['tables'][:3]):
                print(f"  Table {i+1}: {len(t['rows'])} rows")
                if t['headers']:
                    print(f"    Headers: {t['headers']}")
                if t['rows']:
                    print(f"    Row1: {t['rows'][0]}")

            print(f"\n--- Sidebar ---")
            print(f"  {page_data['sidebar'][:300]}")

            print(f"\n--- Body Preview ---")
            print(f"  {page_data['body_preview'][:1000]}")

            results[page_key] = {
                "name": name,
                "url": url,
                "final_url": final_url,
                "title": title,
                "body_length": len(body_text),
                "is_404": is_404,
                "is_redirected": is_redirected,
                "screenshot": screenshot_file,
                "text_file": text_file,
                "headings": page_data['headings'],
                "kpis": page_data['kpis'],
                "tabs": page_data['tabs'],
                "tables": page_data['tables'],
                "body_preview": page_data['body_preview'][:1000]
            }

        except Exception as e:
            print(f"Error: {e}")
            results[page_key] = {"name": name, "error": str(e)}

    # Save results
    out_file = os.path.join(OUTPUT_DIR, "compass_deep_explore.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*50}")
    print(f"Results saved: {out_file}")

    browser.close()
