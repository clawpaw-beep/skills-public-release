#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time, re
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(3)

    print("=== Find JS files ===")
    js_files = []
    for frame in page.frames:
        try:
            url = frame.url
            if url and '.js' in url:
                js_files.append(url)
        except:
            pass

    # Get from main page too
    for url in page.frames:
        try:
            u = url
            if u and '.js' in u:
                js_files.append(u)
        except:
            pass

    js_files = list(set(js_files))
    print(f"Found {len(js_files)} JS files")

    # Find order-related JS
    order_js = [f for f in js_files if 'order' in f.lower()]
    print(f"Order-related: {len(order_js)}")
    for f in order_js[:5]:
        print(f"  {f[:150]}")

    # Get script URLs from DOM
    script_urls = page.evaluate("""
        () => {
            var scripts = Array.from(document.querySelectorAll('script[src]'));
            return scripts.map(s => s.src).filter(s => s.includes('seller') || s.includes('order') || s.includes('tiktok'));
        }
    """)
    print(f"\nDOM script URLs: {len(script_urls)}")
    for u in script_urls[:5]:
        print(f"  {u[:150]}")

    # Now download the order-related JS to find API paths
    print("\n=== Download and search JS for API paths ===")

    # Get the main seller JS
    seller_js = [f for f in js_files if 'seller' in f.lower() or 'i18n' in f.lower()]
    print(f"Seller JS files: {len(seller_js)}")

    # Let's look at what order API paths are in the page's inline scripts
    inline_scripts = page.evaluate("""
        () => {
            var scripts = Array.from(document.querySelectorAll('script:not([src])'));
            var results = [];
            for (var i = 0; i < scripts.length; i++) {
                var text = scripts[i].textContent;
                if (text && (text.includes('order') || text.includes('open-api') || text.includes('orderList'))) {
                    results.push(text.substring(0, 2000));
                }
            }
            return results;
        }
    """)
    print(f"Inline scripts with order content: {len(inline_scripts)}")
    for s in inline_scripts[:2]:
        print(f"  ---")
        print(f"  {s[:500]}")

    # Save JS file list
    out_file = os.path.join(OUTPUT_DIR, "js_files.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(js_files, f, ensure_ascii=False, indent=2)
    print(f"\nJS files saved: {out_file}")

    browser.close()
