#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore ALL TikTok Shop seller module entry points with full Chinese text."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"
ENSURE_OUTPUT = False

def ensure_output_dir():
    global ENSURE_OUTPUT
    if not ENSURE_OUTPUT:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        ENSURE_OUTPUT = True

def extract_page_structure(page, url):
    """Extract full page structure with proper encoding."""
    # Get all sidebar menu items with full Chinese text
    menu_data = page.evaluate("""
        (function() {
            var result = {
                url: window.location.href,
                title: document.title,
                items: [],
                headings: [],
                table_headers: [],
                buttons: [],
                filters: [],
                risk_buttons: [],
                safe_buttons: []
            };

            // Get all sidebar items using the confirmed class
            var sidebarItems = document.querySelectorAll('.core-menu-item');
            sidebarItems.forEach(function(el) {
                var text = el.textContent.trim();
                if (text && text.length > 0 && text.length < 200) {
                    var href = '';
                    var a = el.querySelector('a');
                    if (a) href = a.href || '';
                    result.items.push({
                        text: text,
                        href: href,
                        tag: el.tagName,
                        cls: el.className
                    });
                }
            });

            // Get headings
            var headingEls = document.querySelectorAll('h1, h2, h3, h4');
            headingEls.forEach(function(el) {
                var text = el.textContent.trim();
                if (text && text.length > 0 && text.length < 200) {
                    result.headings.push(text);
                }
            });

            // Get table headers
            var tables = document.querySelectorAll('table');
            tables.forEach(function(t) {
                var headers = Array.from(t.querySelectorAll('th')).map(function(h) {
                    return h.textContent.trim();
                }).filter(function(t) { return t.length > 0; });
                if (headers.length > 0) {
                    result.table_headers.push(headers);
                }
            });

            // Get all buttons with text
            var btnEls = document.querySelectorAll('button');
            btnEls.forEach(function(el) {
                var text = el.textContent.trim();
                var cls = el.className || '';
                if (text && text.length > 0 && text.length < 100) {
                    // Classify by risk
                    var isRisk = /删除|编辑|保存|提交|创建|修改|发货|退款|取消|导出|下载|发布|上架|下架|删除|批量/.test(text);
                    var item = {text: text, cls: cls.substring(0, 80)};
                    if (isRisk) {
                        result.risk_buttons.push(item);
                    } else {
                        result.safe_buttons.push(item);
                    }
                }
            });

            // Get filter inputs
            var inputs = document.querySelectorAll('input, select');
            inputs.forEach(function(el) {
                var placeholder = el.placeholder || '';
                var type = el.type || '';
                var name = el.name || '';
                var id = el.id || '';
                if (placeholder || type === 'search') {
                    result.filters.push({
                        type: type,
                        placeholder: placeholder,
                        name: name,
                        id: id
                    });
                }
            });

            return JSON.stringify(result);
        })()
    """)

    return json.loads(menu_data)

def explore_module(page, module_name, urls_to_try):
    """Explore a single module and return structure."""
    result = {
        'module': module_name,
        'pages': []
    }

    for url in urls_to_try:
        print(f"  -> {url}")
        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            time.sleep(2)

            structure = extract_page_structure(page, url)

            # Take screenshot
            screenshot_name = f"{module_name.replace(' ', '_')}_{int(time.time())}.png"
            screenshot_path = os.path.join(OUTPUT_DIR, screenshot_name)
            page.screenshot(path=screenshot_path, full_page=True)

            page_result = {
                'url': url,
                'title': structure.get('title', ''),
                'screenshot': screenshot_path,
                'menu_items': structure.get('items', []),
                'headings': structure.get('headings', []),
                'table_headers': structure.get('table_headers', []),
                'safe_buttons': structure.get('safe_buttons', []),
                'risk_buttons': structure.get('risk_buttons', []),
                'filters': structure.get('filters', [])
            }
            result['pages'].append(page_result)

            print(f"     Title: {structure.get('title', 'N/A')}")
            print(f"     Menu items: {len(structure.get('items', []))}")

        except Exception as e:
            print(f"  ERROR on {url}: {e}")
            result['pages'].append({'url': url, 'error': str(e)})

    return result

def main():
    ensure_output_dir()
    print(f"=== TikTok Shop 全模块探索 ===")
    print(f"Output: {OUTPUT_DIR}")

    # All main entry URLs to explore
    modules = [
        ("订单", [
            "https://seller.us.tiktokshopglobalselling.com/order/manage",
            "https://seller.us.tiktokshopglobalselling.com/order/list"
        ]),
        ("物流", [
            "https://seller.us.tiktokshopglobalselling.com/logistics/manage"
        ]),
        ("广告营销", [
            "https://seller.us.tiktokshopglobalselling.com/spark/overview"
        ]),
        ("客户", [
            "https://seller.us.tiktokshopglobalselling.com/buyer/manage"
        ]),
        ("联盟", [
            "https://seller.us.tiktokshopglobalselling.com/affiliate/overview"
        ]),
        ("直播和视频", [
            "https://seller.us.tiktokshopglobalselling.com/live/liveList"
        ]),
        ("数据分析", [
            "https://seller.us.tiktokshopglobalselling.com/analytics/overview"
        ]),
        ("账号健康", [
            "https://seller.us.tiktokshopglobalselling.com/accountHealth/overview"
        ]),
        ("合规中心", [
            "https://seller.us.tiktokshopglobalselling.com/compliance/overview"
        ]),
        ("财务", [
            "https://seller.us.tiktokshopglobalselling.com/finance/overview"
        ]),
    ]

    all_results = []

    with sync_playwright() as p:
        # Connect to existing ZhanFu browser
        print("Connecting to ZhanFu browser...")
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        except Exception as e:
            print(f"Failed to connect: {e}")
            return

        context = browser.contexts[0]
        page = context.pages[0]

        print(f"Current page: {page.url}")

        for module_name, urls in modules:
            print(f"\n### {module_name} ###")
            result = explore_module(page, module_name, urls)
            all_results.append(result)

            # Save individual module result
            module_file = os.path.join(OUTPUT_DIR, f"{module_name}.json")
            with open(module_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  Saved: {module_file}")

        browser.close()

    # Save combined results
    combined_file = os.path.join(OUTPUT_DIR, "all_modules_combined.json")
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 ===")
    print(f"Combined: {combined_file}")
    print(f"Total modules explored: {len(all_results)}")

if __name__ == "__main__":
    main()
