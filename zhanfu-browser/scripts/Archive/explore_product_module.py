#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore the product module using Playwright CDP connection - v2."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

MALL_ID = "2376919"  # FMCG store
OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_store_readonly_explore_20260407_fmcg"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def safe_evaluate(page, expression, default=None):
    """Safely evaluate JavaScript and return result."""
    try:
        return page.evaluate(expression)
    except Exception as e:
        print(f"    Evaluate error: {e}")
        return default

def explore_with_playwright():
    print(f"=== Exploring Product Module for store {MALL_ID} ===")
    
    with sync_playwright() as p:
        print("Connecting to ZhanFu browser via CDP...")
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        except Exception as e:
            print(f"Failed to connect: {e}")
            return
        
        print(f"Connected! Contexts: {len(browser.contexts)}")
        
        if not browser.contexts:
            print("No browser contexts!")
            browser.close()
            return
        
        context = browser.contexts[0]
        pages = context.pages
        print(f"Pages in context: {len(pages)}")
        
        if not pages:
            browser.close()
            return
        
        page = pages[0]
        print(f"Current page: {page.url}")
        
        # Navigate to product/manage (already confirmed working)
        product_urls = [
            ("product_list", "https://seller.us.tiktokshopglobalselling.com/product/list"),
            ("product_manage", "https://seller.us.tiktokshopglobalselling.com/product/manage"),
        ]
        
        all_results = {}
        
        for name, url in product_urls:
            print(f"\n--- {name}: {url} ---")
            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                time.sleep(3)
                
                print(f"Title: {page.title()}")
                print(f"URL: {page.url}")
                
                # Get page content structure
                print("\n=== Page Structure ===")
                
                # Check for sidebar/menu
                menu_result = safe_evaluate(page, """
                    (function() {
                        var items = [];
                        var menuSelectors = [
                            'ul.ant-menu li',
                            '[class*="sidebar"] li',
                            '[class*="menu"] li',
                            'nav li',
                            '[role="menuitem"]',
                            '.ant-collapse li'
                        ];
                        
                        for (var sel of menuSelectors) {
                            var els = document.querySelectorAll(sel);
                            if (els.length > 0) {
                                els.forEach(function(el) {
                                    var a = el.querySelector('a');
                                    var span = el.querySelector('span');
                                    var text = (a || span || el).textContent || '';
                                    text = text.trim().replace(/\\s+/g, ' ').substring(0, 80);
                                    if (text) {
                                        var href = a ? (a.href || a.getAttribute('href') || '') : '';
                                        items.push({text: text, href: href.substring(0, 100)});
                                    }
                                });
                                return JSON.stringify({selector: sel, count: els.length, items: items.slice(0, 40)});
                            }
                        }
                        return JSON.stringify({selector: 'none', count: 0, items: []});
                    })()
                """)
                
                if menu_result:
                    try:
                        menu_data = json.loads(menu_result) if isinstance(menu_result, str) else menu_result
                        print(f"Menu selector: {menu_data.get('selector', 'N/A')}")
                        print(f"Menu items found: {menu_data.get('count', 0)}")
                        for item in menu_data.get('items', [])[:20]:
                            print(f"  - {item['text']} -> {item['href']}")
                    except:
                        print(f"Menu raw: {str(menu_result)[:300]}")
                
                # Get headings
                headings_result = safe_evaluate(page, """
                    (function() {
                        var headings = [];
                        var els = document.querySelectorAll('h1, h2, h3, h4, [class*="title"], [class*="heading"]');
                        els.forEach(function(el) {
                            var text = el.textContent.trim().replace(/\\s+/g, ' ');
                            if (text && text.length < 100) {
                                headings.push(text);
                            }
                        });
                        return JSON.stringify(headings.slice(0, 20));
                    })()
                """)
                
                if headings_result:
                    try:
                        headings = json.loads(headings_result) if isinstance(headings_result, str) else headings_result
                        print(f"\nHeadings ({len(headings)}):")
                        for h in headings[:10]:
                            print(f"  - {h}")
                    except:
                        pass
                
                # Get table data
                table_result = safe_evaluate(page, """
                    (function() {
                        var tables = document.querySelectorAll('table');
                        var result = [];
                        tables.forEach(function(t, i) {
                            var headers = Array.from(t.querySelectorAll('th')).map(function(h) { return h.textContent.trim(); });
                            var rows = Array.from(t.querySelectorAll('tbody tr')).slice(0, 3).map(function(r) {
                                return Array.from(r.querySelectorAll('td')).map(function(d) { return d.textContent.trim(); });
                            });
                            if (headers.length > 0) {
                                result.push({headers: headers, sample_rows: rows});
                            }
                        });
                        return JSON.stringify(result);
                    })()
                """)
                
                if table_result:
                    try:
                        tables = json.loads(table_result) if isinstance(table_result, str) else table_result
                        print(f"\nTables ({len(tables)}):")
                        for t in tables:
                            print(f"  Headers: {t.get('headers', [])}")
                            print(f"  Sample rows: {len(t.get('sample_rows', []))}")
                    except:
                        pass
                
                # Get filter/button elements
                filter_result = safe_evaluate(page, """
                    (function() {
                        var items = [];
                        var els = document.querySelectorAll('button, input, select, [class*="filter"], [class*="search"]');
                        els.forEach(function(el) {
                            var text = (el.textContent || el.placeholder || '').trim().substring(0, 50);
                            if (text) {
                                items.push({tag: el.tagName, type: el.type || '', text: text, cls: el.className.substring(0, 50)});
                            }
                        });
                        return JSON.stringify(items.slice(0, 30));
                    })()
                """)
                
                if filter_result:
                    try:
                        filters = json.loads(filter_result) if isinstance(filter_result, str) else filter_result
                        print(f"\nInteractive elements ({len(filters)}):")
                        for f in filters[:15]:
                            print(f"  [{f['tag']}] {f['type']} {f['text']}")
                    except:
                        pass
                
                # Screenshot
                screenshot_path = os.path.join(OUTPUT_DIR, f"product_{name}_{int(time.time())}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"\nScreenshot: {screenshot_path}")
                
                all_results[name] = {
                    'title': page.title(),
                    'url': page.url,
                    'screenshot': screenshot_path
                }
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
        
        browser.close()
        print("\n=== Exploration Complete ===")
        print(f"Results: {json.dumps(all_results, indent=2)}")

if __name__ == "__main__":
    ensure_output_dir()
    explore_with_playwright()
