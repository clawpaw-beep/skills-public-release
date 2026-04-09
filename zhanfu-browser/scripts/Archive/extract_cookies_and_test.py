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

    # Get ALL cookies from the context
    print("=== Extract cookies ===")
    try:
        cookies = context.cookies([
            "https://seller.us.tiktokshopglobalselling.com",
            "https://www.tiktok.com",
        ])
        print(f"Got {len(cookies)} cookies")
        for c in cookies:
            print(f"  {c['name']}: {c['value'][:30]}...")

        # Save cookies
        cookie_dict = {c['name']: c['value'] for c in cookies}
        out_file = os.path.join(OUTPUT_DIR, "tiktok_cookies.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"\nCookies saved: {out_file}")

        # Now use Python requests with these cookies
        import urllib.request, urllib.parse

        csrf_token = cookie_dict.get('csrftoken', '')
        ms_token = ''
        for c in cookies:
            # Find msToken from extension's localStorage via cookie
            pass

        print("\n=== Test with Python requests ===")
        for url, method, body in [
            ('https://seller.us.tiktokshopglobalselling.com/open-api/order/list', 'POST', json.dumps({"shop_region":"US","mall_id":2376919,"page":1,"page_size":20})),
            ('https://seller.us.tiktokshopglobalselling.com/api/order/list?shop_region=US&mall_id=2376919&page=1', 'GET', None),
        ]:
            try:
                req = urllib.request.Request(url, data=body.encode() if body else None, method=method)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
                req.add_header('Accept', 'application/json')
                req.add_header('Content-Type', 'application/json')
                if csrf_token:
                    req.add_header('x-csrftoken', csrf_token)
                req.add_header('Referer', 'https://seller.us.tiktokshopglobalselling.com/order/manage')

                # Add all cookies
                cookie_header = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                req.add_header('Cookie', cookie_header)

                with urllib.request.urlopen(req, timeout=15) as resp:
                    status = resp.status
                    body_resp = resp.read()
                    print(f"\n[{status}] {method} {url}")
                    print(f"  Body ({len(body_resp)} bytes): {body_resp[:300]}")

            except urllib.error.HTTPError as e:
                print(f"\n[HTTP {e.code}] {method} {url}")
                body_err = e.read()
                print(f"  Error body: {body_err[:300]}")
            except Exception as e:
                print(f"\n[ERR] {method} {url}: {e}")

    except Exception as e:
        print(f"Cookie extraction error: {e}")

    # Also check if page has any hidden API data
    print("\n=== Check page for embedded API data ===")
    try:
        page_data = page.evaluate("""
            () => {
                // Check for any __NEXT_DATA__ or similar
                var nextData = document.getElementById('__NEXT_DATA__');
                if (nextData) return {type: 'NEXT_DATA', data: nextData.textContent.substring(0, 1000)};

                // Check for any script tags with data
                var scripts = document.querySelectorAll('script');
                for (var i = 0; i < scripts.length; i++) {
                    var text = scripts[i].textContent;
                    if (text && text.includes('orderList')) {
                        return {type: 'script', content: text.substring(0, 1000)};
                    }
                }

                // Check redux store
                var reduxData = window.__REDUX_DATA__ || window.__STATE__;
                if (reduxData) return {type: 'redux', data: JSON.stringify(reduxData).substring(0, 1000)};

                return null;
            }
        """)
        if page_data:
            print("Page data found:", page_data)
        else:
            print("No embedded data found")
    except Exception as e:
        print(f"Page data error: {e}")

    browser.close()
