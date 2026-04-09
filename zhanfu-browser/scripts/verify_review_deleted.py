#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify if a buyer's review has been deleted.

Uses order_id as the primary key — each review block on the product rating page
contains the order ID, visible in plain text.

  order_id found  → review still exists → status = "present"
  order_id not found → review deleted → status = "deleted"

Note: star rating cannot be extracted from innerText (SVG/CSS rendered).
For rating change detection (negative→positive), use the filter-button
approach: click "4" or "5" filter; if order_id appears, rating≥4.
This requires 2-5 extra page loads (~30-60s) and is optional.

Usage:
  python verify_review_deleted.py <order_id> <product_id> [browser_id]

Examples:
  python verify_review_deleted.py 577323576510550851 1732215213532222288
"""

import sys, os, time, re, json
sys.path.insert(0, os.path.dirname(__file__))

from zhanfu_runtime import ensure_real_webdriver_detailed
from playwright.sync_api import sync_playwright


def verify_review_deleted(order_id, product_id, browser_id='2376919'):
    """
    Returns:
      {
        "order_id": str,
        "product_id": str,
        "status": "deleted" | "present",
        "found_on_page": int or None,
        "error": str or None
      }
    """
    result = ensure_real_webdriver_detailed(browser_id, startup_wait=90)
    if not result.ready:
        return {"error": f"CDP failed: {result.error}", "order_id": order_id}

    ws = result.ready.ws_endpoint
    base_url = f"https://seller.us.tiktokshopglobalselling.com/product/rating?product_id={product_id}&shop_region=US"

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws, timeout=30000)
        page = browser.contexts[0].pages[0]

        page.goto(base_url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(12)

        page_num = 1
        max_pages = 200  # ~200 pages for 2083 reviews

        while page_num <= max_pages:
            full = page.locator('body').inner_text()

            if order_id in full:
                return {
                    "order_id": order_id,
                    "product_id": product_id,
                    "status": "present",
                    "found_on_page": page_num,
                }

            # Try next page
            try:
                next_btn = page.get_by_role("button", name="下一页")
                if not next_btn.count():
                    break
                next_btn.first.click()
            except Exception:
                break

            time.sleep(5)
            page_num += 1

        # Not found on any page
        return {
            "order_id": order_id,
            "product_id": product_id,
            "status": "deleted",
            "found_on_page": None,
        }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_review_deleted.py <order_id> <product_id> [browser_id]")
        sys.exit(1)

    order_id = sys.argv[1]
    product_id = sys.argv[2]
    browser_id = sys.argv[3] if len(sys.argv) > 3 else '2376919'

    r = verify_review_deleted(order_id, product_id, browser_id)
    print(json.dumps(r, ensure_ascii=False, indent=2))

    if r.get("error"):
        sys.exit(1)

    icon = "[X]" if r["status"] == "deleted" else "[OK]"
    print(f"\n{icon} order={r['order_id']} status={r['status']} page={r.get('found_on_page')}")
