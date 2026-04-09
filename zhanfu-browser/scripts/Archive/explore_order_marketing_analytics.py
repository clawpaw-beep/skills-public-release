#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep explore: 订单、广告营销、数据分析 modules with longer waits."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def extract_full(page, wait=10):
    """Extract full page content with longer wait."""
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 4000),
                tabs: [], table_headers: [], buttons: [], inputs: [],
                iframes: [], headings: [], cards: []
            };

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

            var iframes = document.querySelectorAll("iframe");
            result.iframes = Array.from(iframes).map(function(f) { return f.src; });

            var hs = document.querySelectorAll("h1, h2, h3, h4");
            hs.forEach(function(h) {
                var text = h.textContent.trim();
                if (text && text.length < 200) result.headings.push(text);
            });

            var cards = document.querySelectorAll("[class*='card'], [class*='metric'], [class*='stat']");
            cards.forEach(function(c) {
                var text = c.textContent.trim().substring(0, 80);
                if (text && text.length > 5) result.cards.push(text);
            });

            return JSON.stringify(result);
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

def explore(module_name, urls):
    """Explore multiple URLs for one module."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Go to base page first
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(8)

        for name, url in urls:
            print(f"\n### {module_name} - {name} ###")
            print(f"  URL: {url}")
            try:
                page.goto(url, timeout=45000, wait_until="domcontentloaded")
                data = extract_full(page, wait=12)

                print(f"  Title: {data.get('title', 'N/A')}")
                print(f"  URL: {data.get('url', 'N/A')}")
                print(f"  Tabs ({len(data.get('tabs', []))}): {data.get('tabs', [])[:8]}")
                print(f"  Tables ({len(data.get('table_headers', []))}): {data.get('table_headers', [])}")
                print(f"  Buttons ({len(data.get('buttons', []))}): {data.get('buttons', [])[:12]}")
                print(f"  Inputs ({len(data.get('inputs', []))}): {data.get('inputs', [])[:8]}")
                print(f"  Headings ({len(data.get('headings', []))}): {data.get('headings', [])[:8]}")
                print(f"  Iframes: {data.get('iframes', [])}")
                print(f"  Main text: {data.get('main_text', '')[:300]}")

                ss_name = f"{module_name}_{name.replace('/', '_')}_{int(time.time())}.png"
                page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
                print(f"  Screenshot: {ss_name}")

                results.append({**data, "explored_as": name, "url": url})

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({"explored_as": name, "url": url, "error": str(e)})

            time.sleep(3)

        browser.close()

    return results

def main():
    print("=== 深挖：订单 + 广告营销 + 数据分析 ===")

    all_results = {}

    # 订单模块 - 尝试多种URL
    order_urls = [
        ("订单-管理", "https://seller.us.tiktokshopglobalselling.com/order/manage"),
        ("订单-列表", "https://seller.us.tiktokshopglobalselling.com/order/list"),
        ("订单-批量发货", "https://seller.us.tiktokshopglobalselling.com/order/batch-ship"),
        ("订单-取消管理", "https://seller.us.tiktokshopglobalselling.com/order/cancel"),
        ("订单-退货管理", "https://seller.us.tiktokshopglobalselling.com/order/return"),
        ("订单-履约", "https://seller.us.tiktokshopglobalselling.com/fulfillment/performance"),
    ]
    print("\n### 探索订单模块 ###")
    all_results["订单"] = explore("订单", order_urls)

    # 广告营销模块
    marketing_urls = [
        ("营销-概览", "https://seller.us.tiktokshopglobalselling.com/marketing/overview"),
        ("营销-促销活动", "https://seller.us.tiktokshopglobalselling.com/marketing/promotion"),
        ("营销-触达", "https://seller.us.tiktokshopglobalselling.com/marketing/reach"),
        ("营销-广告", "https://seller.us.tiktokshopglobalselling.com/marketing/ad"),
        ("营销-智能营销", "https://seller.us.tiktokshopglobalselling.com/marketing/smart"),
        ("店铺广告", "https://seller.us.tiktokshopglobalselling.com/shop-ad/overview"),
    ]
    print("\n### 探索广告营销模块 ###")
    all_results["广告营销"] = explore("广告营销", marketing_urls)

    # 数据分析模块
    analytics_urls = [
        ("分析-概览", "https://seller.us.tiktokshopglobalselling.com/analytics/overview"),
        ("分析-店铺", "https://seller.us.tiktokshopglobalselling.com/analytics/store"),
        ("分析-订单", "https://seller.us.tiktokshopglobalselling.com/analytics/orders"),
        ("分析-商品", "https://seller.us.tiktokshopglobalselling.com/analytics/product"),
        ("分析-营销", "https://seller.us.tiktokshopglobalselling.com/analytics/marketing"),
        ("分析-客户", "https://seller.us.tiktokshopglobalselling.com/analytics/customer"),
    ]
    print("\n### 探索数据分析模块 ###")
    all_results["数据分析"] = explore("数据分析", analytics_urls)

    # Save
    out_file = os.path.join(OUTPUT_DIR, "deep_explore_order_marketing_analytics.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 === Saved: {out_file}")

if __name__ == "__main__":
    main()
