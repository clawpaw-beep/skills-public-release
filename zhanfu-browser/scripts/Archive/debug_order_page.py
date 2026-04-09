#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug order page - check why content doesn't render."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Go to order/manage
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=40000, wait_until="domcontentloaded")
    time.sleep(5)

    # Take screenshot
    ss_path = os.path.join(OUTPUT_DIR, f"订单页_debug_{int(time.time())}.png")
    page.screenshot(path=ss_path)
    print(f"Screenshot: {ss_path}")

    # Check main content area
    result = page.evaluate("""() => {
        // Check for ant-layout-content (main content area)
        var contentArea = document.querySelector('.ant-layout-content');
        var contentText = contentArea ? contentArea.innerText.substring(0, 500) : 'NOT FOUND';

        // Check for any error messages
        var errors = document.querySelectorAll('[class*="error"], [class*="alert"], [class*="message"]');
        var errorMsgs = Array.from(errors).map(function(e) { return e.innerText; });

        // Check for loading indicators
        var loaders = document.querySelectorAll('[class*="loading"], [class*="spinner"]');
        var loaderCount = loaders.length;

        // Check what's in the main div
        var mainDiv = document.querySelector('#root, #app, [data-testid]');
        var mainHTML = mainDiv ? mainDiv.innerHTML.substring(0, 500) : 'NOT FOUND';

        return JSON.stringify({
            contentText: contentText,
            errorMsgs: errorMsgs,
            loaderCount: loaderCount,
            mainHTML: mainHTML
        });
    }""")

    data = json.loads(result)
    print("Content area text:", data['contentText'])
    print("Error messages:", data['errorMsgs'])
    print("Loader count:", data['loaderCount'])

    # Check root element
    root_html = page.evaluate("() => document.getElementById('root').innerHTML.substring(0, 1000)")
    print("Root HTML (first 1000):", root_html)

    # Save full result
    output_file = os.path.join(OUTPUT_DIR, "订单页_debug.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved:", output_file)

    browser.close()
