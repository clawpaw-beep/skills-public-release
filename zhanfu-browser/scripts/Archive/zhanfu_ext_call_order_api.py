#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Use ZhanFu extension's cookies/tokens to call TikTok Shop order API."""

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
        print(f"Extension page: {ext_page.url}")

        # Call order API from extension context
        print("\n=== Call order list API ===")
        try:
            result = ext_page.evaluate("""() => {
                var csrfToken = document.cookie.match(/csrftoken=([^;]+)/);
                csrfToken = csrfToken ? csrfToken[1] : '';
                var url = 'https://seller.us.tiktokshopglobalselling.com/api/order/list';
                var params = new URLSearchParams({
                    shop_region: 'US',
                    mall_id: '2376919',
                    page: '1',
                    page_size: '20'
                });
                return fetch(url + '?' + params.toString(), {
                    credentials: 'include',
                    headers: {
                        'accept': 'application/json',
                        'x-csrftoken': csrfToken,
                        'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage'
                    }
                }).then(function(r) { return r.text(); }).then(function(t) { return t.substring(0, 2000); }).catch(function(e) { return 'Error: ' + e.message; });
            }""")
            print("Order API result:", result)
        except Exception as e:
            print("Order API error:", e)

        # Call return order API
        print("\n=== Call return order API ===")
        try:
            result2 = ext_page.evaluate("""() => {
                var csrfToken = document.cookie.match(/csrftoken=([^;]+)/);
                csrfToken = csrfToken ? csrfToken[1] : '';
                var url = 'https://seller.us.tiktokshopglobalselling.com/api/order/return/list';
                var params = new URLSearchParams({
                    shop_region: 'US',
                    mall_id: '2376919',
                    page: '1',
                    page_size: '20'
                });
                return fetch(url + '?' + params.toString(), {
                    credentials: 'include',
                    headers: {
                        'accept': 'application/json',
                        'x-csrftoken': csrfToken,
                        'referer': 'https://seller.us.tiktokshopglobalselling.com/order/return'
                    }
                }).then(function(r) { return r.text(); }).then(function(t) { return t.substring(0, 3000); }).catch(function(e) { return 'Error: ' + e.message; });
            }""")
            print("Return API result:", result2)
        except Exception as e:
            print("Return API error:", e)

        # Try getting all localStorage keys
        print("\n=== All localStorage keys ===")
        try:
            all_keys = ext_page.evaluate("""() => {
                var keys = [];
                for (var i = 0; i < localStorage.length; i++) {
                    keys.push(localStorage.key(i));
                }
                return JSON.stringify(keys);
            }""")
            print("All localStorage keys:", all_keys)
        except Exception as e:
            print("localStorage error:", e)

    browser.close()
