#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Intercept real TikTok Shop API calls via CDP + try msToken/teaToken auth."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time, base64
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

def decode_body(body_obj):
    if not body_obj:
        return ""
    if isinstance(body_obj, dict):
        if body_obj.get("type") == "string":
            return body_obj.get("string", "")
        elif body_obj.get("type") == "base64":
            try:
                return base64.b64decode(body_obj.get("base64", "")).decode('utf-8', errors='replace')
            except:
                return str(body_obj)
    return str(body_obj)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    intercepted_requests = []
    intercepted_responses = []

    def on_request(request):
        url = request.url
        if any(x in url.lower() for x in ['tiktok', 'tiktokshop', '/api/', '/order/', 'seller.us']) and len(url) > 20:
            try:
                post_data = decode_body(request.post_data_buffer) if request.method == "POST" else None
                intercepted_requests.append({
                    "url": url,
                    "method": request.method,
                    "headers": dict(request.headers),
                    "post_data": post_data[:500] if post_data else None,
                    "resource_type": request.resource_type
                })
            except:
                pass

    def on_response(response):
        url = response.url
        if any(x in url.lower() for x in ['tiktokshop', '/api/', '/order/']) and len(url) > 30:
            try:
                body_preview = ""
                try:
                    body = response.body()
                    body_preview = body[:1000].decode('utf-8', errors='replace') if body else ""
                except:
                    pass
                intercepted_responses.append({
                    "url": url,
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": dict(response.headers),
                    "body_preview": body_preview[:500]
                })
            except:
                pass

    page.on("request", on_request)
    page.on("response", on_response)

    print("=== Navigating to order/manage with interception ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")

    # Wait for dynamic content to load
    time.sleep(15)

    print(f"\nIntercepted {len(intercepted_requests)} API requests")
    print(f"Intercepted {len(intercepted_responses)} API responses")

    # Show relevant requests
    print("\n=== API Requests (order-related) ===")
    for req in intercepted_requests:
        if '/order/' in req['url'] or '/api/order' in req['url']:
            print(f"\n{req['method']} {req['url'][:150]}")
            print(f"  Headers: {json.dumps({k: req['headers'].get(k,'') for k in list(req['headers'].keys())[:10]})}")
            if req.get('post_data'):
                print(f"  PostData: {req['post_data'][:200]}")

    print("\n=== API Responses (order-related) ===")
    for resp in intercepted_responses:
        if '/order/' in resp['url'] or '/api/order' in resp['url']:
            print(f"\n{resp['status']} {resp['url'][:150]}")
            print(f"  Body: {resp['body_preview'][:300]}")

    # Show ALL intercepted URLs
    print("\n=== All intercepted URLs ===")
    for req in intercepted_requests[:30]:
        print(f"  [{req['method']}] {req['url'][:120]}")

    # Save
    out_file = os.path.join(OUTPUT_DIR, "intercepted_api_calls.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "requests": intercepted_requests,
            "responses": intercepted_responses
        }, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Take screenshot
    page.screenshot(path=f"{OUTPUT_DIR}/order_intercepted.png", full_page=True)
    print("Screenshot saved")

    browser.close()
