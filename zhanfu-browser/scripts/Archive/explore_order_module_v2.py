#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore order module with screenshot + full page text extraction."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

def extract_full(page, wait=12):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 10000),
                tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item")).map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                table_headers: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean)).filter(h => h.length > 0),
                buttons: Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                inputs: Array.from(document.querySelectorAll("input")).filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                iframes: Array.from(document.querySelectorAll("iframe")).map(f => f.src)
            });
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

ORDER_URLS = {
    # 订单管理 - the main order page
    "order-manage": "https://seller.us.tiktokshopglobalselling.com/order/manage",
    "order-list": "https://seller.us.tiktokshopglobalselling.com/order/list",
    "order-all": "https://seller.us.tiktokshopglobalselling.com/order/all",
    "order-pending": "https://seller.us.tiktokshopglobalselling.com/order/pending",
    # 物流相关
    "logistics-manage": "https://seller.us.tiktokshopglobalselling.com/logistics/manage",
    "logistics-list": "https://seller.us.tiktokshopglobalselling.com/logistics/list",
    # 发货
    "batch-ship": "https://seller.us.tiktokshopglobalselling.com/order/batch-ship",
    "ship-list": "https://seller.us.tiktokshopglobalselling.com/shipment/list",
    # 取消
    "order-cancel": "https://seller.us.tiktokshopglobalselling.com/order/cancel",
    # 履约
    "fulfillment-perf": "https://seller.us.tiktokshopglobalselling.com/fulfillment/performance",
    "fulfillment-setting": "https://seller.us.tiktokshopglobalselling.com/fulfillment/setting",
    # 包邮/退货设置
    "free-shipping": "https://seller.us.tiktokshopglobalselling.com/shipping/free",
    "return-setting": "https://seller.us.tiktokshopglobalselling.com/return/setting",
    "return-list": "https://seller.us.tiktokshopglobalselling.com/return/list",
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    all_results = {}

    for name, url in ORDER_URLS.items():
        print(f"\n### {name} ###")
        print(f"  URL: {url}")
        try:
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            data = extract_full(page, wait=15)

            print(f"  Title: {data.get('title')}")
            print(f"  URL: {data.get('url')}")
            print(f"  Iframes: {data.get('iframes', [])}")
            print(f"  Tabs: {data.get('tabs', [])[:8]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:10]}")
            print(f"  Inputs: {data.get('inputs', [])[:8]}")
            print(f"  Headings: {data.get('headings', [])[:5]}")
            print(f"  Text (first 500): {data.get('main_text', '')[:500]}")

            ss_name = f"order_{name}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[name] = {**data, "tested_url": url}

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = {"error": str(e), "tested_url": url}

        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "order_explore_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== Done === Saved: {out_file}")
    browser.close()
