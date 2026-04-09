#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(6)
    print(f"URL: {page.url}")

    # Get menu items - use innerText directly
    menu_raw = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var text = items[i].innerText || '';
            var rect = items[i].getBoundingClientRect();
            result.push({i: i, text: text, visible: rect.width > 0 && rect.height > 0});
        }
        return JSON.stringify(result);
    }""")

    items = json.loads(menu_raw)
    print(f"Total menu items: {len(items)}")

    # Show items with text
    visible_items = [item for item in items if item['visible'] and len(item['text'].strip()) > 0]
    print(f"Visible items with text: {len(visible_items)}")

    for item in visible_items[:15]:
        print(f"  [{item['i']}] '{item['text'][:30]}'")

    # Show ALL items (including hidden/empty)
    print(f"\nAll {len(items)} items:")
    for item in items:
        print(f"  [{item['i']}] visible={item['visible']} text='{item['text'][:20]}'")

    browser.close()
