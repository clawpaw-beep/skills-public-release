#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore TikTok Shop modules with LONGER wait times for slow external network."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def safe_extract(page, wait_sec=8):
    """Extract page content after waiting for load."""
    time.sleep(wait_sec)
    try:
        data = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 3000),
                tabs: [],
                table_headers: [],
                buttons: [],
                inputs: []
            });
        }""")
        more = page.evaluate("""() => {
            var result = {tabs: [], table_headers: [], buttons: [], inputs: []};
            var tabs = document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item");
            tabs.forEach(function(t) {
                var text = t.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.tabs.push(text);
            });
            var tables = document.querySelectorAll("table");
            tables.forEach(function(t, i) {
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
        result = json.loads(data)
        result.update(json.loads(more))
        return result
    except Exception as e:
        return {"error": str(e)}

def explore_page(page, url, name):
    """Navigate to URL and extract."""
    print(f"\n### {name} ###")
    print(f"  URL: {url}")
    try:
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        # Wait longer for external network
        data = safe_extract(page, wait_sec=10)
        print(f"  Title: {data.get('title', 'N/A')}")
        print(f"  URL after: {data.get('url', 'N/A')}")
        print(f"  Tabs: {data.get('tabs', [])[:8]}")
        print(f"  Tables: {data.get('table_headers', [])}")
        print(f"  Buttons: {data.get('buttons', [])[:10]}")
        print(f"  Main text: {data.get('main_text', '')[:200]}")
        ss_name = f"{name.replace('/', '_')}_{int(time.time())}.png"
        page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
        print(f"  Screenshot: {ss_name}")
        return data
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"error": str(e)}

def main():
    print("=== TikTok Shop 慢速网络探索 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # First establish baseline
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(8)
        print(f"Baseline: {page.url}")

        # Retry modules that failed or need longer load
        modules = [
            ("订单管理", "https://seller.us.tiktokshopglobalselling.com/order/manage"),
            ("订单列表", "https://seller.us.tiktokshopglobalselling.com/order/list"),
            ("物流管理", "https://seller.us.tiktokshopglobalselling.com/logistics/manage"),
            ("合规看板_retry", "https://seller.us.tiktokshopglobalselling.com/compliance/overview"),
            ("触达_retry", "https://seller.us.tiktokshopglobalselling.com/marketing/reach"),
            ("促销活动_retry", "https://seller.us.tiktokshopglobalselling.com/marketing/promotion"),
            ("店铺健康_retry", "https://seller.us.tiktokshopglobalselling.com/accountHealth/overview"),
            ("客户群_retry", "https://seller.us.tiktokshopglobalselling.com/buyer/manage"),
            ("财务详情", "https://seller.us.tiktokshopglobalselling.com/finance/reconciliation"),
            ("我的任务_retry", "https://seller.us.tiktokshopglobalselling.com/growth/task"),
            ("成长权益_retry", "https://seller.us.tiktokshopglobalselling.com/growth/benefits"),
            ("数据分析", "https://seller.us.tiktokshopglobalselling.com/analytics/orders"),
            ("退款管理", "https://seller.us.tiktokshopglobalselling.com/order/refund"),
        ]

        all_results = {}
        for name, url in modules:
            result = explore_page(page, url, name)
            all_results[name] = result
            time.sleep(2)

        # Save
        out_file = os.path.join(OUTPUT_DIR, "retry_explore_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file}")

        browser.close()

if __name__ == "__main__":
    main()
