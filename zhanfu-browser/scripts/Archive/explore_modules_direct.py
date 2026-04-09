#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore modules by direct URL with longer wait times."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def explore_page(page, url, name):
    """Navigate to URL and extract page content."""
    print(f"\n### {name} ###")
    print(f"  URL: {url}")

    try:
        page.goto(url, timeout=35000, wait_until="domcontentloaded")
        time.sleep(5)  # Wait for dynamic content

        # Get page info
        page_info = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 3000),
                tabs: [],
                table_headers: [],
                buttons: [],
                inputs: [],
                headings: []
            });
        }""")

        data = json.loads(page_info)

        # Extract more specific content
        more_data = page.evaluate("""() => {
            var result = {tabs: [], table_headers: [], buttons: [], inputs: [], headings: []};

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

            var hs = document.querySelectorAll("h1, h2, h3, h4");
            hs.forEach(function(h) {
                var text = h.textContent.trim();
                if (text && text.length < 200) result.headings.push(text);
            });

            return JSON.stringify(result);
        }""")

        more = json.loads(more_data)
        data.update(more)

        print(f"  Title: {data.get('title', 'N/A')}")
        print(f"  URL after load: {data.get('url', 'N/A')}")
        print(f"  Tabs: {data.get('tabs', [])[:10]}")
        print(f"  Tables: {data.get('table_headers', [])}")
        print(f"  Buttons: {data.get('buttons', [])[:10]}")
        print(f"  Inputs: {data.get('inputs', [])[:8]}")
        print(f"  Headings: {data.get('headings', [])[:10]}")
        print(f"  Main text preview: {data.get('main_text', '')[:300]}")

        # Screenshot
        ss_name = f"{name}_{int(time.time())}.png"
        ss_path = os.path.join(OUTPUT_DIR, ss_name)
        page.screenshot(path=ss_path, full_page=True)
        print(f"  Screenshot: {ss_path}")

        return data

    except Exception as e:
        print(f"  ERROR: {e}")
        return {"error": str(e), "url": url}

def main():
    print("=== TikTok Shop 模块直接探索 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # First go to product list to establish baseline
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=40000, wait_until="domcontentloaded")
        time.sleep(3)
        print(f"Baseline URL: {page.url}")

        # Modules to explore with known working URLs
        modules = [
            # From the 60-item sidebar, these have URL patterns we can try
            ("联盟", "https://seller.us.tiktokshopglobalselling.com/affiliate/landing"),
            ("商品评分", "https://seller.us.tiktokshopglobalselling.com/product/rating"),
            ("财务概览", "https://seller.us.tiktokshopglobalselling.com/finance/overview"),
            ("店铺健康", "https://seller.us.tiktokshopglobalselling.com/accountHealth/overview"),
            ("合规看板", "https://seller.us.tiktokshopglobalselling.com/compliance/overview"),
            ("触达", "https://seller.us.tiktokshopglobalselling.com/marketing/reach"),
            ("促销活动", "https://seller.us.tiktokshopglobalselling.com/marketing/promotion"),
            ("客户群", "https://seller.us.tiktokshopglobalselling.com/buyer/group"),
            ("直播管理平台", "https://seller.us.tiktokshopglobalselling.com/live/manage"),
            ("带货视频", "https://seller.us.tiktokshopglobalselling.com/video/affiliate"),
            ("我的任务", "https://seller.us.tiktokshopglobalselling.com/growth/task"),
            ("成长权益", "https://seller.us.tiktokshopglobalselling.com/growth/benefits"),
            ("应用商店", "https://seller.us.tiktokshopglobalselling.com/appstore"),
        ]

        all_results = {}
        for name, url in modules:
            result = explore_page(page, url, name)
            all_results[name] = result

            # Save individual result
            out_file = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            time.sleep(1)

        # Save combined
        combined_file = os.path.join(OUTPUT_DIR, "direct_explore_results.json")
        with open(combined_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"\n=== 完成 ===")
        print(f"Combined: {combined_file}")
        print(f"Modules explored: {len(all_results)}")

        browser.close()

if __name__ == "__main__":
    main()
