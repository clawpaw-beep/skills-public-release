#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore modules by clicking sidebar menu items - more reliable than direct URL."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def get_menu_item_text(page, selector):
    """Get text content from element."""
    try:
        el = page.query_selector(selector)
        if el:
            return el.inner_text().strip()
    except:
        pass
    return ""

def click_menu_and_extract(page, menu_text, max_wait=5):
    """Click a menu item and extract the page content."""
    try:
        # Find the menu item by text
        menu_items = page.query_selector_all(".core-menu-item")
        target = None
        for item in menu_items:
            if menu_text in item.inner_text():
                target = item
                break

        if not target:
            return {"error": f"Menu item '{menu_text}' not found"}

        print(f"  Clicking: {menu_text}")
        target.click()
        time.sleep(max_wait)

        # Extract page content after click
        content = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 2000),
                tabs: [],
                table_headers: [],
                buttons: [],
                inputs: []
            };

            // Tabs
            var tabs = document.querySelectorAll("[role='tab'], .ant-tabs-tab");
            tabs.forEach(function(t) {
                var text = t.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.tabs.push(text);
            });

            // Tables
            var tables = document.querySelectorAll("table");
            tables.forEach(function(t, i) {
                var headers = Array.from(t.querySelectorAll("th")).map(function(h) { return h.textContent.trim(); }).filter(Boolean);
                if (headers.length > 0) result.table_headers.push(headers);
            });

            // Buttons
            var btns = document.querySelectorAll("button");
            btns.forEach(function(b) {
                var text = b.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.buttons.push(text);
            });

            // Inputs
            var inps = document.querySelectorAll("input");
            inps.forEach(function(i) {
                if (i.placeholder) result.inputs.push({type: i.type || "text", placeholder: i.placeholder});
            });

            return JSON.stringify(result);
        }""")

        return json.loads(content)

    except Exception as e:
        return {"error": str(e)}

def main():
    print("=== 通过点击菜单探索各模块 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start from product list page (where sidebar is confirmed working)
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=40000, wait_until="domcontentloaded")
        time.sleep(3)
        print(f"Starting URL: {page.url}")

        # Menu items to explore (from the confirmed 60-item sidebar)
        menu_items_to_explore = [
            "管理订单",
            "管理物流",
            "促销活动",
            "触达",
            "联盟",
            "带货视频",
            "直播管理平台",
            "店铺数据分析",
            "财务概览",
            "店铺健康",
            "合规看板",
            "商品评分",
        ]

        results = {}
        for menu_text in menu_items_to_explore:
            print(f"\n### 探索: {menu_text} ###")
            result = click_menu_and_extract(page, menu_text)
            results[menu_text] = result

            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  标题: {result.get('title', 'N/A')}")
            print(f"  标签页: {result.get('tabs', [])[:5]}")
            print(f"  表格: {result.get('table_headers', [])}")
            print(f"  按钮: {result.get('buttons', [])[:8]}")
            print(f"  输入框: {result.get('inputs', [])[:5]}")

            # Screenshot
            ss_name = f"click_{menu_text.replace(' ', '_')}_{int(time.time())}.png"
            ss_path = os.path.join(OUTPUT_DIR, ss_name)
            page.screenshot(path=ss_path, full_page=True)

            # Small delay between clicks
            time.sleep(1)

        # Save all results
        output_file = os.path.join(OUTPUT_DIR, "菜单点击探索结果.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 ===")
        print(f"结果: {output_file}")

        browser.close()

if __name__ == "__main__":
    main()
