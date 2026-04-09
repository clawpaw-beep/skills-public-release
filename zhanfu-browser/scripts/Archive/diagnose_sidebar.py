#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose current page state and find correct selectors."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Go to product list
    page.goto("https://seller.us.tiktokshopglobalselling.com/product/list",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(5)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Try different selectors
    selectors = [
        ".core-menu-item",
        "[class*='menu']",
        "nav",
        ".ant-menu",
        "[role='menuitem']"
    ]

    for sel in selectors:
        count = page.evaluate(f"""() => {{
            return document.querySelectorAll('{sel}').length;
        }}""")
        print(f"Selector '{sel}': {count} elements")

    # Get all text content of body
    all_text = page.evaluate("() => document.body.innerText.substring(0, 500)")
    print(f"\nBody text: {all_text}")

    # Try to find and print all menu-like items
    menu_items = page.evaluate("""() => {
        var items = [];
        // Try multiple approaches
        var approaches = [
            document.querySelectorAll('.core-menu-item'),
            document.querySelectorAll('[class*="menu-item"]'),
            document.querySelectorAll('[role="menuitem"]'),
            document.querySelectorAll('.ant-menu-item')
        ];
        var labels = ['.core-menu-item', '[class*="menu-item"]', '[role="menuitem"]', '.ant-menu-item'];
        for (var a = 0; a < approaches.length; a++) {
            if (approaches[a].length > 0) {
                items.push({selector: labels[a], count: approaches[a].length, texts: Array.from(approaches[a]).map(function(el) { return el.innerText.trim().substring(0, 50); }).slice(0, 10)});
            }
        }
        return JSON.stringify(items);
    }""")

    print(f"\nMenu items found: {menu_items}")

    # Take screenshot
    page.screenshot(path=f"{OUTPUT_DIR}/diagnose_sidebar.png", full_page=True)
    print(f"\nScreenshot saved")

    browser.close()
