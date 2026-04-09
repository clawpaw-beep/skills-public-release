#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try correct US seller center paths with proper structure."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

# Try URL combinations on the US seller center
US_URL_PATTERNS = {
    # 数据分析 - common patterns
    "analytics-orders": "https://seller.us.tiktokshopglobalselling.com/analytics/orders",
    "analytics-orders2": "https://seller.us.tiktokshopglobalselling.com/order/analytics",
    "analytics-product": "https://seller.us.tiktokshopglobalselling.com/analytics/product",
    "analytics-store": "https://seller.us.tiktokshopglobalselling.com/analytics/store",
    "analytics-live": "https://seller.us.tiktokshopglobalselling.com/analytics/live",
    "analytics-marketing": "https://seller.us.tiktokshopglobalselling.com/marketing/analytics",
    "analytics-customer": "https://seller.us.tiktokshopglobalselling.com/analytics/customer",
    "analytics-after-sales": "https://seller.us.tiktokshopglobalselling.com/analytics/after-sales",
    "analytics-ranking": "https://seller.us.tiktokshopglobalselling.com/analytics/ranking",
    "analytics-overview": "https://seller.us.tiktokshopglobalselling.com/analytics/overview",

    # 订单
    "order-list": "https://seller.us.tiktokshopglobalselling.com/order/list",
    "order-all": "https://seller.us.tiktokshopglobalselling.com/order/all",

    # 营销
    "marketing-home": "https://seller.us.tiktokshopglobalselling.com/marketing/home",
    "marketing-campaigns": "https://seller.us.tiktokshopglobalselling.com/marketing/campaigns",
    "marketing-reach2": "https://seller.us.tiktokshopglobalselling.com/marketing/reach",
    "marketing-ads": "https://seller.us.tiktokshopglobalselling.com/marketing/ads",

    # 触达/客户
    "reach-overview": "https://seller.us.tiktokshopglobalselling.com/reach/overview",
    "buyer-manage": "https://seller.us.tiktokshopglobalselling.com/buyer/manage",

    # 成长
    "growth-overview": "https://seller.us.tiktokshopglobalselling.com/growth/overview",
    "growth-center": "https://seller.us.tiktokshopglobalselling.com/growth/center",

    # 账号健康
    "health-overview": "https://seller.us.tiktokshopglobalselling.com/health/overview",
    "accountHealth-score": "https://seller.us.tiktokshopglobalselling.com/accountHealth/score",

    # 合规
    "compliance-dashboard": "https://seller.us.tiktokshopglobalselling.com/compliance/dashboard",
    "compliance-product": "https://seller.us.tiktokshopglobalselling.com/compliance/product",
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
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                sidebar: Array.from(document.querySelectorAll('.core-menu-item')).map(el => el.innerText.trim()).filter(t => t.length > 0)
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

    for name, url in US_URL_PATTERNS.items():
        print(f"\n### {name} ###")
        print(f"  URL: {url}")
        try:
            page.goto(url, timeout=40000, wait_until="domcontentloaded")
            data = extract(page, wait=15)

            print(f"  Title: {data.get('title')}")
            print(f"  Final URL: {data.get('url')}")
            print(f"  Sidebar: {data.get('sidebar', [])}")
            print(f"  Tabs: {data.get('tabs', [])[:6]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:8]}")
            print(f"  Headings: {data.get('headings', [])[:5]}")
            print(f"  Text: {data.get('main_text', '')[:200]}")

            ss_name = f"us_{name}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[name] = {**data, "tested_url": url}

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = {"error": str(e), "tested_url": url}

        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "us_correct_urls.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== Done === Saved: {out_file}")
    browser.close()
