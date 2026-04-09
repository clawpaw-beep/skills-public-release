#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try English/global TikTok Shop URLs without the 'us' prefix."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

ENGLISH_URL_PATTERNS = {
    # Try without 'us' prefix - global seller center
    "analytics-orders": "https://seller.tiktokshopglobalselling.com/analytics/orders",
    "analytics-store": "https://seller.tiktokshopglobalselling.com/analytics/store",
    "analytics-product": "https://seller.tiktokshopglobalselling.com/analytics/product",
    "analytics-live": "https://seller.tiktokshopglobalselling.com/analytics/live",
    "marketing-reach": "https://seller.tiktokshopglobalselling.com/marketing/reach",
    "marketing-promotion": "https://seller.tiktokshopglobalselling.com/marketing/promotion",
    "marketing-shopads": "https://seller.tiktokshopglobalselling.com/shop-ad/overview",
    "marketing-smart": "https://seller.tiktokshopglobalselling.com/marketing/smart",
    "buyer-group": "https://seller.tiktokshopglobalselling.com/buyer/group",
    "affiliate-landing": "https://seller.tiktokshopglobalselling.com/affiliate/landing",
    "order-manage": "https://seller.tiktokshopglobalselling.com/order/manage",
    "finance-overview": "https://seller.tiktokshopglobalselling.com/finance/overview",
    "growth-task": "https://seller.tiktokshopglobalselling.com/growth/task",
    "compliance-overview": "https://seller.tiktokshopglobalselling.com/compliance/overview",
    "accountHealth-health": "https://seller.tiktokshopglobalselling.com/accountHealth/health",

    # Also try seller-uk (UK domain)
    "uk-analytics": "https://seller-uk.tiktokshopglobalselling.com/analytics/orders",
    "uk-marketing": "https://seller-uk.tiktokshopglobalselling.com/marketing/reach",
    "uk-order": "https://seller-uk.tiktokshopglobalselling.com/order/manage",
}

def extract(page, wait=12):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 5000),
                tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item")).map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                table_headers: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean)).filter(h => h.length > 0),
                buttons: Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                inputs: Array.from(document.querySelectorAll("input")).filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                sidebar_items: Array.from(document.querySelectorAll('.core-menu-item')).map(el => el.innerText.trim()).filter(t => t.length > 0)
            });
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    all_results = {}

    for name, url in ENGLISH_URL_PATTERNS.items():
        print(f"\n### {name} ###")
        print(f"  URL: {url}")
        try:
            page.goto(url, timeout=40000, wait_until="domcontentloaded")
            data = extract(page, wait=15)

            print(f"  Title: {data.get('title')}")
            print(f"  Final URL: {data.get('url')}")
            print(f"  Sidebar items: {data.get('sidebar_items', [])[:10]}")
            print(f"  Tabs: {data.get('tabs', [])[:6]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:8]}")
            print(f"  Text (first 300): {data.get('main_text', '')[:300]}")

            ss_name = f"en_{name}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[name] = {**data, "tested_url": url}

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = {"error": str(e), "tested_url": url}

        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "english_url_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== Done === Saved: {out_file}")
    browser.close()
