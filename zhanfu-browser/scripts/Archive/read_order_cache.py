#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read order data from ZhanFu extension's localStorage cache."""

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

        # Read order-related localStorage keys
        print("=== Order-related localStorage data ===")
        order_keys = [
            'order_module_batch_label_action_map',
            'order_module_batch_order_action_map',
            'garrModulesBackup',
            'garr-list-cache',
        ]

        for key in order_keys:
            try:
                value = ext_page.evaluate(
                    ("() => { var val = localStorage.getItem('%s'); "
                     "if (val) { try { return JSON.stringify(JSON.parse(val)); } "
                     "catch(e) { return val.substring(0, 500); } } return null; }") % key
                )
                print(f"\n--- {key} ---")
                if value:
                    print(value[:800])
                else:
                    print("null")
            except Exception as e:
                print(f"{key}: error - {e}")

        # Try to find any order data
        print("\n=== All keys containing 'order' or 'refund' ===")
        try:
            order_data = ext_page.evaluate("""() => {
                var results = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    if (key.toLowerCase().includes('order') || key.toLowerCase().includes('refund')) {
                        var val = localStorage.getItem(key);
                        try { results[key] = JSON.parse(val); }
                        catch(e) { results[key] = val ? val.substring(0, 300) : null; }
                    }
                }
                return JSON.stringify(results, null, 2);
            }""")
            print(order_data[:2000])
        except Exception as e:
            print(f"Error: {e}")

        # Save all localStorage for analysis
        print("\n=== All localStorage keys ===")
        try:
            all_keys = ext_page.evaluate("""() => {
                var keys = [];
                for (var i = 0; i < localStorage.length; i++) {
                    keys.push(localStorage.key(i));
                }
                return JSON.stringify(keys);
            }""")
            all_keys_list = json.loads(all_keys)
            print(f"Total keys: {len(all_keys_list)}")
            print("Keys:", json.dumps(all_keys_list[:50], ensure_ascii=False))

            # Save to file
            out_file = os.path.join(OUTPUT_DIR, "zhanfu_ext_localstorage.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(all_keys_list, f, ensure_ascii=False, indent=2)
            print(f"Saved keys list: {out_file}")
        except Exception as e:
            print(f"localStorage error: {e}")

    browser.close()
