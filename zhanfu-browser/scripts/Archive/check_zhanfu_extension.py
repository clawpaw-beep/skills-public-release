#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check what the ZhanFu extension's check.html page contains."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate to order/manage
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    # Check all pages
    print("=== All Pages ===")
    for i, ctx in enumerate(browser.contexts):
        print(f"Context {i}:")
        for j, pg in enumerate(ctx.pages):
            try:
                print(f"  [{j}] {pg.url[:120]} | {pg.title()[:50]}")
            except:
                print(f"  [{j}] (error)")

    # Try to access the ZhanFu extension page directly
    ext_url = "chrome-extension://dbhcfopojlklmgfaldcggjamimlbjloo/contentPage/check.html?mallId=2376919"
    print(f"\n=== Try ZhanFu Extension Page ===")
    page2 = context.new_page()
    page2.goto(ext_url, timeout=15000)
    time.sleep(5)
    print(f"URL: {page2.url}")
    print(f"Title: {page2.title()}")
    try:
        text = page2.evaluate("() => document.body.innerText.substring(0, 2000)")
        print(f"Text: {repr(text[:1000])}")
    except Exception as e:
        print(f"Error: {e}")

    page2.screenshot(path=f"{OUTPUT_DIR}/zhanfu_extension_check.png", full_page=True)

    # Check extension ID
    print(f"\n=== Extension Info ===")
    ext_info = page.evaluate("""() => {
        return JSON.stringify({
            extensions: Array.from(navigator.plugins).map(p => p.name),
            userAgent: navigator.userAgent
        });
    }""")
    print(f"Plugins: {ext_info}")

    browser.close()
