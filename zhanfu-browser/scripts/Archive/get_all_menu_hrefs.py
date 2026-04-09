#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get href (URL) for every sidebar menu item, then navigate directly."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate to product/list and wait a long time
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(15)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Get ALL menu items with href, text, and index
    menu_data = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var el = items[i];
            var a = el.querySelector('a');
            var href = a ? (a.href || a.getAttribute('href') || '') : '';
            var text = el.innerText.trim();
            result.push({
                i: i,
                text: text,
                href: href,
                cls: el.className,
                hasA: !!a
            });
        }
        return JSON.stringify(result);
    }""")

    menu_items = json.loads(menu_data)
    print(f"\nTotal menu items: {len(menu_items)}")

    # Show items with href (navigation items)
    with_href = [it for it in menu_items if it['href']]
    print(f"Items with href: {len(with_href)}")
    for it in with_href[:20]:
        print(f"  [{it['i']}] '{it['text']}' -> {it['href']}")

    # Show items without href
    without_href = [it for it in menu_items if not it['href']]
    print(f"\nItems WITHOUT href: {len(without_href)}")
    for it in without_href[:10]:
        print(f"  [{it['i']}] '{it['text']}' cls={it['cls'][:50]}")

    # Save the full menu data
    out_file = os.path.join(OUTPUT_DIR, "full_menu_with_hrefs.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(menu_items, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Now try navigating to a known page, then to one of the href pages
    print("\n--- Testing direct navigation to '触达' href ---")
    reach_item = next((it for it in menu_items if '触达' in it['text'] and it['href']), None)
    if reach_item:
        print(f"Found: '{reach_item['text']}' -> {reach_item['href']}")
        page.goto(reach_item['href'], timeout=45000, wait_until="domcontentloaded")
        time.sleep(12)
        print(f"After navigation:")
        print(f"  URL: {page.url}")
        print(f"  Title: {page.title()}")
        main_text = page.evaluate("() => document.body.innerText.substring(0, 1000)")
        print(f"  Text: {repr(main_text[:300])}")
        page.screenshot(path=f"{OUTPUT_DIR}/direct_nav_reach.png", full_page=True)
        print("  Screenshot saved")
    else:
        print("'触达' not found or has no href")

    browser.close()
