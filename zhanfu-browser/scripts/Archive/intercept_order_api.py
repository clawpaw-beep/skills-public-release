#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Navigate to order/manage and intercept API responses via CDP."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time, base64
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

def decode_base64_safe(s):
    try:
        return base64.b64decode(s).decode('utf-8', errors='replace')
    except:
        return s

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Intercept network requests
    api_calls = []

    def handle_request(request):
        if '/api/' in request.url or '/order/' in request.url or '/tiktok/' in request.url:
            api_calls.append({
                "url": request.url,
                "method": request.method,
                "post_data": request.post_data,
                "headers": dict(request.headers)
            })

    def handle_response(response):
        url = response.url
        if '/api/' in url or '/order/' in url or 'tiktok' in url.lower():
            try:
                body = response.body()
                try:
                    text = body.decode('utf-8', errors='replace')
                except:
                    text = repr(body)
                api_calls.append({
                    "type": "response",
                    "url": url,
                    "status": response.status,
                    "body_preview": text[:500] if len(text) > 500 else text
                })
            except Exception as e:
                api_calls.append({
                    "type": "response_error",
                    "url": url,
                    "error": str(e)
                })

    # Register handlers BEFORE navigation
    page.on("request", handle_request)
    page.on("response", handle_response)

    print("=== 导航到 order/manage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")

    # Wait and let API calls complete
    time.sleep(15)

    print(f"Intercepted {len(api_calls)} API calls")

    # Filter for relevant calls
    relevant_calls = [c for c in api_calls if '/api/' in c.get('url', '') or '/order/' in c.get('url', '')]
    print(f"\nRelevant API calls: {len(relevant_calls)}")

    for call in relevant_calls[:20]:
        print(f"\n--- {call.get('type', 'request')} ---")
        print(f"URL: {call.get('url', '')[:200]}")
        if 'method' in call:
            print(f"Method: {call.get('method')}")
        if 'status' in call:
            print(f"Status: {call.get('status')}")
        if 'body_preview' in call:
            print(f"Body: {call.get('body_preview')[:300]}")
        if 'post_data' in call and call['post_data']:
            print(f"PostData: {call.get('post_data')[:200]}")

    # Save results
    out_file = os.path.join(OUTPUT_DIR, "order_api_intercept.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "all_calls": api_calls,
            "relevant_calls": relevant_calls
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Take screenshot
    page.screenshot(path=os.path.join(OUTPUT_DIR, "order_intercept.png"), full_page=True)
    print("Screenshot saved")

    browser.close()
