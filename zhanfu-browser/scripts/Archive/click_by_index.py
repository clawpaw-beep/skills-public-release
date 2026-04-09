#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore sub-menu by clicking all indices to find the correct ones."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate to product/list
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)

    # Get ALL 61 menu items (even if innerText is empty)
    all_items = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var el = items[i];
            result.push({
                i: i,
                text: el.innerText.trim(),
                cls: el.className,
                hasText: el.innerText.trim().length > 0
            });
        }
        return JSON.stringify(result);
    }""")

    items = json.loads(all_items)
    print(f"Total menu items: {len(items)}")

    # Items with text
    with_text = [it for it in items if it['hasText']]
    print(f"Items with text: {len(with_text)}")
    for it in with_text:
        print(f"  [{it['i']}] cls={it['cls'][:50]} text='{it['text']}'")

    # Empty items
    empty_items = [it for it in items if not it['hasText']]
    print(f"\nEmpty items: {len(empty_items)}")
    # These are the indented sub-items - try clicking some
    for it in empty_items[:5]:
        print(f"  [{it['i']}] cls={it['cls'][:60]}")

    # Try clicking each of the items with text by index
    print("\n=== Clicking items WITH text ===")
    for it in with_text:
        idx = it['i']
        text = it['text']
        print(f"\n--- Clicking [{idx}] '{text}' ---")
        page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            items[{idx}].click();
        }}""")
        time.sleep(10)
        print(f"  URL: {page.url}")
        print(f"  Title: {page.title()}")

        # Extract if content changed
        main_text = page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"  Text: {repr(main_text[:200])}")

        ss_name = f"click_idx_{idx}_{text[:6]}_{int(time.time())}.png"
        page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
        time.sleep(2)

    browser.close()
