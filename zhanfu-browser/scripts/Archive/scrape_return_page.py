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
    time.sleep(8)

    # Get full body text
    body_text = page.evaluate("() => document.body.innerText")

    print("=== Full body text ===")
    print(body_text[:3000])

    # Try to find order data in a smarter way - look for React data structures
    print("\n=== Try React fiber / component data ===")
    result = page.evaluate("""
        () => {
            // Look for any JavaScript object with order data
            var results = {};

            // Try to access React internal state
            var root = document.getElementById('GEC-content');
            if (root && root._reactRootContainer) {
                results.reactRoot = 'found';
            }

            // Look for __REACT_STATE__ or similar
            for (var key in window) {
                if (key.includes('Order') || key.includes('order') || key.includes('Return') || key.includes('return')) {
                    try {
                        var val = window[key];
                        if (val && typeof val === 'object') {
                            results[key] = JSON.stringify(val).substring(0, 500);
                        }
                    } catch(e) {}
                }
            }

            // Try to find data in __NEXT_DATA__ or similar
            var nextData = document.getElementById('__NEXT_DATA__');
            if (nextData) {
                try {
                    results.nextData = JSON.parse(nextData.textContent);
                } catch(e) {
                    results.nextData = nextData.textContent.substring(0, 500);
                }
            }

            // Check for atlas data
            var atlasEl = document.querySelector('[data-atlas]');
            if (atlasEl) {
                results.atlas = atlasEl.getAttribute('data-atlas');
            }

            return JSON.stringify(results);
        }
    """)
    print("React/Window data:", result[:500])

    # Save body text
    out_file = os.path.join(OUTPUT_DIR, "return_page_body_text.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(body_text)
    print(f"\nBody text saved: {out_file}")

    # Now let's also get the page title and visible content
    print(f"\nPage title: {page.title()}")
    print(f"URL: {page.url}")

    browser.close()
