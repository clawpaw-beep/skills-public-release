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

        # First try plain empty POST
        print("=== Test empty POST to /open-api/order/list ===")
        try:
            result1 = ext_page.evaluate("""
                () => {
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list', false);
                    xhr.setRequestHeader('accept', 'application/json');
                    xhr.setRequestHeader('content-type', 'application/json');
                    xhr.send();
                    return JSON.stringify({status: xhr.status, body: xhr.responseText, len: xhr.responseText.length});
                }
            """)
            print("Empty POST:", result1)
        except Exception as e:
            print("Empty POST error:", e)

        # Now try with all headers
        print("\n=== Test with full headers ===")
        try:
            result2 = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var bssdk = localStorage.getItem('bssdk_user_token') || '';
                    var teaToken = '';
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        if (key.startsWith('__tea_cache_tokens_')) {
                            try { teaToken = localStorage.getItem(key); break; } catch(e) {}
                        }
                    }

                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list', false);
                    xhr.setRequestHeader('accept', 'application/json, text/plain, */*');
                    xhr.setRequestHeader('content-type', 'application/json');
                    xhr.setRequestHeader('x-csrftoken', csrfToken);
                    xhr.setRequestHeader('x-sousaa', msToken);
                    xhr.setRequestHeader('x-tos-client-id', 'tts_seller_pc');
                    xhr.setRequestHeader('x-loc', 'us');
                    xhr.setRequestHeader('referer', 'https://seller.us.tiktokshopglobalselling.com/order/manage');
                    xhr.setRequestHeader('origin', 'https://seller.us.tiktokshopglobalselling.com');
                    xhr.send(JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20}));
                    return JSON.stringify({
                        status: xhr.status,
                        statusText: xhr.statusText,
                        body: xhr.responseText,
                        bodyLen: xhr.responseText.length,
                        allHeaders: xhr.getAllResponseHeaders()
                    });
                }
            """)
            r2 = json.loads(result2)
            print("Full headers POST:")
            print(f"  Status: {r2['status']} {r2['statusText']}")
            print(f"  Body len: {r2['bodyLen']}")
            print(f"  Body: {r2['body'][:300]}")
            print(f"  Headers: {r2['allHeaders'][:200]}")

        except Exception as e:
            print("Full headers error:", e)

        # Maybe the API requires different auth - try with bssdk token
        print("\n=== Test with bssdk token ===")
        try:
            result3 = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var bssdk = localStorage.getItem('bssdk_user_token') || '';
                    var webId = '';
                    try {
                        var tea = null;
                        for (var i = 0; i < localStorage.length; i++) {
                            var key = localStorage.key(i);
                            if (key.startsWith('__tea_cache_tokens_')) {
                                var val = localStorage.getItem(key);
                                if (val) { tea = JSON.parse(val); break; }
                            }
                        }
                        if (tea && tea.web_id) webId = tea.web_id;
                    } catch(e) {}

                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list', false);
                    xhr.setRequestHeader('accept', 'application/json');
                    xhr.setRequestHeader('content-type', 'application/json');
                    xhr.setRequestHeader('x-csrftoken', csrfToken);
                    xhr.setRequestHeader('x-sousaa', msToken);
                    xhr.setRequestHeader('x-tos-client-id', 'tts_seller_pc');
                    xhr.setRequestHeader('x-bssdk-token', bssdk);
                    xhr.setRequestHeader('x-web-id', webId);
                    xhr.send(JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20}));
                    return JSON.stringify({
                        status: xhr.status,
                        body: xhr.responseText.substring(0, 500),
                        bodyLen: xhr.responseText.length
                    });
                }
            """)
            r3 = json.loads(result3)
            print(f"Status: {r3['status']}, Body: {r3['body'][:300]}")

        except Exception as e:
            print("bssdk test error:", e)

        # Try intercepting the actual order page fetch to see what real API it calls
        print("\n=== Intercept fetch in iframe context ===")
        try:
            # Navigate to the iframe URL directly and intercept
            result4 = ext_page.evaluate("""
                () => {
                    // Get all iframes
                    var iframes = document.querySelectorAll('iframe');
                    var results = [];
                    for (var i = 0; i < iframes.length; i++) {
                        results.push({
                            id: iframes[i].id,
                            src: iframes[i].src,
                            name: iframes[i].name
                        });
                    }
                    // Also check frames
                    var frames = [];
                    for (var i = 0; i < window.frames.length; i++) {
                        try {
                            frames.push({
                                index: i,
                                url: window.frames[i].location.href,
                                name: window.frames[i].name
                            });
                        } catch(e) {
                            frames.push({index: i, error: e.message});
                        }
                    }
                    return JSON.stringify({iframes: results, frames: frames});
                }
            """)
            print("Frames info:", result4[:500])

        except Exception as e:
            print("Frames info error:", e)

    browser.close()
