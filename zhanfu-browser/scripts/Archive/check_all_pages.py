#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)

    # Get CDP to access all frames
    # Try to get all pages/frames via CDP directly
    from playwright.sync_api import Page

    # Navigate to order/manage
    page = browser.contexts[0].pages[0]
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    print(f"Main page URL: {page.url}")
    print(f"Main page title: {page.title()}")

    # Check all frames using CDP
    try:
        # Use CDP directly
        cdp = page._impl_obj._channel
        frame_tree = cdp.send("Page.getFrameTree", {})
        print(f"\nFrame tree: {json.dumps(frame_tree, indent=2)[:2000]}")
    except Exception as e:
        print(f"CDP FrameTree error: {e}")

    # Check all browser contexts
    print(f"\nBrowser contexts: {len(browser.contexts)}")
    for i, ctx in enumerate(browser.contexts):
        print(f"\nContext {i}: {len(ctx.pages)} pages")
        for j, pg in enumerate(ctx.pages):
            try:
                print(f"  Page {j}: {pg.url} | {pg.title()}")
            except:
                print(f"  Page {j}: (error reading)")

    # Check all frames in main page
    print(f"\nAll frames in main page:")
    for f in page.frames:
        print(f"  Frame: url={f.url[:100]}, name={f.name}")

    browser.close()
