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
        print("Extension page:", ext_page.url)

        print("\n=== Try GET order API ===")
        try:
            result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var url = 'https://seller.us.tiktokshopglobalselling.com/api/order/list?shop_region=US&mall_id=2376919&page=1&page_size=20';
                    return fetch(url, {
                        method: 'GET',
                        credentials: 'include',
                        headers: {
                            'accept': 'application/json',
                            'x-csrftoken': csrfToken,
                            'x-sousaa': msToken,
                            'x-tos-client-id': 'tts_seller_pc',
                            'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage'
                        }
                    }).then(function(r) { return r.text(); })
                      .then(function(t) { return t.substring(0, 2000); })
                      .catch(function(e) { return 'Error: ' + e.message; });
                }
            """)
            print("GET result:", result[:500])
        except Exception as e:
            print("GET error:", e)

        print("\n=== Try POST order API ===")
        try:
            result2 = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    return fetch('https://seller.us.tiktokshopglobalselling.com/api/order/list', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'accept': 'application/json',
                            'content-type': 'application/json',
                            'x-csrftoken': csrfToken,
                            'x-sousaa': msToken,
                            'x-tos-client-id': 'tts_seller_pc'
                        },
                        body: JSON.stringify({
                            shop_region: 'US',
                            mall_id: 2376919,
                            page: 1,
                            page_size: 20
                        })
                    }).then(function(r) { return r.text(); })
                      .then(function(t) { return t.substring(0, 2000); })
                      .catch(function(e) { return 'Error: ' + e.message; });
                }
            """)
            print("POST result:", result2[:500])
        except Exception as e:
            print("POST error:", e)

        print("\n=== Get all localStorage keys ===")
        try:
            keys_result = ext_page.evaluate("""
                () => {
                    var keys = [];
                    for (var i = 0; i < localStorage.length; i++) {
                        keys.push(localStorage.key(i));
                    }
                    return JSON.stringify(keys);
                }
            """)
            all_keys = json.loads(keys_result)
            print("Total keys:", len(all_keys))
            # Show keys related to data
            data_keys = [k for k in all_keys if any(x in k.lower() for x in ['data', 'cache', 'order', 'shop', 'api', 'user', 'token'])]
            print("Data-related keys:", data_keys[:20])
        except Exception as e:
            print("Keys error:", e)

    browser.close()
