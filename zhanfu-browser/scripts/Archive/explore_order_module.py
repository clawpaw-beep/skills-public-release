#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore order module content."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

def explore_order():
    print("=== 订单模块探索 ===")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
                  timeout=40000, wait_until="domcontentloaded")
        time.sleep(5)

        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")

        # Extract content
        content = page.evaluate("""
            (function() {
                var result = {
                    tabs: [],
                    table_headers: [],
                    buttons: [],
                    inputs: [],
                    headings: []
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

                var hs = document.querySelectorAll("h1, h2, h3, h4");
                hs.forEach(function(h) {
                    var text = h.textContent.trim();
                    if (text && text.length < 200) result.headings.push(text);
                });

                return JSON.stringify(result);
            })()
        """)

        data = json.loads(content)

        print("\n=== 标签页 ===")
        for t in data.get('tabs', []):
            print(f"  {t}")

        print("\n=== 表格 ===")
        for t in data.get('table_headers', []):
            print(f"  {t}")

        print("\n=== 按钮 ===")
        for b in data.get('buttons', []):
            print(f"  {b}")

        print("\n=== 输入框 ===")
        for i in data.get('inputs', []):
            print(f"  [{i['type']}] {i['placeholder']}")

        print("\n=== 标题 ===")
        for h in data.get('headings', []):
            print(f"  {h}")

        # Save
        output_file = os.path.join(OUTPUT_DIR, "订单模块.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已保存: {output_file}")

        ss_path = os.path.join(OUTPUT_DIR, f"订单模块_{int(time.time())}.png")
        page.screenshot(path=ss_path, full_page=True)
        print(f"截图: {ss_path}")

        browser.close()

if __name__ == "__main__":
    explore_order()
