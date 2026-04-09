#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

# Inject a script to override fetch and capture all API calls
HOOK_FETCH = """
() => {
    if (window.__fetchHookInstalled) return;
    window.__fetchHookInstalled = true;

    const originalFetch = window.fetch;
    window.__capturedFetches = [];

    window.fetch = function(url, options) {
        var urlStr = typeof url === 'string' ? url : url.url;
        var method = (options && options.method) || 'GET';
        var headers = (options && options.headers) || {};

        window.__capturedFetches.push({
            url: urlStr,
            method: method,
            headers: headers,
            postData: (options && options.body) || null,
            timestamp: Date.now()
        });

        console.log('[FETCH HOOK]', method, urlStr);

        return originalFetch.apply(this, arguments);
    };

    console.log('[FETCH HOOK] Installed');
    return 'Hook installed';
}
"""

READ_CAPTURES = """
() => {
    if (!window.__capturedFetches) return JSON.stringify([]);
    var captures = window.__capturedFetches;
    window.__capturedFetches = [];
    return JSON.stringify(captures);
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Install hook on current page
    print("=== Install fetch hook ===")
    result = page.evaluate(HOOK_FETCH)
    print("Hook result:", result)

    print("\n=== Navigate to order/return ===")
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(8)

    # Read captured fetches
    print("\n=== Captured fetches ===")
    captures = page.evaluate(READ_CAPTURES)
    fetch_list = json.loads(captures)
    print(f"Total: {len(fetch_list)}")
    for f in fetch_list:
        if any(x in f['url'].lower() for x in ['api', 'order', 'seller', 'shop']):
            print(f"\n[{f['method']}] {f['url']}")
            if f.get('postData'):
                print(f"  POST: {f['postData'][:200]}")

    # Save all
    out_file = os.path.join(OUTPUT_DIR, "captured_fetches.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(fetch_list, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Screenshot
    page.screenshot(path=f"{OUTPUT_DIR}/order_return_fetch_hook.png", full_page=True)
    print("Screenshot saved")

    browser.close()
