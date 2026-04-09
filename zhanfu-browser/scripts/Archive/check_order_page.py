#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=40000, wait_until="domcontentloaded")
    time.sleep(5)

    # Check for iframes
    iframes = page.evaluate("""() => {
        var iframes = document.querySelectorAll("iframe");
        return JSON.stringify(Array.from(iframes).map(function(f) {
            return {src: f.src, id: f.id, name: f.name, cls: f.className};
        }));
    }""")
    print("Iframes:", iframes)

    # Get all visible text
    all_text = page.evaluate("() => document.body.innerText.substring(0, 3000)")
    print("Page text (first 3000):")
    print(all_text)

    # Save to file
    result = {
        "url": page.url,
        "title": page.title(),
        "iframes": json.loads(iframes),
        "page_text": all_text
    }
    output_file = os.path.join(OUTPUT_DIR, "订单页面内容.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Saved:", output_file)

    browser.close()
