#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Strategy 1: Go to product list first (works), wait, then navigate to order/manage
    print("=== Strategy 1: product -> order/manage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)
    print(f"Product list: {page.url}")

    # Now navigate to order/manage using JavaScript (SPA navigation)
    page.evaluate("""() => {
        window.history.pushState({}, '', '/order/manage');
    }""")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(15)

    print(f"After pushState nav: {page.url}")
    print(f"Title: {page.title()}")

    # Check all pages
    print(f"\nPages in context: {len(context.pages)}")
    for i, pg in enumerate(context.pages):
        try:
            print(f"  [{i}] {pg.url[:80]} | {pg.title()[:50]}")
        except:
            print(f"  [{i}] (error)")

    # Check all frames
    print(f"\nFrames: {len(page.frames)}")
    for f in page.frames:
        print(f"  {f.name} | {f.url[:100]}")

    main_text = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"\nMain text: {repr(main_text[:300])}")

    # Check iframes
    iframes = page.evaluate("""() => {
        return JSON.stringify(Array.from(document.querySelectorAll('iframe')).map(f => ({
            src: f.src,
            id: f.id
        })));
    }""")
    print(f"\nIframes: {iframes}")

    page.screenshot(path=os.path.join(OUTPUT_DIR, "order_strategy1.png"), full_page=True)

    # Strategy 2: Navigate directly with special params
    print("\n=== Strategy 2: Direct navigation with params ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage?shop_region=US&mall_id=2376919",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(15)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    main_text2 = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"Main text: {repr(main_text2[:300])}")

    # Check all pages again
    print(f"\nPages: {len(context.pages)}")
    for i, pg in enumerate(context.pages):
        try:
            print(f"  [{i}] {pg.url[:80]}")
        except:
            pass

    page.screenshot(path=os.path.join(OUTPUT_DIR, "order_strategy2.png"), full_page=True)

    browser.close()
