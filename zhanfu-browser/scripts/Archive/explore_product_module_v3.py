#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explore product module and save results with proper encoding."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

MALL_ID = "2376919"
OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_store_readonly_explore_20260407_fmcg"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def run():
    print(f"=== Product Module Explorer v3 ===")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Navigate to product/list
        url = "https://seller.us.tiktokshopglobalselling.com/product/list"
        print(f"Going to: {url}")
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        time.sleep(3)
        
        # Extract full menu structure
        menu_data = page.evaluate("""
            (function() {
                var result = {items: [], url: window.location.href, title: document.title};
                
                // Get all menu items using multiple approaches
                var allItems = [];
                
                // Approach 1: ant-menu items
                var menuItems = document.querySelectorAll('.ant-menu-item, .ant-menu-submenu-title, [class*="menu-item"]');
                menuItems.forEach(function(el) {
                    var text = el.textContent.trim().replace(/\\s+/g, ' ');
                    var href = '';
                    var a = el.querySelector('a');
                    if (a) href = a.href || a.getAttribute('href') || '';
                    else href = el.getAttribute('href') || '';
                    allItems.push({text: text.substring(0, 100), href: href.substring(0, 150), tag: el.tagName, cls: el.className.substring(0, 80)});
                });
                
                // Approach 2: role=menuitem
                if (allItems.length < 5) {
                    var roleItems = document.querySelectorAll('[role="menuitem"]');
                    roleItems.forEach(function(el) {
                        var text = el.textContent.trim().replace(/\\s+/g, ' ');
                        var href = el.getAttribute('href') || '';
                        allItems.push({text: text.substring(0, 100), href: href.substring(0, 150), tag: el.tagName, cls: el.className.substring(0, 80)});
                    });
                }
                
                // Remove duplicates by text
                var seen = {};
                var unique = [];
                allItems.forEach(function(item) {
                    if (item.text && !seen[item.text]) {
                        seen[item.text] = true;
                        unique.push(item);
                    }
                });
                
                result.items = unique;
                return JSON.stringify(result);
            })()
        """)
        
        menu_obj = json.loads(menu_data)
        
        # Save raw results
        output_file = os.path.join(OUTPUT_DIR, "product_module_menu.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(menu_data)
        print(f"Menu data saved: {output_file}")
        print(f"URL: {menu_obj.get('url')}")
        print(f"Title: {menu_obj.get('title')}")
        print(f"Total menu items: {len(menu_obj.get('items', []))}")
        
        print("\n=== Menu Items ===")
        for item in menu_obj.get('items', []):
            print(f"  {item['text']} -> {item['href']}")
        
        # Screenshot
        screenshot_path = os.path.join(OUTPUT_DIR, f"product_list_v3_{int(time.time())}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nScreenshot: {screenshot_path}")
        
        browser.close()

if __name__ == "__main__":
    ensure_output_dir()
    run()
