#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retry failed URLs with MUCH longer delays and rate limit protection."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def extract(page, wait=12):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 4000),
                tabs: [], table_headers: [], buttons: [], inputs: []
            };
            var tabs = document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item");
            tabs.forEach(function(t) {
                var text = t.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.tabs.push(text);
            });
            var tables = document.querySelectorAll("table");
            tables.forEach(function(t) {
                var headers = Array.from(t.querySelectorAll("th")).map(function(h) { return h.textContent.trim(); }).filter(Boolean);
                if (headers.length > 0) result.table_headers.push(headers);
            });
            var btns = document.querySelectorAll("button");
            btns.forEach(function(b) {
                var text = b.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.buttons.push(text);
            });
            var inps = document.querySelectorAll("input");
            inps.forEach(function(i) {
                if (i.placeholder) result.inputs.push({type: i.type || "text", placeholder: i.placeholder});
            });
            return JSON.stringify(result);
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

def retry_single(page, name, url):
    print(f"\n### {name} ###")
    print(f"  URL: {url}")
    try:
        # First go to a neutral page to "reset" state
        page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(10)  # Long pause before retry

        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        data = extract(page, wait=15)  # Long wait for content

        print(f"  Title: {data.get('title', 'N/A')}")
        print(f"  URL: {data.get('url', 'N/A')}")
        print(f"  Tabs: {data.get('tabs', [])[:8]}")
        print(f"  Tables: {data.get('table_headers', [])}")
        print(f"  Buttons: {data.get('buttons', [])[:10]}")
        print(f"  Main text: {data.get('main_text', '')[:200]}")

        ss_name = f"retry_{name.replace('/', '_')}_{int(time.time())}.png"
        page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
        print(f"  Screenshot: {ss_name}")

        return data
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"error": str(e)}

def main():
    print("=== 重试失败URL（长等待）===")

    failed_urls = [
        ("数据分析-概览", "https://seller.us.tiktokshopglobalselling.com/analytics/overview"),
        ("数据分析-订单", "https://seller.us.tiktokshopglobalselling.com/analytics/orders"),
        ("数据分析-商品", "https://seller.us.tiktokshopglobalselling.com/analytics/product"),
        ("数据分析-店铺", "https://seller.us.tiktokshopglobalselling.com/analytics/store"),
        ("触达", "https://seller.us.tiktokshopglobalselling.com/marketing/reach"),
        ("促销活动", "https://seller.us.tiktokshopglobalselling.com/marketing/promotion"),
        ("智能营销", "https://seller.us.tiktokshopglobalselling.com/marketing/smart"),
        ("店铺广告", "https://seller.us.tiktokshopglobalselling.com/shop-ad/overview"),
        ("客户群", "https://seller.us.tiktokshopglobalselling.com/buyer/manage"),
        ("成长中心-任务", "https://seller.us.tiktokshopglobalselling.com/growth/task"),
        ("成长中心-权益", "https://seller.us.tiktokshopglobalselling.com/growth/benefits"),
        ("合规看板", "https://seller.us.tiktokshopglobalselling.com/compliance/overview"),
    ]

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        for name, url in failed_urls:
            result = retry_single(page, name, url)
            results[name] = result
            time.sleep(5)  # 5秒间隔，避免频繁请求

        browser.close()

    out_file = os.path.join(OUTPUT_DIR, "retry_failed_urls.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 === Saved: {out_file}")

if __name__ == "__main__":
    main()
