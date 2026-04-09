#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Access ZhanFu extension's storage and internal APIs for order data."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Go to order/manage first
    page.goto("https://seller.us.tiktokshopglobalselling.com/order/manage",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    # Get ZhanFu extension page (Page 1)
    if len(context.pages) > 1:
        ext_page = context.pages[1]
        print(f"Extension page URL: {ext_page.url}")
        print(f"Extension page title: {ext_page.title()}")

        # Try to access localStorage from extension page
        print("\n=== Extension localStorage ===")
        try:
            storage = ext_page.evaluate("""() => {
                var keys = [];
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    var value = localStorage.getItem(key);
                    keys.push({key: key, value: value});
                }
                return JSON.stringify(keys);
            }""")
            storage_data = json.loads(storage)
            print(f"localStorage keys: {len(storage_data)}")
            for item in storage_data[:20]:
                print(f"  {item['key']}: {item['value'][:100] if item['value'] else 'null'}")
        except Exception as e:
            print(f"localStorage error: {e}")

        # Try to access cookies
        print("\n=== Extension cookies ===")
        try:
            cookies = ext_page.evaluate("""() => {
                return document.cookie;
            }""")
            print(f"Cookies: {cookies[:500]}")
        except Exception as e:
            print(f"Cookies error: {e}")

        # Try to access sessionStorage
        print("\n=== Extension sessionStorage ===")
        try:
            sstorage = ext_page.evaluate("""() => {
                var keys = [];
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    var value = sessionStorage.getItem(key);
                    keys.push({key: key, value: value});
                }
                return JSON.stringify(keys);
            }""")
            ss_data = json.loads(sstorage)
            print(f"sessionStorage keys: {len(ss_data)}")
            for item in ss_data[:20]:
                print(f"  {item['key']}: {item['value'][:100] if item['value'] else 'null'}")
        except Exception as e:
            print(f"sessionStorage error: {e}")

        # Try to execute JavaScript in extension context
        print("\n=== Try to get TikTok token from extension ===")
        try:
            token_data = ext_page.evaluate("""() => {
                // Try to find TikTok auth token
                var result = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.toLowerCase().includes('token') ||
                        key.toLowerCase().includes('auth') ||
                        key.toLowerCase().includes('session') ||
                        key.toLowerCase().includes('tiktok')) {
                        result[key] = localStorage.getItem(key);
                    }
                }
                return JSON.stringify(result);
            }""")
            print(f"Token-like keys: {token_data}")
        except Exception as e:
            print(f"Token search error: {e}")

        # Try to access TikTok Shop API via extension
        print("\n=== Try TikTok Shop API via extension ===")
        try:
            api_result = ext_page.evaluate("""() => {
                // Try fetching order API
                return fetch('https://seller.us.tiktokshopglobalselling.com/api/order/list', {
                    credentials: 'include'
                }).then(r => r.text()).then(t => t.substring(0, 500)).catch(e => 'Error: ' + e.message);
            }""")
            print(f"API result: {api_result}")
        except Exception as e:
            print(f"API error: {e}")

    # Also check main page
    print("\n=== Main page localStorage (first 10) ===")
    try:
        main_storage = page.evaluate("""() => {
            var keys = [];
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                keys.push(key);
            }
            return JSON.stringify(keys.slice(0, 20));
        }""")
        print(f"Main page localStorage: {main_storage}")
    except Exception as e:
        print(f"Error: {e}")

    # Try postMessage to the iframe
    print("\n=== Try postMessage to iframe ===")
    try:
        msg_result = page.evaluate("""() => {
            var iframe = document.querySelector('iframe');
            if (iframe && iframe.contentWindow) {
                iframe.contentWindow.postMessage({
                    type: 'ORDER_LIST_REQUEST',
                    mallId: '2376919'
                }, '*');
                return 'Message sent to iframe';
            }
            return 'No iframe found';
        }""")
        print(f"postMessage result: {msg_result}")
        time.sleep(3)
    except Exception as e:
        print(f"postMessage error: {e}")

    # Take screenshot of extension page
    try:
        ext_page.screenshot(path=f"{OUTPUT_DIR}/zhanfu_ext_storage.png", full_page=True)
        print("\nScreenshot saved")
    except Exception as e:
        print(f"Screenshot error: {e}")

    browser.close()
