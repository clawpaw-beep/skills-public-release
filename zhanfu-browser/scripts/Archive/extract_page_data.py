#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time, re
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    print("=== Extract ALL inline script data ===")
    try:
        all_data = page.evaluate("""
            () => {
                var scripts = Array.from(document.querySelectorAll('script:not([src])'));
                var results = [];
                for (var i = 0; i < scripts.length; i++) {
                    var text = scripts[i].textContent;
                    if (text && text.trim().length > 100) {
                        results.push({
                            index: i,
                            length: text.length,
                            preview: text.substring(0, 500)
                        });
                    }
                }
                return JSON.stringify(results);
            }
        """)
        scripts_data = json.loads(all_data)
        print(f"Found {len(scripts_data)} non-empty inline scripts")
        for s in scripts_data:
            print(f"\\n--- Script {s['index']} (len={s['length']}) ---")
            print(s['preview'][:300])

    except Exception as e:
        print(f"Error: {e}")

    # Also check for window.__NEXT_DATA__ or similar
    print("\\n=== Check for embedded data ===")
    try:
        window_data = page.evaluate("""
            () => {
                var results = {};
                // Check various window properties that might contain order data
                var props = ['__NEXT_DATA__', '__STATE__', '__REDUX_DATA__', '__INITIAL_STATE__',
                             '__PRELOADED_STATE__', '__context__', '__apollo_state__'];
                for (var p of props) {
                    if (window[p]) {
                        try {
                            results[p] = JSON.stringify(window[p]).substring(0, 500);
                        } catch(e) {
                            results[p] = String(window[p]).substring(0, 200);
                        }
                    }
                }

                // Check for atlas data
                if (window.__ATLAS__) results['__ATLAS__'] = JSON.stringify(window.__ATLAS__).substring(0, 500);
                if (window.__atlas__) results['__atlas__'] = JSON.stringify(window.__atlas__).substring(0, 500);

                // Check for any JSON-like data in script tags
                var jsonBlocks = [];
                var allScripts = document.querySelectorAll('script');
                for (var s of allScripts) {
                    var text = s.textContent;
                    if (text && text.includes('orderList') || text && text.includes('"orders"')) {
                        jsonBlocks.push(text.substring(0, 1000));
                    }
                }
                results.jsonBlocks = jsonBlocks;

                return JSON.stringify(results);
            }
        """)
        wdata = json.loads(window_data)
        print("Window data keys:", list(wdata.keys()))
        for k, v in wdata.items():
            if k != 'jsonBlocks':
                print(f"\\n{k}: {v[:300]}")
            else:
                print(f"\\njsonBlocks ({len(v)}): {v[:500]}")

    except Exception as e:
        print(f"Window data error: {e}")

    # Save page HTML for analysis
    print("\\n=== Save page HTML ===")
    try:
        html = page.content()
        out_file = os.path.join(OUTPUT_DIR, "return_page_full.html")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved: {out_file} ({len(html)} bytes)")

        # Extract order data from HTML
        print("\\n=== Extract order data from HTML ===")
        # Look for order-related JSON
        order_pattern = re.compile(r'"order[^"]*":\s*\\[', re.IGNORECASE)
        matches = order_pattern.findall(html[:100000])
        print(f"Order patterns found: {len(matches)}")

        # Extract all JSON-like structures
        json_structures = re.findall(r'\\{[^{}]*"order[^{}]*[^{}]*\\}', html[:500000], re.IGNORECASE)
        print(f"JSON structures with 'order': {len(json_structures)}")
        if json_structures:
            for s in json_structures[:3]:
                print(f"  {s[:200]}")

    except Exception as e:
        print(f"HTML save error: {e}")

    browser.close()
