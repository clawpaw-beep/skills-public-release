#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Call TikTok Shop API using msToken from extension localStorage."""

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

        # Get msToken and cookies
        auth_data = ext_page.evaluate("""() => {
            var msToken = localStorage.getItem('msToken') || '';
            var teaTokens = '';
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                if (key.startsWith('__tea_cache_tokens_')) {
                    teaTokens = localStorage.getItem(key);
                    break;
                }
            }
            var cookies = document.cookie;
            var csrfMatch = cookies.match(/csrftoken=([^;]+)/);
            var csrfToken = csrfMatch ? csrfMatch[1] : '';
            return JSON.stringify({
                msToken: msToken,
                teaTokens: teaTokens,
                csrfToken: csrfToken,
                cookie: cookies.substring(0, 200)
            });
        }""")
        print("Auth data:", auth_data[:200])

        # Try to call API using msToken
        print("\n=== Try order API with msToken ===")
        try:
            result = ext_page.evaluate("""() => {
                var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                var csrfToken = csrfMatch ? csrfMatch[1] : '';
                var msToken = localStorage.getItem('msToken') || '';

                // Try multiple API patterns
                var urls = [
                    'https://seller.us.tiktokshopglobalselling.com/api/order/list?shop_region=US&mall_id=2376919&page=1&page_size=20',
                    'https://seller.us.tiktokshopglobalselling.com/api/v1/order/list?shop_region=US&mall_id=2376919',
                    'https://seller.us.tiktokshopglobalselling.com/webapi/order/list?shop_region=US&mall_id=2376919',
                ];

                var reqHeaders = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/json',
                    'origin': 'https://seller.us.tiktokshopglobalselling.com',
                    'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage',
                    'x-csrftoken': csrfToken,
                    'x-sousaa': msToken,
                    'x-tos-client-id': 'tts_seller_pc'
                };

                var results = [];
                urls.forEach(function(url) {
                    results.push({url: url, method: 'GET'});
                });

                // Try POST to order API
                fetch('https://seller.us.tiktokshopglobalselling.com/api/order/list', {
                    method: 'POST',
                    credentials: 'include',
                    headers: reqHeaders,
                    body: JSON.stringify({
                        shop_region: 'US',
                        mall_id: 2376919,
                        page: 1,
                        page_size: 20
                    })
                }).then(function(r) { return r.text(); })
                  .then(function(t) { results.push({type: 'POST', status: 'ok', body: t.substring(0, 500)}); })
                  .catch(function(e) { results.push({type: 'POST', error: e.message}); });

                return JSON.stringify(results);
            }""")
            print("API results:", result[:500])

            time.sleep(5)

            # Try GET requests
            print("\n=== Try GET order API ===")
            get_result = ext_page.evaluate("""() => {
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
            }""")
            print("GET result:", get_result[:500])

        except Exception as e:
            print("API error:", e)

        # Try the return order API since that page works
        print("\n=== Try return order API (should work since page loads) ===")
        try:
            ret_result = ext_page.evaluate("""() => {
                var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                var csrfToken = csrfMatch ? csrfMatch[1] : '';
                var msToken = localStorage.getItem('msToken') || '';

                // First go to return page
                window.location.href = 'https://seller.us.tiktokshopglobalselling.com/order/return';
                return 'navigating...';
            }""")
            print(ret_result)
            time.sleep(8)

            // Now try API
            ret_api = ext_page.evaluate("""() => {
                var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                var csrfToken = csrfMatch ? csrfMatch[1] : '';
                var msToken = localStorage.getItem('msToken') || '';

                var url = 'https://seller.us.tiktokshopglobalselling.com/api/order/return/list?shop_region=US&mall_id=2376919&page=1&page_size=20';
                return fetch(url, {
                    credentials: 'include',
                    headers: {
                        'accept': 'application/json',
                        'x-csrftoken': csrfToken,
                        'x-sousaa': msToken,
                        'x-tos-client-id': 'tts_seller_pc'
                    }
                }).then(function(r) { return r.text(); })
                  .then(function(t) { return t.substring(0, 2000); })
                  .catch(function(e) { return 'Error: ' + e.message; });
            }""")
            print("Return API:", ret_api[:500])

        except Exception as e:
            print("Return API error:", e)

    browser.close()
