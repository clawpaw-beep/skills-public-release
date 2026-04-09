#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Robust click exploration - re-query sidebar before EVERY click."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def find_menu_item(page, search_text):
    """Find menu item index by text, re-querying each time."""
    try:
        result_str = page.evaluate(
            """(text) => {
                var items = document.querySelectorAll('.core-menu-item');
                for (var i = 0; i < items.length; i++) {
                    if (items[i].innerText.trim().includes(text)) {
                        return JSON.stringify({found: true, index: i, text: items[i].innerText.trim()});
                    }
                }
                return JSON.stringify({found: false});
            }""",
            text=search_text
        )
        return json.loads(result_str)
    except Exception as e:
        return {"found": False, "error": str(e)}

def extract(page, wait=8):
    time.sleep(wait)
    try:
        data_str = page.evaluate("""() => {
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
        return json.loads(data_str)
    except Exception as e:
        return {"error": str(e)}

def click_by_index(page, idx):
    """Click menu item by index."""
    try:
        result_str = page.evaluate(
            """(i) => {
                var items = document.querySelectorAll('.core-menu-item');
                if (items[i]) {
                    items[i].click();
                    return 'clicked';
                }
                return 'not_found';
            }""",
            i=idx
        )
        return result_str == 'clicked'
    except:
        return False

def main():
    print("=== 稳健点击探索（每次重新查询菜单）===")

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

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start at affiliate/landing (which worked before)
        page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(10)
        print(f"Starting: {page.url}")

        all_results = {}
        skipped = []

        for item_text in items_to_explore:
            print(f"\n--- 探索: {item_text} ---")

            # Step 1: Re-query sidebar to find current index
            find_result = find_menu_item(page, item_text)

            if not find_result.get("found"):
                print(f"  菜单中未找到: {item_text}")
                all_results[item_text] = {"error": "NOT FOUND in sidebar", "clicked": item_text}
                skipped.append(item_text)

                # Try reloading the page to get fresh sidebar
                page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing",
                          timeout=45000, wait_until="domcontentloaded")
                time.sleep(8)
                continue

            idx = find_result["index"]
            print(f"  找到索引: {idx}, 文本: {find_result['text'][:30]}")

            # Step 2: Click by index
            clicked = click_by_index(page, idx)
            if not clicked:
                print(f"  点击失败")
                all_results[item_text] = {"error": "Click failed", "clicked": item_text}
                continue

            print(f"  点击成功，等待内容加载...")
            time.sleep(12)  # Wait for SPA to update content

            # Step 3: Extract
            data = extract(page, wait=6)
            data["clicked"] = item_text
            data["found_at_index"] = idx

            print(f"  URL: {data.get('url')}")
            print(f"  Title: {data.get('title')}")
            print(f"  Tabs: {data.get('tabs', [])[:6]}")
            print(f"  Tables: {data.get('table_headers', [])}")
            print(f"  Buttons: {data.get('buttons', [])[:8]}")
            print(f"  Headings: {data.get('headings', [])[:5]}")
            print(f"  Text: {data.get('main_text', '')[:150]}")

            ss_name = f"robust_{item_text[:6]}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

            all_results[item_text] = data
            time.sleep(3)

        # Save
        out_file = os.path.join(OUTPUT_DIR, "robust_explore_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file}")
        print(f"Explored: {len(all_results) - len(skipped)}")
        print(f"Skipped: {len(skipped)} - {skipped}")

        browser.close()

if __name__ == "__main__":
    main()
