#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test clicking Chinese menu items with proper encoding."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

# All menu texts we want to click - read from the already-saved JSON
def get_menu_items_to_click():
    return [
        # 订单相关
        "管理订单", "批量发货", "管理物流", "管理取消申请", "管理退货",
        "履约表现", "包邮", "退货设置",
        # 促销营销
        "触达", "客户群", "促销活动", "店铺广告", "智能营销", "店铺页面",
        # 成长
        "经营洞察", "成长权益", "我的任务", "我的奖励",
        # 应用
        "TikTok Shop 服务商", "物流服务市场",
        # 数据分析
        "店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析",
        "营销数据分析", "客户数据分析", "排行榜", "售后数据分析",
        # 账号健康
        "店铺健康", "店铺体验分", "达人健康评分", "明星商家认证计划",
        # 合规
        "合规看板", "合规资质", "商品合规诊断",
        # 财务
        "财务概览", "保证金", "收益数据分析", "账单", "钱包",
    ]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(6)
    print(f"Starting URL: {page.url}")

    # First test: try clicking using index instead of text match
    # Find index of "触达" in the menu
    idx_test = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            result.push({i: i, text: items[i].innerText.trim().substring(0, 20)});
        }
        return JSON.stringify(result);
    }""")

    items = json.loads(idx_test)
    print(f"\nAll menu items (index: text):")
    for item in items:
        if item['text']:
            print(f"  [{item['i']}] {item['text']}")

    # Find "触达" index
    reach_idx = None
    for item in items:
        if '触达' in item['text']:
            reach_idx = item['i']
            print(f"\n'触达' found at index {reach_idx}")
            break

    if reach_idx is not None:
        # Click it by index
        page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            items[{reach_idx}].click();
        }}""")
        print(f"Clicked '触达' by index {reach_idx}")
        time.sleep(8)

        print(f"\nAfter clicking 触达:")
        print(f"  URL: {page.url}")
        print(f"  Title: {page.title()}")

        # Get main text
        main_text = page.evaluate("() => document.body.innerText.substring(0, 1000)")
        print(f"  Main text: {main_text[:500]}")

        page.screenshot(path=f"{OUTPUT_DIR}/test_click_reach_v2.png", full_page=True)
        print("  Screenshot saved")

    browser.close()
