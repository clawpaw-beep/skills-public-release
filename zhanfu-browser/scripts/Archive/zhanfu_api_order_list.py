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

        # Get all auth data from localStorage
        auth_info = ext_page.evaluate("""
            () => {
                var result = {};
                // Get msToken
                result.msToken = localStorage.getItem('msToken') || '';
                // Get tea cache tokens
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.startsWith('__tea_cache_tokens_')) {
                        result.teaToken = localStorage.getItem(key);
                        result.teaTokenKey = key;
                        break;
                    }
                }
                // Get bssdk tokens
                result.bssdkToken = localStorage.getItem('bssdk_user_token') || '';
                // Get all cookie names
                var cookies = document.cookie.split(';');
                result.cookies = cookies;
                // Get other auth data
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth')) {
                        result[key] = localStorage.getItem(key);
                    }
                }
                return result;
            }
        """)

        print("\nAuth data keys:", list(auth_info.keys()))
        print("msToken:", (auth_info.get('msToken') or '')[:50])
        print("teaToken:", (auth_info.get('teaToken') or '')[:50])
        print("bssdkToken:", (auth_info.get('bssdkToken') or '')[:50])
        print("Cookies:", auth_info.get('cookies', [])[:5])

        # Try with ALL headers from localStorage
        print("\n=== Full API call with all headers ===")
        try:
            full_result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var teaToken = '';
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        if (key.startsWith('__tea_cache_tokens_')) {
                            teaToken = localStorage.getItem(key);
                            break;
                        }
                    }
                    var bssdkToken = localStorage.getItem('bssdk_user_token') || '';

                    var url = 'https://seller.us.tiktokshopglobalselling.com/api/order/list?shop_region=US&mall_id=2376919&page=1&page_size=20';
                    var headers = {
                        'accept': 'application/json, text/plain, */*',
                        'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                        'content-type': 'application/json',
                        'origin': 'https://seller.us.tiktokshopglobalselling.com',
                        'referer': window.location.href,
                        'x-csrftoken': csrfToken,
                        'x-sousaa': msToken,
                        'x-tos-client-id': 'tts_seller_pc',
                        'x-loc': 'us',
                        'Cookie': document.cookie
                    };
                    var resp = fetch(url, {
                        method: 'GET',
                        headers: headers,
                        credentials: 'include'
                    });
                    return resp.then(function(r) { return r.text(); })
                               .then(function(t) { return t.substring(0, 3000); })
                               .catch(function(e) { return 'Error: ' + e.message; });
                }
            """)
            print("Full API result:", full_result[:500])
        except Exception as e:
            print("Full API error:", e)

        # Save auth info for reference
        out_file = os.path.join(OUTPUT_DIR, "zhanfu_auth_info.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({k: (v if len(str(v)) < 500 else str(v)[:500]) for k, v in auth_info.items()}, f, ensure_ascii=False, indent=2)
        print(f"\nAuth info saved: {out_file}")

    browser.close()
