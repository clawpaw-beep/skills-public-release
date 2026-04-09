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

    print("=== Extract order data from DOM ===")

    # Get page text and tables
    result = page.evaluate("""
        () => {
            // Find all tables
            var tables = document.querySelectorAll('table');
            var tableData = [];
            for (var t of tables) {
                var rows = [];
                var trs = t.querySelectorAll('tr');
                for (var tr of trs) {
                    var cells = Array.from(tr.querySelectorAll('th, td')).map(c => c.textContent.trim());
                    if (cells.length > 0) rows.push(cells);
                }
                if (rows.length > 0) tableData.push(rows);
            }

            // Find all divs with order-like content
            var allDivs = document.querySelectorAll('div');
            var orderDivs = [];
            for (var d of allDivs) {
                var text = d.textContent || '';
                if ((text.includes('5773') || text.includes('$') || text.includes('退款')) && d.children.length < 10 && text.length < 500) {
                    orderDivs.push({
                        tag: d.tagName,
                        id: d.id,
                        className: d.className,
                        text: text.substring(0, 200)
                    });
                }
            }

            // Find React root elements
            var roots = [];
            for (var id of ['root', 'GEC-content', '__next', 'app']) {
                var el = document.getElementById(id);
                if (el) roots.push({id: id, html: el.innerHTML.substring(0, 500)});
            }

            return JSON.stringify({
                tables: tableData,
                orderDivs: orderDivs.slice(0, 20),
                roots: roots,
                bodyText: document.body.innerText.substring(0, 3000)
            });
        }
    """)

    data = json.loads(result)

    print(f"Tables found: {len(data['tables'])}")
    for i, table in enumerate(data['tables']):
        print(f"\n--- Table {i+1} ---")
        for row in table[:10]:
            print('  |'.join(str(c)[:30] for c in row))

    print(f"\nOrder divs: {len(data['orderDivs'])}")
    for d in data['orderDivs'][:5]:
        print(f"  [{d['tag']}] {d['text'][:100]}")

    print(f"\nBody text (first 1000 chars):")
    print(data['bodyText'][:1000])

    # Save
    out_file = os.path.join(OUTPUT_DIR, "dom_order_data.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_file}")

    # Screenshot
    page.screenshot(path=f"{OUTPUT_DIR}/return_page_dom.png", full_page=True)
    print("Screenshot saved")

    browser.close()
