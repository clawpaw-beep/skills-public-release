#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final exploration - use saved menu data with long waits."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

# Read menu items from saved JSON (correctly encoded)
with open(r"C:\Users\9400\Documents\zhanfu_module_explore_20260407\product_module_menu.json", "r", encoding="utf-8") as f:
    saved_menu = json.load(f)

# Build lookup by text
menu_items = saved_menu["items"]  # [{text, href, tag, cls}, ...]
print(f"Loaded {len(menu_items)} menu items from saved file")
print("First 5:", [it["text"] for it in menu_items[:5]])

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate once
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(15)  # Long wait for SPA to fully render
    print(f"Baseline: {page.url}")

    all_results = {}

    # Items to explore (text -> sub-item mapping)
    items_to_explore = [
        "触达", "客户群", "促销活动", "店铺广告", "智能营销", "店铺页面",
        "管理订单", "批量发货", "管理物流", "管理取消申请", "管理退货",
        "履约表现", "包邮", "退货设置",
        "经营洞察", "成长权益", "我的任务", "我的奖励",
        "店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析",
        "营销数据分析", "客户数据分析", "排行榜", "售后数据分析",
        "店铺健康", "店铺体验分", "达人健康评分", "明星商家认证计划",
        "合规看板", "合规资质", "商品合规诊断",
        "财务概览", "保证金", "收益数据分析", "账单", "钱包"
    ]

    for item_text in items_to_explore:
        print(f"\n--- 探索: {item_text} ---")

        # Refresh page each time to ensure clean state
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(15)  # Long wait for SPA

        # Find index
        idx = None
        for i, it in enumerate(menu_items):
            if item_text in it["text"]:
                idx = i
                print(f"  Found '{it['text']}' at index {i}")
                break

        if idx is None:
            print(f"  NOT FOUND in saved menu")
            all_results[item_text] = {"error": "NOT FOUND in saved menu", "clicked": item_text}
            continue

        # Click by index
        page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            if (items[{idx}]) items[{idx}].click();
        }}""")
        print(f"  Clicked at index {idx}")
        time.sleep(12)  # Wait for navigation/content

        # Extract
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 3000),
                tabs: [], table_headers: [], buttons: [], inputs: [], headings: []
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
            var hs = document.querySelectorAll("h1, h2, h3, h4");
            hs.forEach(function(h) {
                var text = h.textContent.trim();
                if (text && text.length < 200) result.headings.push(text);
            });
            return JSON.stringify(result);
        }""")
        result = json.loads(data)
        result["clicked"] = item_text

        print(f"  URL: {result.get('url')}")
        print(f"  Title: {result.get('title')}")
        print(f"  Tabs: {result.get('tabs', [])[:6]}")
        print(f"  Tables: {result.get('table_headers', [])}")
        print(f"  Buttons: {result.get('buttons', [])[:8]}")
        print(f"  Headings: {result.get('headings', [])[:5]}")
        print(f"  Main text: {result.get('main_text', '')[:150]}")

        ss_name = f"final_{item_text[:6]}_{int(time.time())}.png"
        page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
        print(f"  Screenshot: {ss_name}")

        all_results[item_text] = result
        time.sleep(3)

    # Save all
    out_file = os.path.join(OUTPUT_DIR, "final_submenu_explore.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 === Saved: {out_file} ({len(all_results)} items)")

    browser.close()
