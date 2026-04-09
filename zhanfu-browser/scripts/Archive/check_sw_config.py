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

    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    if len(context.pages) > 1:
        ext_page = context.pages[1]

        # Read sw-config.json
        print("=== Fetch sw-config.json ===")
        try:
            result = ext_page.evaluate("""
                () => {
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', 'https://seller.us.tiktokshopglobalselling.com/sw-config.json', false);
                    xhr.send();
                    return JSON.stringify({
                        status: xhr.status,
                        body: xhr.responseText.substring(0, 2000)
                    });
                }
            """)
            r = json.loads(result)
            print(f"Status: {r['status']}")
            print("Config:", r['body'][:2000])

            # Save
            try:
                config = json.loads(r['body'])
                out_file = os.path.join(OUTPUT_DIR, "sw_config.json")
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                print(f"\nSaved: {out_file}")
            except:
                pass
        except Exception as e:
            print("sw-config error:", e)

        # Also try to look at localStorage for API hints
        print("\n=== localStorage API hints ===")
        try:
            keys_result = ext_page.evaluate("""
                () => {
                    var result = {};
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        if (key.startsWith('__tea_cache_tokens_') ||
                            key.includes('api') ||
                            key.includes('mall') ||
                            key.includes('shop') ||
                            key.includes('order')) {
                            try {
                                result[key] = JSON.parse(localStorage.getItem(key));
                            } catch(e) {
                                result[key] = localStorage.getItem(key);
                            }
                        }
                    }
                    return JSON.stringify(result);
                }
            """)
            keys_data = json.loads(keys_result)
            print("Keys with API hints:")
            for k, v in keys_data.items():
                vstr = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                print(f"  {k}: {vstr[:200]}")

        except Exception as e:
            print("Keys error:", e)

        # Most importantly - try to read the order page's JS to find API paths
        print("\n=== Try to find order API path in page scripts ===")
        try:
            # Get all script tags from main page
            scripts = page.evaluate("""
                () => {
                    var scripts = document.querySelectorAll('script');
                    var results = [];
                    for (var i = 0; i < scripts.length; i++) {
                        var src = scripts[i].src;
                        if (src && (src.includes('order') || src.includes('seller'))) {
                            results.push(src);
                        }
                    }
                    return JSON.stringify(results);
                }
            """)
            print("Relevant scripts:", scripts[:500])

        except Exception as e:
            print("Scripts error:", e)

        # Let me try a different approach - look at the actual network request format
        # used by the working return page
        print("\n=== Look at return page API ===")
        page2_goto = page.evaluate("""() => {
            window.location.href = 'https://seller.us.tiktokshopglobalselling.com/order/return';
            return 'navigating';
        }""")
        print(page2_goto)
        time.sleep(8)

        # Now intercept on this page
        api_calls = []
        def on_request(req):
            if '/api/' in req.url or '/open-api/' in req.url:
                api_calls.append({
                    'url': req.url,
                    'method': req.method,
                    'headers': dict(req.headers)
                })
        page.on('request', on_request)
        time.sleep(3)

        print("API calls on return page:")
        for c in api_calls:
            print(f"  [{c['method']}] {c['url']}")

        if api_calls:
            out_file = os.path.join(OUTPUT_DIR, "return_page_apis.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(api_calls, f, ensure_ascii=False, indent=2)
            print(f"\nSaved: {out_file}")

    browser.close()
