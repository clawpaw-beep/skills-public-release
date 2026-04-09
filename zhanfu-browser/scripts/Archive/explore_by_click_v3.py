#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore by clicking sidebar - fixed click logic with proper waiting."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def get_all_menu_texts(page):
    """Get all menu item texts."""
    try:
        items = page.evaluate("""() => {
            var items = document.querySelectorAll('.core-menu-item');
            return Array.from(items).map(function(el) {
                return el.innerText.trim();
            }).filter(function(t) { return t.length > 0 && t.length < 100; });
        }""")
        return json.loads(items) if isinstance(items, str) else items
    except:
        return []

def find_and_click(page, text, timeout=5000):
    """Find menu item by text and click it."""
    try:
        # Get all menu items and their indices
        menu_data = page.evaluate("""() => {
            var items = document.querySelectorAll('.core-menu-item');
            var result = [];
            items.forEach(function(el, i) {
                result.push({text: el.innerText.trim(), index: i});
            });
            return JSON.stringify(result);
        }""")
        menu_items = json.loads(menu_data)

        # Find matching item
        for item in menu_items:
            if text in item['text']:
                idx = item['index']
                # Use JavaScript click to avoid issues
                page.evaluate(f"""() => {{
                    var items = document.querySelectorAll('.core-menu-item');
                    if (items[{idx}]) {{
                        items[{idx}].click();
                    }}
                }}""")
                print(f"  Clicked: {item['text'][:50]}")
                return True
        print(f"  NOT FOUND: {text}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def extract(page, wait=6):
    """Extract page content."""
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 5000),
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
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

def explore_all():
    print("=== 通过点击探索所有子模块 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start at product list
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(6)
        print(f"Baseline: {page.url}")

        all_results = {}

        # Define all modules and their sub-items
        modules = {
            "广告营销": ["触达", "客户群", "促销活动", "店铺广告", "智能营销", "店铺页面"],
            "数据分析": ["店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析", "营销数据分析", "客户数据分析", "排行榜", "售后数据分析"],
            "订单": ["管理订单", "批量发货", "管理物流", "管理取消申请", "管理退货", "履约表现", "包邮", "退货设置"],
            "成长中心": ["经营洞察", "成长权益", "我的任务", "我的奖励"],
            "合规中心": ["合规看板", "合规资质", "商品合规诊断"],
            "账号健康": ["店铺健康", "店铺体验分", "达人健康评分", "明星商家认证计划"],
            "财务": ["财务概览", "保证金", "收益数据分析", "账单", "钱包"]
        }

        for parent, subs in modules.items():
            print(f"\n\n===== {parent} =====")

            for sub in subs:
                print(f"\n--- {parent} > {sub} ---")

                # First click parent to expand
                find_and_click(page, parent)
                time.sleep(3)

                # Then click sub-item
                found = find_and_click(page, sub)
                if found:
                    time.sleep(8)  # Wait for content to load
                    data = extract(page, wait=6)
                    data["parent"] = parent
                    data["clicked"] = sub

                    print(f"  URL: {data.get('url', 'N/A')}")
                    print(f"  Title: {data.get('title', 'N/A')}")
                    print(f"  Tabs ({len(data.get('tabs', []))}): {data.get('tabs', [])[:6]}")
                    print(f"  Tables ({len(data.get('table_headers', []))}): {data.get('table_headers', [])}")
                    print(f"  Buttons ({len(data.get('buttons', []))}): {data.get('buttons', [])[:8]}")
                    print(f"  Headings ({len(data.get('headings', []))}): {data.get('headings', [])[:5]}")
                    print(f"  Main text: {data.get('main_text', '')[:200]}")

                    ss_name = f"v3_{parent}_{sub}_{int(time.time())}.png"
                    page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
                    print(f"  Screenshot: {ss_name}")

                    all_results[f"{parent}>{sub}"] = data
                else:
                    all_results[f"{parent}>{sub}"] = {"error": "Menu item not found", "parent": parent, "clicked": sub}

                time.sleep(3)

        # Save results
        out_file = os.path.join(OUTPUT_DIR, "click_explore_v3_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file}")
        print(f"Modules: {len(all_results)}")

        browser.close()

if __name__ == "__main__":
    explore_all()
