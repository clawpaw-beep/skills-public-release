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

        print("=== Read streaming response from /open-api/order/list ===")
        try:
            stream_result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var bssdk = localStorage.getItem('bssdk_user_token') || '';

                    // Use fetch with response body as stream
                    var reader = null;
                    var chunks = [];
                    var error = null;

                    return fetch('https://seller.us.tiktokshopglobalselling.com/open-api/order/list', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'accept': 'application/json, text/plain, */*',
                            'content-type': 'application/json',
                            'x-csrftoken': csrfToken,
                            'x-sousaa': msToken,
                            'x-tos-client-id': 'tts_seller_pc',
                            'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage'
                        },
                        body: JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20})
                    }).then(function(response) {
                        // Check content type
                        var ct = response.headers.get('content-type');
                        var reader = response.body.getReader();
                        return new Promise(function(resolve) {
                            function read() {
                                reader.read().then(function(result) {
                                    if (result.done) {
                                        resolve({chunks: chunks, done: true});
                                    } else {
                                        var chunk = new TextDecoder().decode(result.value);
                                        chunks.push(chunk);
                                        read();
                                    }
                                }).catch(function(e) {
                                    resolve({chunks: chunks, error: e.message});
                                });
                            }
                            read();
                        });
                    }).then(function(data) {
                        return JSON.stringify(data);
                    }).catch(function(e) {
                        return JSON.stringify({error: e.message});
                    });
                }
            """)
            result = json.loads(stream_result)
            if 'error' in result:
                print("Error:", result['error'])
            else:
                print("Chunks received:", len(result['chunks']))
                full_text = ''.join(result['chunks'])
                print("Total length:", len(full_text))
                print("Content:", full_text[:2000])

                # Save
                out_file = os.path.join(OUTPUT_DIR, "streaming_order_response.json")
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\nSaved: {out_file}")

        except Exception as e:
            print("Stream error:", e)

        # Also try to get response headers to see TT_LOGID
        print("\n=== Get trace headers ===")
        try:
            headers_result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';

                    return fetch('https://seller.us.tiktokshopglobalselling.com/open-api/order/list', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'accept': '*/*',
                            'content-type': 'application/json',
                            'x-csrftoken': csrfToken,
                            'x-sousaa': msToken,
                            'x-tos-client-id': 'tts_seller_pc',
                            'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage'
                        },
                        body: JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20})
                    }).then(function(response) {
                        var headers = {};
                        response.headers.forEach(function(value, key) {
                            headers[key] = value;
                        });
                        var ct = response.headers.get('content-type');
                        return JSON.stringify({
                            contentType: ct,
                            status: response.status,
                            headers: headers
                        });
                    }).catch(function(e) { return JSON.stringify({error: e.message}); });
                }
            """)
            print("Headers:", headers_result)

        except Exception as e:
            print("Headers error:", e)

    browser.close()
