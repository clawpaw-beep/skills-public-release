#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore 广告营销 and 数据分析 by clicking each of the 61 menu items."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def get_menu_items(page):
    """Get all 61 menu items with their text."""
    try:
        result = page.evaluate("""() => {
            var items = document.querySelectorAll('.core-menu-item');
            var result = [];
            for (var i = 0; i < items.length; i++) {
                var el = items[i];
                result.push({
                    i: i,
                    text: el.innerText.trim(),
                    cls: el.className
                });
            }
            return JSON.stringify(result);
        }""")
        return json.loads(result)
    except:
        return []

def click_by_index(page, idx):
    """Click menu item by index."""
    try:
        r = page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            if (items[{idx}]) {{ items[{idx}].click(); return 'ok'; }}
            return 'fail';
        }}""")
        return r == 'ok'
    except:
        return False

def extract(page, wait=8):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 4000),
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

def main():
    print("=== 探索广告营销 + 数据分析 ===")

    # Target items we want
    targets = [
        # 广告营销
        "触达", "客户群", "促销活动", "店铺广告", "智能营销", "店铺页面",
        # 数据分析
        "店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析",
        "营销数据分析", "客户数据分析", "排行榜", "售后数据分析",
        # 账号健康
        "店铺健康", "店铺体验分", "达人健康评分",
        # 合规
        "合规看板", "合规资质", "商品合规诊断",
        # 成长
        "经营洞察", "成长权益", "我的任务", "我的奖励",
        # 财务
        "财务概览", "保证金", "收益数据分析", "账单", "钱包"
    ]

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start at product/list (known working page)
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(10)
        print(f"Starting URL: {page.url}")

        # Build text -> index map from all 61 items
        all_items = get_menu_items(page)
        print(f"Total menu items: {len(all_items)}")

        # Build lookup
        text_to_idx = {}
        for item in all_items:
            t = item['text']
            if t:
                text_to_idx[t] = item['i']

        # Show items with text
        print("\nItems with text:")
        for item in all_items:
            if item['text']:
                print(f"  [{item['i']}] '{item['text']}'")

        all_results = {}

        for target in targets:
            print(f"\n--- 探索: {target} ---")

            # Check if we have this text in our map
            idx = text_to_idx.get(target)

            if idx is None:
                # Try partial match
                for item in all_items:
                    if target in item['text']:
                        idx = item['i']
                        print(f"  Partial match: [{idx}] '{item['text']}'")
                        break

            if idx is None:
                print(f"  NOT FOUND in menu")
                all_results[target] = {"error": "NOT FOUND in menu", "clicked": target}
                continue

            print(f"  Clicking index {idx} ('{all_items[idx]['text']}')...")

            clicked = click_by_index(page, idx)
            if not clicked:
                print(f"  Click failed")
                all_results[target] = {"error": "Click failed", "clicked": target, "index": idx}
                continue

            time.sleep(10)

            data = extract(page, wait=6)
            data["clicked"] = target
            data["index"] = idx

            print(f"  URL: {data.get('url')}")
            print(f"  Title: {data.get('title')}")
            print(f"  Tabs: {data.get('tabs', [])[:6]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:8]}")
            print(f"  Headings: {data.get('headings', [])[:5]}")
            print(f"  Text: {data.get('main_text', '')[:150]}")

            ss_name = f"ad_ana_{target[:6]}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[target] = data
            time.sleep(3)

        # Save
        out_file = os.path.join(OUTPUT_DIR, "ad_analytics_explore.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file} ({len(all_results)} items)")

        browser.close()

if __name__ == "__main__":
    main()
