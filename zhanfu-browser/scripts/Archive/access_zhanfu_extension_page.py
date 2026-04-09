#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Access ZhanFu extension's internal page for order management."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)

    # Navigate to order/manage first
    page = browser.contexts[0].pages[0]
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    print(f"Page 0 URL: {page.url}")

    # Now access Page 1 (ZhanFu extension)
    if len(browser.contexts[0].pages) > 1:
        page1 = browser.contexts[0].pages[1]
        print(f"\n=== Page 1: ZhanFu Extension ===")
        print(f"URL: {page1.url}")
        print(f"Title: {page1.title()}")

        try:
            main_text = page1.evaluate("() => document.body.innerText.substring(0, 5000)")
            print(f"Text (first 3000): {repr(main_text[:3000])}")
        except Exception as e:
            print(f"Error getting text: {e}")

        try:
            page1.screenshot(path=os.path.join(OUTPUT_DIR, "zhanfu_extension_page.png"), full_page=True)
            print("Screenshot saved")
        except Exception as e:
            print(f"Screenshot error: {e}")

        # Get all frames in page1
        try:
            for f in page1.frames:
                print(f"Frame: {f.name} | {f.url[:100]}")
        except Exception as e:
            print(f"Frames error: {e}")

    # Also check ALL pages across ALL contexts
    print(f"\n=== All Pages (all contexts) ===")
    for i, ctx in enumerate(browser.contexts):
        for j, pg in enumerate(ctx.pages):
            try:
                print(f"[{i}][{j}] {pg.url[:100]}")
            except:
                print(f"[{i}][{j}] (error)")

    # Try to wait for order iframe to load
    print(f"\n=== Wait for order content ===")
    time.sleep(10)

    for i, ctx in enumerate(browser.contexts):
        print(f"Context {i}: {len(ctx.pages)} pages")
        for j, pg in enumerate(ctx.pages):
            try:
                print(f"  [{j}] {pg.url[:80]} | {pg.title()[:50]}")
                if "2376919" in pg.url:
                    print(f"    This looks like order iframe!")
                    try:
                        text = pg.evaluate("() => document.body.innerText.substring(0, 2000)")
                        print(f"    Content: {repr(text[:500])}")
                    except Exception as e:
                        print(f"    Error: {e}")
            except:
                pass

    browser.close()
