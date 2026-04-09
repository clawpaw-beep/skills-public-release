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

    page.goto("https://seller.us.tiktokshopglobalselling.com/order/return",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    print("=== Try fetch from extension context ===")
    if len(context.pages) > 1:
        ext_page = context.pages[1]

        # Try to call order API from the extension page using its authenticated context
        result = ext_page.evaluate("""
            () => {
                var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                var csrfToken = csrfMatch ? csrfMatch[1] : '';
                var msToken = localStorage.getItem('msToken') || '';

                // First get all tokens
                var teaToken = '';
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.startsWith('__tea_cache_tokens_')) {
                        try {
                            var val = JSON.parse(localStorage.getItem(key));
                            if (val && val.user_unique_id && val.user_unique_id.startsWith('7494148854457534288')) {
                                teaToken = localStorage.getItem(key);
                                break;
                            }
                        } catch(e) {}
                    }
                }

                // Also try different order API paths
                var results = [];
                var paths = [
                    '/api/order/list',
                    '/api/v2/order/list',
                    '/open-api/order/list',
                    '/api/v1/order/list'
                ];

                for (var i = 0; i < paths.length; i++) {
                    var path = paths[i];
                    var body = JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20});

                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com' + path, false);
                    xhr.setRequestHeader('accept', 'application/json');
                    xhr.setRequestHeader('content-type', 'application/json');
                    xhr.setRequestHeader('x-csrftoken', csrfToken);
                    xhr.setRequestHeader('x-sousaa', msToken);
                    xhr.setRequestHeader('x-tos-client-id', 'tts_seller_pc');
                    xhr.setRequestHeader('referer', 'https://seller.us.tiktokshopglobalselling.com/order/return');
                    try {
                        xhr.send(body);
                        results.push({
                            path: path,
                            status: xhr.status,
                            body: xhr.responseText.substring(0, 500),
                            contentType: xhr.getResponseHeader('content-type')
                        });
                    } catch(e) {
                        results.push({path: path, error: e.message});
                    }
                }
                return JSON.stringify(results);
            }
        """)
        print("Results:", result[:2000])

    # Now try from main page context with full cookies
    print("\n=== Try from main page ===")
    try:
        main_result = page.evaluate("""
            () => {
                var csrf = document.cookie.match(/csrftoken=([^;]+)/) ? document.cookie.match(/csrftoken=([^;]+)/)[1] : '';
                var results = [];

                var paths = [
                    '/api/order/list',
                    '/api/v2/order/list',
                    '/open-api/order/list'
                ];

                var body = JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20});

                for (var i = 0; i < paths.length; i++) {
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com' + paths[i], false);
                    xhr.setRequestHeader('accept', 'application/json');
                    xhr.setRequestHeader('content-type', 'application/json');
                    xhr.setRequestHeader('x-csrftoken', csrf);
                    try {
                        xhr.send(body);
                        results.push({
                            path: paths[i],
                            status: xhr.status,
                            body: xhr.responseText.substring(0, 300),
                            ct: xhr.getResponseHeader('content-type')
                        });
                    } catch(e) {
                        results.push({path: paths[i], error: e.message});
                    }
                }
                return JSON.stringify(results);
            }
        """)
        print("Main page results:", main_result[:2000])
    except Exception as e:
        print("Main page error:", e)

    browser.close()
