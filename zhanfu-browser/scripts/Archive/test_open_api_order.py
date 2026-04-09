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

        print("=== Test /open-api/order/list with various params ===")
        try:
            results = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var results = [];

                    var testCases = [
                        // POST with different bodies
                        {method:'POST', path:'/open-api/order/list', body:{shop_region:'US', mall_id:2376919, page:1, page_size:20}, headers:{}},
                        {method:'POST', path:'/open-api/order/list', body:{shop_region:'US', page:1, page_size:20}, headers:{}},
                        {method:'POST', path:'/open-api/order/list', body:{region:'US', mall_id:2376919}, headers:{}},
                        // GET
                        {method:'GET', path:'/open-api/order/list?shop_region=US&mall_id=2376919&page=1&page_size=20', body:null, headers:{}},
                        {method:'GET', path:'/open-api/order/list?shop_region=US', body:null, headers:{}},
                        // Other paths that might work
                        {method:'POST', path:'/open-api/orders', body:{shop_region:'US', mall_id:2376919, page:1, page_size:20}, headers:{}},
                        {method:'POST', path:'/open-api/v1/order/list', body:{shop_region:'US', mall_id:2376919, page:1, page_size:20}, headers:{}},
                    ];

                    for (var i = 0; i < testCases.length; i++) {
                        var tc = testCases[i];
                        var url = 'https://seller.us.tiktokshopglobalselling.com' + tc.path;
                        try {
                            var xhr = new XMLHttpRequest();
                            xhr.open(tc.method, url, false);
                            xhr.setRequestHeader('accept', 'application/json');
                            xhr.setRequestHeader('content-type', 'application/json');
                            xhr.setRequestHeader('x-csrftoken', csrfToken);
                            xhr.setRequestHeader('x-sousaa', msToken);
                            xhr.setRequestHeader('x-tos-client-id', 'tts_seller_pc');
                            xhr.setRequestHeader('referer', 'https://seller.us.tiktokshopglobalselling.com/order/manage');
                            if (tc.body) {
                                xhr.send(JSON.stringify(tc.body));
                            } else {
                                xhr.send();
                            }
                            var respText = xhr.responseText;
                            results.push({
                                test: tc.method + ' ' + tc.path,
                                status: xhr.status,
                                body_length: respText.length,
                                body_preview: respText.substring(0, 300)
                            });
                        } catch(e) {
                            results.push({test: tc.method + ' ' + tc.path, error: e.message});
                        }
                    }
                    return JSON.stringify(results);
                }
            """)
            print("Results:")
            for r in json.loads(results):
                status = r.get('status', 'ERR')
                preview = r.get('body_preview', r.get('error', ''))
                print(f"  [{status}] {r.get('test')}: {preview[:200]}")

        except Exception as e:
            print(f"Error: {e}")

        # Save
        out_file = os.path.join(OUTPUT_DIR, "open_api_order_tests.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(json.loads(results), f, ensure_ascii=False, indent=2)
        print(f"\nSaved: {out_file}")

    browser.close()
