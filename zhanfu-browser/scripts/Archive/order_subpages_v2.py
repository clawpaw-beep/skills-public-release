#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore order sub-pages that DON'T use the ZTI iframe."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

def extract(page, wait=12):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 8000),
                tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item")).map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                table_headers: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean)).filter(h => h.length > 0),
                table_rows: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("tbody tr")).slice(0, 20).map(r => Array.from(r.querySelectorAll("td")).map(d => d.textContent.trim()))),
                buttons: Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                inputs: Array.from(document.querySelectorAll("input")).filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                metrics: Array.from(document.querySelectorAll("[class*='metric'], [class*='card'], [class*='stat']")).map(c => c.textContent.trim().substring(0, 100)).filter(t => t.length > 5),
                iframes: Array.from(document.querySelectorAll("iframe")).map(f => f.src)
            });
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

ORDER_SUBPAGES = [
    ("退货管理", "https://seller.us.tiktokshopglobalselling.com/order/return"),
    ("管理取消申请", "https://seller.us.tiktokshopglobalselling.com/order/cancel"),
    ("管理物流", "https://seller.us.tiktokshopglobalselling.com/logistics/manage"),
    ("批量发货", "https://seller.us.tiktokshopglobalselling.com/order/batch-ship"),
    ("履约表现", "https://seller.us.tiktokshopglobalselling.com/fulfillment/performance"),
    ("包邮", "https://seller.us.tiktokshopglobalselling.com/shipping/free"),
    ("退货设置", "https://seller.us.tiktokshopglobalselling.com/return/setting"),
]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # First go to a known working page
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/rating",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(8)
    print(f"Baseline: {page.url}")

    all_results = {}

    for name, url in ORDER_SUBPAGES:
        print(f"\n### {name} ({url}) ###")
        try:
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            data = extract(page, wait=12)

            print(f"  Title: {data.get('title')}")
            print(f"  URL: {data.get('url')}")
            print(f"  Iframes: {data.get('iframes', [])}")
            print(f"  Tabs: {data.get('tabs', [])[:8]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:10]}")
            print(f"  Metrics: {data.get('metrics', [])[:5]}")
            print(f"  Headings: {data.get('headings', [])[:5]}")
            print(f"  Text (first 300): {data.get('main_text', '')[:300]}")

            ss_name = f"order2_{name[:6]}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[name] = {**data, "tested_url": url}

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = {"error": str(e), "tested_url": url}

        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "order_subpages_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== Done === Saved: {out_file}")
    browser.close()
