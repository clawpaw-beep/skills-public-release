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
    time.sleep(8)

    print("=== Extract full order table ===")
    result = page.evaluate("""
        () => {
            // Find ALL tables and extract completely
            var tables = document.querySelectorAll('table');
            var results = [];

            for (var table of tables) {
                var headers = [];
                var headerCells = table.querySelectorAll('thead th');
                for (var h of headerCells) {
                    headers.push(h.textContent.trim());
                }

                var rows = [];
                var bodyRows = table.querySelectorAll('tbody tr');
                for (var row of bodyRows) {
                    var cells = [];
                    var tds = row.querySelectorAll('td');
                    for (var td of tds) {
                        // Get direct text without nested elements
                        var clone = td.cloneNode(true);
                        // Remove button/nested element text that might clutter
                        var buttons = clone.querySelectorAll('button, a, .action, .btn');
                        for (var b of buttons) b.remove();
                        cells.push(clone.textContent.trim().replace(/\\s+/g, ' '));
                    }
                    if (cells.length > 0) rows.push(cells);
                }

                if (rows.length > 0) {
                    results.push({headers, rows});
                }
            }

            return JSON.stringify(results);
        }
    """)

    tables = json.loads(result)
    print(f"Tables: {len(tables)}")

    all_orders = []
    for i, table in enumerate(tables):
        print(f"\n=== Table {i+1} ===")
        print(f"Headers: {table['headers']}")
        print(f"Rows: {len(table['rows'])}")
        for j, row in enumerate(table['rows']):
            print(f"\nRow {j+1}:")
            for k, cell in enumerate(row):
                if k < len(table['headers']):
                    print(f"  {table['headers'][k]}: {cell[:200]}")
                else:
                    print(f"  Col{k}: {cell[:200]}")
            all_orders.append(dict(zip(table['headers'], row)))

    # Save
    out_file = os.path.join(OUTPUT_DIR, "return_orders_full.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"tables": tables, "orders": all_orders}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Also get summary stats
    print("\n=== Summary Stats ===")
    summary = page.evaluate("""
        () => {
            // Find tab counts
            var tabs = document.querySelectorAll('[class*="tab"], [class*="Tab"]');
            var tabData = [];
            for (var t of tabs) {
                var text = t.textContent.trim();
                if (text) tabData.push(text);
            }

            // Find any stat numbers
            var statPattern = /(\\d+)\\s*(待|已|全|取消|退款|退货|争议)/g;
            var body = document.body.innerText;
            var stats = [];
            var match;
            while ((match = statPattern.exec(body)) !== null) {
                stats.push(match[0]);
            }

            return JSON.stringify({
                tabs: tabData.slice(0, 20),
                stats: [...new Set(stats)]
            });
        }
    """)
    s = json.loads(summary)
    print("Tabs:", s['tabs'])
    print("Stats:", s['stats'])

    browser.close()
