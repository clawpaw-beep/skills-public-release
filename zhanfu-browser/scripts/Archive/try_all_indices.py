#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try clicking ALL 61 menu items (including empty ones) by index."""

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
    time.sleep(10)

    # Get all 61 menu items
    all_items = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var el = items[i];
            result.push({
                i: i,
                text: el.innerText.trim().substring(0, 30),
                cls: el.className,
                rect: JSON.stringify(el.getBoundingClientRect())
            });
        }
        return JSON.stringify(result);
    }""")

    items = json.loads(all_items)
    print(f"Total items: {len(items)}")

    results = {}

    # Try clicking each item by index and see what URL it goes to
    for it in items:
        idx = it['i']
        cls = it['cls']
        is_indented = 'indented' in cls

        print(f"\n--- [{idx}] indented={is_indented} text='{it['text']}' ---")

        # Get current URL before click
        url_before = page.url

        # Click by index
        click_js = page.evaluate(f"""(i) => {{
            var items = document.querySelectorAll('.core-menu-item');
            if (items[i]) {{
                items[i].click();
                return 'clicked';
            }}
            return 'not_found';
        }}""", idx)

        if click_js == 'not_found':
            print(f"  Element not found at index {idx}")
            continue

        time.sleep(8)

        url_after = page.url
        title = page.title()

        print(f"  Before: {url_before}")
        print(f"  After:  {url_after}")
        print(f"  Title:  {title}")

        if url_after != url_before:
            print(f"  *** NAVIGATED! ***")
            results[idx] = {
                'index': idx,
                'text': it['text'],
                'cls': cls,
                'url_before': url_before,
                'url_after': url_after,
                'title': title,
                'navigated': True
            }

            # Take screenshot
            ss_name = f"nav_{idx}_{it['text'][:10]}_{int(time.time())}.png"
            page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
            print(f"  Screenshot: {ss_name}")

        time.sleep(2)

    # Save navigation results
    out_file = os.path.join(OUTPUT_DIR, "navigation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n=== Done === Navigated pages: {len(results)}")
    print(f"Saved: {out_file}")

    browser.close()
