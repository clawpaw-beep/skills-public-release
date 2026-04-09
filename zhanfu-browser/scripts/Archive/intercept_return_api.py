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

    # Create fresh page for return
    page = context.new_page()

    api_calls = []
    resp_bodies = []

    def on_request(req):
        if '/api/' in req.url or '/open-api/' in req.url or 'tiktok' in req.url.lower():
            try:
                pd = req.post_data
                if pd and len(pd) > 500:
                    pd = pd[:500]
                api_calls.append({
                    'url': req.url,
                    'method': req.method,
                    'post_data': pd
                })
            except:
                pass

    def on_response(resp):
        url = resp.url
        if '/api/' in url or '/open-api/' in url:
            try:
                body = resp.body()
                body_str = body[:500].decode('utf-8', errors='replace') if body else ''
                resp_bodies.append({
                    'url': url,
                    'status': resp.status,
                    'body_preview': body_str
                })
            except:
                pass

    page.on('request', on_request)
    page.on('response', on_response)

    print("=== Navigate to return page ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)

    print(f"\nCaptured {len(api_calls)} API requests")
    print(f"Captured {len(resp_bodies)} API responses")

    print("\n--- API requests ---")
    for c in api_calls[:20]:
        print(f"  [{c['method']}] {c['url'][:150]}")
        if c.get('post_data'):
            print(f"    POST: {c['post_data'][:200]}")

    print("\n--- API responses ---")
    for r in resp_bodies[:10]:
        print(f"  [{r['status']}] {r['url'][:150]}")
        if r.get('body_preview'):
            print(f"    {r['body_preview'][:200]}")

    # Save
    out_file = os.path.join(OUTPUT_DIR, "return_page_intercept.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({'requests': api_calls, 'responses': resp_bodies}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    page.screenshot(path=f"{OUTPUT_DIR}/return_page_intercept.png")
    print("Screenshot saved")

    browser.close()
