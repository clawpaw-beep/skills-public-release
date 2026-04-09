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

        # Get full auth
        auth = ext_page.evaluate("""
            () => {
                var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                var csrfToken = csrfMatch ? csrfMatch[1] : '';
                var msToken = localStorage.getItem('msToken') || '';
                var teaToken = '';
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.startsWith('__tea_cache_tokens_')) {
                        try { teaToken = localStorage.getItem(key); break; } catch(e) {}
                    }
                }
                var bssdk = localStorage.getItem('bssdk_user_token') || '';
                var cookies = document.cookie;
                return JSON.stringify({
                    csrfToken, msToken, teaToken, bssdk,
                    cookie: cookies
                });
            }
        """)
        auth_data = json.loads(auth)
        print("csrfToken:", auth_data['csrfToken'])
        print("msToken:", auth_data['msToken'][:30])
        print("teaToken:", (auth_data['teaToken'] or '')[:50])
        print("bssdk:", auth_data['bssdk'][:30])
        print("cookie:", auth_data['cookie'][:100])

        csrf = auth_data['csrfToken']
        ms = auth_data['msToken']

        # Test many possible API paths
        api_paths = [
            "/api/order/list?shop_region=US&page=1&page_size=20",
            "/api/v2/order/list?shop_region=US&mall_id=2376919",
            "/api/v1/orders?shop_region=US",
            "/open-api/order/list?shop_region=US",
            "/api/seller/order/list?shop_region=US",
            "/api/v2/seller/order/list?shop_region=US",
            "/api/order/list/v2?shop_region=US",
            "/webapi/order/list?shop_region=US",
            "/api/v1/order/management/list",
            "/api/ech orders?shop_region=US",
            "/api/v1/orders",
        ]

        print("\n=== Testing API paths ===")
        for path in api_paths:
            try:
                result = ext_page.evaluate(f"""
                    () => {{
                        var url = 'https://seller.us.tiktokshopglobalselling.com{path}';
                        var headers = {{
                            'accept': 'application/json',
                            'x-csrftoken': '{csrf}',
                            'x-sousaa': '{ms}',
                            'x-tos-client-id': 'tts_seller_pc',
                            'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage',
                            'Cookie': document.cookie
                        }};
                        return fetch(url, {{
                            method: 'GET',
                            credentials: 'include',
                            headers: headers
                        }}).then(r => r.text()).then(t => r.status + '|' + t.substring(0, 150))
                           .catch(e => 'ERR:' + e.message);
                    }}
                """)
                # Actually need to fix the JS
            except Exception as e:
                print(f"{path}: JS error - {e}")

        # Better approach: try POST with JSON body
        print("\n=== Try POST order API with full body ===")
        try:
            post_result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';
                    var bssdk = localStorage.getItem('bssdk_user_token') || '';

                    var paths = [
                        '/api/order/list',
                        '/api/v2/order/list',
                        '/open-api/order/list',
                        '/api/v1/orders'
                    ];

                    var bodies = [
                        {shop_region:'US', mall_id:2376919, page:1, page_size:20},
                        {shop_region:'US', page:1, page_size:20},
                        {shop_region:'US', mall_id:'2376919', page:1, page_size:20}
                    ];

                    var results = [];
                    paths.forEach(function(p) {
                        bodies.forEach(function(b) {
                            var url = 'https://seller.us.tiktokshopglobalselling.com' + p;
                            fetch(url, {
                                method: 'POST',
                                credentials: 'include',
                                headers: {
                                    'accept': 'application/json',
                                    'content-type': 'application/json',
                                    'x-csrftoken': csrfToken,
                                    'x-sousaa': msToken,
                                    'x-tos-client-id': 'tts_seller_pc',
                                    'referer': 'https://seller.us.tiktokshopglobalselling.com/order/manage'
                                },
                                body: JSON.stringify(b)
                            }).then(function(r) { return r.text(); })
                              .then(function(t) {
                                  results.push({
                                      path: p,
                                      body: JSON.stringify(b),
                                      status: 'ok',
                                      body_preview: t.substring(0, 200)
                                  });
                              })
                              .catch(function(e) {
                                  results.push({
                                      path: p,
                                      body: JSON.stringify(b),
                                      status: 'error',
                                      error: e.message
                                  });
                              });
                        });
                    });
                    return 'requests_sent';
                }
            """)
            print("POST requests sent, waiting for responses...")
            time.sleep(8)

            # Get results - but they're async, let me try a simpler sync approach
        except Exception as e:
            print(f"POST error: {e}")

        # Let me try a synchronous approach - use XMLHttpRequest
        print("\n=== Try XMLHttpRequest (sync-like) ===")
        try:
            sync_result = ext_page.evaluate("""
                () => {
                    var csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
                    var csrfToken = csrfMatch ? csrfMatch[1] : '';
                    var msToken = localStorage.getItem('msToken') || '';

                    var results = [];
                    var urls = [
                        '/api/order/list',
                        '/api/v2/order/list',
                        '/open-api/order/list'
                    ];
                    var body = JSON.stringify({shop_region:'US', mall_id:2376919, page:1, page_size:20});

                    for (var i = 0; i < urls.length; i++) {
                        try {
                            var xhr = new XMLHttpRequest();
                            xhr.open('POST', 'https://seller.us.tiktokshopglobalselling.com' + urls[i], false);
                            xhr.setRequestHeader('accept', 'application/json');
                            xhr.setRequestHeader('content-type', 'application/json');
                            xhr.setRequestHeader('x-csrftoken', csrfToken);
                            xhr.setRequestHeader('x-sousaa', msToken);
                            xhr.setRequestHeader('x-tos-client-id', 'tts_seller_pc');
                            xhr.setRequestHeader('referer', 'https://seller.us.tiktokshopglobalselling.com/order/manage');
                            xhr.send(body);
                            results.push({
                                url: urls[i],
                                status: xhr.status,
                                body: xhr.responseText.substring(0, 300)
                            });
                        } catch(e) {
                            results.push({url: urls[i], error: e.message});
                        }
                    }
                    return JSON.stringify(results);
                }
            """)
            print("XMLHttpRequest results:")
            for r in json.loads(sync_result):
                print(f"  [{r.get('status','ERR')}] {r.get('url')}: {r.get('body', r.get('error',''))[:150]}")

            # Save results
            out_file = os.path.join(OUTPUT_DIR, "api_path_test_results.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(json.loads(sync_result), f, ensure_ascii=False, indent=2)
            print(f"\nSaved: {out_file}")
        except Exception as e:
            print(f"Sync API test error: {e}")

    browser.close()
