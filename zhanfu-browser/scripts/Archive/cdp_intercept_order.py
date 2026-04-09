#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)

    # Enable CDP fetch to intercept all network
    version = browser.version
    print("Browser version:", version)

    # Get CDP session
    try:
        cdp = browser.contexts[0].pages[0]._impl_obj._browser_session
    except:
        # Try different approach
        cdp = None
        for page in browser.contexts[0].pages:
            try:
                cdp = page._impl_obj._browser_session
                break
            except:
                continue

    print("CDP available:", cdp is not None)

    # Try to use Fetch domain
    try:
        cdp.send("Fetch.enable", {"patterns": [{"urlPattern": "*", "resourceType": "XHR", "requestStage": "Request"}, {"urlPattern": "*", "resourceType": "Fetch", "requestStage": "Request"}]})
        print("Fetch domain enabled")
    except Exception as e:
        print("Fetch enable error:", e)

    # Now navigate to order page and collect
    context = browser.contexts[0]
    page = context.pages[0]

    intercepted = []

    def handle_fetch(event):
        intercepted.append(event)

    if cdp:
        try:
            cdp.on("Fetch.requestPaused", handle_fetch)
        except:
            pass

    print("\n=== Navigate to order/manage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(12)

    print(f"Intercepted {len(intercepted)} fetch events")

    # Show relevant ones
    order_apis = [e for e in intercepted if '/order/' in str(e.get('request', {}).get('url', '')) or '/api/' in str(e.get('request', {}).get('url', ''))]
    print(f"\nOrder-related: {len(order_apis)}")
    for e in order_apis[:10]:
        req = e.get('request', {})
        print(f"  [{e.get('requestStage', '')}] {req.get('method', '')} {req.get('url', '')[:150]}")

    # Save
    out_file = os.path.join(OUTPUT_DIR, "cdp_fetch_intercept.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(intercepted, f, default=str, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    browser.close()
