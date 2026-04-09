#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

HOOK_FETCH = """
() => {
    if (window.__fetchHookInstalled) return 'already installed';
    window.__fetchHookInstalled = true;

    const originalFetch = window.fetch;
    window.__capturedFetches = [];

    window.fetch = function(url, options) {
        var urlStr = typeof url === 'string' ? url : url.url;
        var method = (options && options.method) || 'GET';
        var headers = (options && options.headers) || {};
        var body = (options && options.body) || null;

        window.__capturedFetches.push({
            url: urlStr,
            method: method,
            headers: headers,
            postData: body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null,
            timestamp: Date.now()
        });

        return originalFetch.apply(this, arguments);
    };

    window.__readCaptures = function() {
        var c = window.__capturedFetches;
        window.__capturedFetches = [];
        return JSON.stringify(c);
    };

    return 'Hook installed';
}
"""

READ_CAPTURES = "() => window.__readCaptures ? window.__readCaptures() : '[]'"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # First navigate to return page
    print("=== Navigate to order/return ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    # Install hook
    print("\n=== Install fetch hook ===")
    result = page.evaluate(HOOK_FETCH)
    print("Result:", result)

    # Wait for page to settle and trigger some activity
    print("\n=== Wait for API calls ===")
    time.sleep(5)

    # Read captures
    print("\n=== Captured fetches ===")
    captures = page.evaluate(READ_CAPTURES)
    fetch_list = json.loads(captures)
    print(f"Total: {len(fetch_list)}")

    # Show relevant ones
    relevant = [f for f in fetch_list if any(x in f['url'].lower() for x in ['api', 'order', 'seller', 'shop', 'mall'])]
    print(f"Relevant: {len(relevant)}")
    for f in relevant[:20]:
        print(f"\n[{f['method']}] {f['url'][:150]}")
        if f.get('postData'):
            print(f"  POST: {f['postData'][:300]}")

    # Also trigger some UI interaction to capture lazy-load requests
    print("\n=== Trigger scroll ===")
    page.evaluate("() => window.scrollTo(0, 500)")
    time.sleep(2)
    page.evaluate("() => window.scrollTo(0, 0)")
    time.sleep(2)

    # Read more captures
    captures2 = page.evaluate(READ_CAPTURES)
    fetch_list2 = json.loads(captures2)
    relevant2 = [f for f in fetch_list2 if any(x in f['url'].lower() for x in ['api', 'order', 'seller'])]
    print(f"After scroll: {len(relevant2)} more relevant fetches")
    for f in relevant2[:10]:
        print(f"\n[{f['method']}] {f['url'][:150]}")

    # Save
    all_relevant = relevant + relevant2
    out_file = os.path.join(OUTPUT_DIR, "fetch_hook_captures.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_relevant, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Screenshot
    page.screenshot(path=f"{OUTPUT_DIR}/order_return_fetch.png", full_page=True)
    print("Screenshot saved")

    browser.close()
