#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore by clicking sidebar menu items - expand parent first then click child."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def click_and_wait(page, selector_or_text, wait=8):
    """Click an element by selector or text, then wait."""
    try:
        # Try to find by text first
        items = page.query_selector_all(".core-menu-item")
        for item in items:
            text = item.inner_text().strip()
            if text == selector_or_text or selector_or_text in text:
                print(f"  Clicking: {text[:50]}")
                item.click()
                time.sleep(wait)
                return True

        # Try by selector
        el = page.query_selector(selector_or_text)
        if el:
            el.click()
            time.sleep(wait)
            return True

        print(f"  NOT FOUND: {selector_or_text}")
        return False
    except Exception as e:
        print(f"  Click error: {e}")
        return False

def extract(page):
    """Extract page content."""
    time.sleep(5)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 5000),
                tabs: [], table_headers: [], buttons: [], inputs: [],
                headings: [], sub_menu_items: []
            };

            // Tabs
            var tabs = document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item");
            tabs.forEach(function(t) {
                var text = t.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.tabs.push(text);
            });

            // Tables
            var tables = document.querySelectorAll("table");
            tables.forEach(function(t) {
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

            // Headings
            var hs = document.querySelectorAll("h1, h2, h3, h4");
            hs.forEach(function(h) {
                var text = h.textContent.trim();
                if (text && text.length < 200) result.headings.push(text);
            });

            // Current sidebar expanded items
            var expanded = document.querySelectorAll(".core-menu-item-indented");
            expanded.forEach(function(el) {
                var text = el.textContent.trim();
                if (text && text.length > 0 && text.length < 100) result.sub_menu_items.push(text);
            });

            return JSON.stringify(result);
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

def explore_by_click():
    print("=== 通过点击探索子模块 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        # Start at product list
        page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
                  timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)
        print(f"Baseline: {page.url}")

        all_results = {}

        # --- 广告营销 ---
        print("\n\n===== 广告营销 =====")
        click_and_wait(page, "广告营销", wait=5)

        marketing_subs = [
            "触达",
            "客户群",
            "促销活动",
            "店铺广告",
            "智能营销",
            "店铺页面"
        ]
        for sub in marketing_subs:
            print(f"\n--- 广告营销 > {sub} ---")
            # First click parent
            click_and_wait(page, "广告营销", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "广告营销"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"广告营销>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_广告营销_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # --- 数据分析 ---
        print("\n\n===== 数据分析 =====")
        click_and_wait(page, "数据分析", wait=5)

        analytics_subs = [
            "店铺数据分析",
            "直播和视频数据分析",
            "商品卡",
            "商品数据分析",
            "营销数据分析",
            "客户数据分析",
            "排行榜",
            "售后数据分析"
        ]
        for sub in analytics_subs:
            print(f"\n--- 数据分析 > {sub} ---")
            click_and_wait(page, "数据分析", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "数据分析"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"数据分析>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_数据分析_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # --- 订单 ---
        print("\n\n===== 订单 =====")
        click_and_wait(page, "订单", wait=5)

        order_subs = [
            "管理订单",
            "批量发货",
            "管理物流",
            "管理取消申请",
            "管理退货",
            "履约表现",
            "包邮",
            "退货设置"
        ]
        for sub in order_subs:
            print(f"\n--- 订单 > {sub} ---")
            click_and_wait(page, "订单", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "订单"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"订单>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_订单_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # --- 成长中心 ---
        print("\n\n===== 成长中心 =====")
        click_and_wait(page, "成长中心", wait=5)

        growth_subs = [
            "经营洞察",
            "成长权益",
            "我的任务",
            "我的奖励"
        ]
        for sub in growth_subs:
            print(f"\n--- 成长中心 > {sub} ---")
            click_and_wait(page, "成长中心", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "成长中心"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"成长中心>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_成长中心_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # --- 合规中心 ---
        print("\n\n===== 合规中心 =====")
        click_and_wait(page, "合规中心", wait=5)

        compliance_subs = [
            "合规看板",
            "合规资质",
            "商品合规诊断"
        ]
        for sub in compliance_subs:
            print(f"\n--- 合规中心 > {sub} ---")
            click_and_wait(page, "合规中心", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "合规中心"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"合规中心>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_合规中心_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # --- 账号健康 ---
        print("\n\n===== 账号健康 =====")
        click_and_wait(page, "账号健康", wait=5)

        health_subs = [
            "店铺健康",
            "店铺体验分",
            "达人健康评分",
            "明星商家认证计划"
        ]
        for sub in health_subs:
            print(f"\n--- 账号健康 > {sub} ---")
            click_and_wait(page, "账号健康", wait=3)
            time.sleep(2)
            clicked = click_and_wait(page, sub, wait=8)
            if clicked:
                data = extract(page)
                data["clicked"] = sub
                data["parent"] = "账号健康"
                print(f"  URL: {data.get('url')}")
                print(f"  Title: {data.get('title')}")
                print(f"  Tabs: {data.get('tabs', [])[:8]}")
                print(f"  Tables: {data.get('table_headers', [])}")
                print(f"  Buttons: {data.get('buttons', [])[:10]}")
                print(f"  Headings: {data.get('headings', [])[:5]}")
                print(f"  Main text: {data.get('main_text', '')[:200]}")
                all_results[f"账号健康>{sub}"] = data
                page.screenshot(path=os.path.join(OUTPUT_DIR, f"click_账号健康_{sub}_{int(time.time())}.png"), full_page=True)
            time.sleep(3)

        # Save results
        out_file = os.path.join(OUTPUT_DIR, "click_explore_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n=== 完成 === Saved: {out_file}")
        print(f"Total modules explored: {len(all_results)}")

        browser.close()

if __name__ == "__main__":
    explore_by_click()
