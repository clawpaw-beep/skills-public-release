#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try to access the TikTok ZTI iframe content directly."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

# Also try accessing order data via API instead of UI
ZTI_IFRAME_URL = "https://www.tiktok.com/ucenter_web/zti_web"

# And try the seller API endpoints directly
API_ENDPOINTS = {
    "order-list-api": "https://seller.us.tiktokshopglobalselling.com/api/order/list",
    "order-manage-api": "https://seller.us.tiktokshopglobalselling.com/api/order/manage",
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # First, go to order/manage and check what iframe looks like
    print("=== 1. 导航到 order/manage ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Get iframe info
    iframes = page.evaluate("""() => {
        return JSON.stringify(Array.from(document.querySelectorAll('iframe')).map(f => ({
            src: f.src,
            id: f.id,
            name: f.name,
            className: f.className
        })));
    }""")
    print(f"Iframes: {iframes}")

    # Try to get iframe element and its content
    iframe_data = page.evaluate("""() => {
        var iframe = document.querySelector('iframe');
        if (!iframe) return JSON.stringify({found: false});
        try {
            var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            return JSON.stringify({
                found: true,
                src: iframe.src,
                readyState: iframeDoc.readyState,
                bodyText: iframeDoc.body ? iframeDoc.body.innerText.substring(0, 2000) : 'no body'
            });
        } catch(e) {
            return JSON.stringify({found: true, error: e.message, src: iframe.src});
        }
    }""")
    print(f"Iframe content: {iframe_data}")

    # Try direct access to ZTI iframe URL
    print("\n=== 2. 直接访问 ZTI iframe URL ===")
    page.goto(ZTI_IFRAME_URL, timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    main_text = page.evaluate("() => document.body.innerText.substring(0, 3000)")
    print(f"Text: {repr(main_text[:500])}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, "zti_iframe_direct.png"), full_page=True)

    # Try checking all frames in the browser
    print("\n=== 3. 检查所有 frames ===")
    frames_info = page.evaluate("""() => {
        return JSON.stringify({
            framesCount: frames.length,
            frameNames: Array.from(frames).map(f => f.name || f.document.title || 'unnamed').slice(0, 5)
        });
    }""")
    print(f"Frames: {frames_info}")

    # Try using page.context.pages to see all pages
    print("\n=== 4. 检查所有页面 ===")
    all_pages_info = []
    for p in page.context.pages:
        try:
            all_pages_info.append({
                "url": p.url,
                "title": p.title(),
                "is_visible": p.is_visible()
            })
        except:
            pass
    print(f"Pages: {json.dumps(all_pages_info, indent=2)}")

    browser.close()
