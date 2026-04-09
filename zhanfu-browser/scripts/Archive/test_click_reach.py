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

    # Go to product/list
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(6)
    print(f"URL: {page.url}")

    # Get all menu texts
    menu_texts = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        return JSON.stringify(Array.from(items).map(function(el) {
            return el.innerText.trim();
        }));
    }""")
    texts = json.loads(menu_texts)
    print(f"Menu items count: {len(texts)}")
    print(f"First 10: {texts[:10]}")
    print(f"'触达' in list: {'触达' in texts}")
    print(f"'促销' in list: {'促销' in texts}")
    print(f"'广告营销' in list: {'广告营销' in texts}")

    # Try clicking 触达
    result = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        for (var i = 0; i < items.length; i++) {
            if (items[i].innerText.trim() === '触达') {
                items[i].click();
                return JSON.stringify({found: true, index: i, text: items[i].innerText.trim()});
            }
        }
        return JSON.stringify({found: false});
    }""")
    print(f"Click 触达 result: {result}")

    time.sleep(8)
    print(f"After click URL: {page.url}")
    print(f"After click title: {page.title()}")

    page.screenshot(path=f"{OUTPUT_DIR}/test_click_reach.png", full_page=True)
    print("Screenshot saved")

    browser.close()
