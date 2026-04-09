#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test with longer wait and networkidle."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Use networkidle - wait until no more network requests
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=60000, wait_until="networkidle")
    time.sleep(8)  # Extra wait for SPA

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Now check menu items
    menu_raw = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var text = items[i].innerText || '';
            result.push({i: i, text: text, cls: items[i].className});
        }
        return JSON.stringify(result);
    }""")

    items = json.loads(menu_raw)
    print(f"Total menu items: {len(items)}")

    # Count non-empty
    non_empty = [it for it in items if len(it['text'].strip()) > 0]
    print(f"Items with text: {len(non_empty)}")

    for it in non_empty[:15]:
        print(f"  [{it['i']}] {repr(it['text'][:30])}")

    # Find indices for specific items
    target_texts = ['触达', '促销活动', '店铺数据分析', '管理订单', '财务概览']
    for target in target_texts:
        for it in items:
            if target in it['text']:
                print(f"Found '{target}' at index {it['i']}")

    # Try clicking '触达' - find its index
    reach_idx = None
    for it in items:
        if '触达' in it['text']:
            reach_idx = it['i']
            break

    if reach_idx is not None:
        print(f"\nClicking index {reach_idx} ('触达')")
        page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            items[{reach_idx}].click();
        }}""")
        time.sleep(10)

        print(f"After click URL: {page.url}")
        print(f"After click title: {page.title()}")

        main_text = page.evaluate("() => document.body.innerText.substring(0, 1000)")
        print(f"Main text preview: {repr(main_text[:300])}")

        page.screenshot(path=f"{OUTPUT_DIR}/test_networkidle.png", full_page=True)
        print("Screenshot saved")
    else:
        print("'触达' not found in menu!")

    browser.close()
