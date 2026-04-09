#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Click submenu items - no parent expansion needed, just click directly."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def find_and_click(page, text):
    """Find menu item by partial text match and click it."""
    try:
        result = page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            for (var i = 0; i < items.length; i++) {{
                var el = items[i];
                if (el.innerText.trim().includes('{text}')) {{
                    el.click();
                    return JSON.stringify({{found: true, text: el.innerText.trim()}});
                }}
            }}
            return JSON.stringify({{found: false}});
        }}""")
        data = json.loads(result)
        if data.get('found'):
            print(f"  Clicked: {data['text'][:50]}")
            return True
        print(f"  NOT FOUND: {text}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def extract(page, wait=6):
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

def main():
    print("=== 点击子菜单项探索（直接点击，无需展开父级）===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start at a neutral page
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(6)
        print(f"Starting: {page.url}")

        all_results = {}

        # Define all sub-menu items to click
        # These are ALL direct clicks - no parent expansion needed
        # Based on the 60-item sidebar
        items_to_explore = [
            # 商品 sub-items
            "管理订单", "批量发货", "管理物流", "管理取消申请", "管理退货",
            "履约表现", "包邮", "退货设置", "仓库管理", "履约设置",
            "物流服务", "Fulfilled by TikTok（FBT）",
            # 促销营销 sub-items
            "触达", "客户群",
            # 联盟 sub-items (from affiliate landing)
            "带货视频", "直播管理平台",
            # 成长中心 sub-items
            "经营洞察", "成长权益", "我的任务", "我的奖励",
            # 应用和服务商 sub-items
            "TikTok Shop 服务商", "物流服务市场",
            # 数据分析 sub-items
            "店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析",
            "营销数据分析", "客户数据分析", "排行榜", "售后数据分析",
            # 账号健康 sub-items
            "店铺健康", "店铺体验分", "达人健康评分", "明星商家认证计划",
            # 合规 sub-items
            "合规看板", "合规资质", "商品合规诊断",
            # 财务 sub-items
            "财务概览", "保证金", "收益数据分析", "账单", "钱包"
        ]

        for item_text in items_to_explore:
            print(f"\n--- 探索: {item_text} ---")

            # Go to base page first
            page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                      timeout=45000, wait_until="domcontentloaded")
            time.sleep(5)

            found = find_and_click(page, item_text)
            if found:
                time.sleep(8)
                data = extract(page, wait=5)
                data["clicked"] = item_text

                print(f"  URL: {data.get('url', 'N/A')}")
                print(f"  Title: {data.get('title', 'N/A')}")
                print(f"  Tabs: {data.get('tabs', [])[:6]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:8]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Text: {data.get('main_text', '')[:150]}")

                ss_name = f"sub_{item_text[:8]}_{int(time.time())}.png"
                page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
                print(f"  SS: {ss_name}")

                all_results[item_text] = data
            else:
                all_results[item_text] = {"error": "NOT FOUND", "clicked": item_text}

            time.sleep(3)

        out_file = os.path.join(OUTPUT_DIR, "submenu_click_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file} ({len(all_results)} items)")

        browser.close()

if __name__ == "__main__":
    main()
