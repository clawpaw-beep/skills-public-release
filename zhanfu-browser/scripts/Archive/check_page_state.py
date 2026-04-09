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

    print("Testing different approaches to render full sidebar...")

    # Approach 1: Direct navigation to affiliate (which worked before)
    page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)
    print(f"\n=== After affiliate/landing ===")
    print(f"URL: {page.url}")

    menu1 = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var withText = 0;
        var texts = [];
        for (var i = 0; i < items.length; i++) {
            var t = items[i].innerText.trim();
            if (t) { withText++; texts.push({i:i, text: t.substring(0,20)}); }
        }
        return JSON.stringify({total: items.length, withText: withText, samples: texts.slice(0,10)});
    }""")
    data1 = json.loads(menu1)
    print(f"Items: {data1['total']} total, {data1['withText']} with text")
    for t in data1.get('samples', []):
        print(f"  [{t['i']}] {t['text']}")

    # Now navigate to product/list from here
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)
    print(f"\n=== After navigating to product/list ===")
    print(f"URL: {page.url}")

    menu2 = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var withText = 0;
        var texts = [];
        for (var i = 0; i < items.length; i++) {
            var t = items[i].innerText.trim();
            if (t) { withText++; texts.push({i:i, text: t.substring(0,20)}); }
        }
        return JSON.stringify({total: items.length, withText: withText, samples: texts.slice(0,10)});
    }""")
    data2 = json.loads(menu2)
    print(f"Items: {data2['total']} total, {data2['withText']} with text")
    for t in data2.get('samples', []):
        print(f"  [{t['i']}] {t['text']}")

    # Try clicking on '触达' by text if visible
    if data2['withText'] > 3:
        print("\nClicking '触达'...")
        click_r = page.evaluate("""() => {
            var items = document.querySelectorAll('.core-menu-item');
            for (var i = 0; i < items.length; i++) {
                if (items[i].innerText.trim() === '触达') {
                    items[i].click();
                    return JSON.stringify({found: true, i: i});
                }
            }
            return JSON.stringify({found: false});
        }""")
        click_data = json.loads(click_r)
        print(f"Click result: {click_data}")
        if click_data.get('found'):
            time.sleep(10)
            print(f"After click URL: {page.url}")
            page.screenshot(path=f"{OUTPUT_DIR}/click_reach_test.png", full_page=True)
            print("Screenshot saved")

    browser.close()
