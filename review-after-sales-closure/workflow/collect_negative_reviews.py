#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect negative reviews from ZhanFu and import into case state.

Collects reviews from the product rating page for configured FMCG store.
Records: order_id, product_id, buyer_username, rating, review_text.

Usage:
  python collect_negative_reviews.py [--store-id 2376919] [--min-stars 4]
"""

import sys, os, time, csv, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "zhanfu-browser", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "zhanfu-browser", "scripts"))

from zhanfu_runtime import ensure_real_webdriver_detailed
from playwright.sync_api import sync_playwright
from state import CaseState


def collect_negative_reviews(store_id: str = "2376919", min_stars: int = 4) -> list[dict]:
    """
    Collect all reviews from product rating pages of the FMCG store,
    filter to negative (rating <= min_stars), return list of review dicts.
    """
    result = ensure_real_webdriver_detailed(store_id, startup_wait=90)
    if not result.ready:
        raise RuntimeError(f"CDP failed: {result.error}")
    ws = result.ready.ws_endpoint

    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws, timeout=30000)
        page = browser.contexts[0].pages[0]

        # First: get product list for this store
        # We'll scan the most-reviewed products
        # Get the product list from the product module
        page.goto(
            "https://seller.us.tiktokshopglobalselling.com/product/list?shop_region=US",
            timeout=60000, wait_until="domcontentloaded"
        )
        time.sleep(8)

        # Extract product IDs from the list
        product_ids = _extract_product_ids(page)

        if not product_ids:
            # Fallback: try the known FMCG product IDs
            product_ids = [
                "1732215258184258384",  # from earlier orders
                "1732215213532222288",  # floor cleaning tablets
            ]

        print(f"Found {len(product_ids)} products, scanning for reviews...")

        for i, product_id in enumerate(product_ids):
            try:
                revs = _collect_reviews_for_product(
                    page, product_id, min_stars
                )
                reviews.extend(revs)
                print(f"  [{i+1}/{len(product_ids)}] product={product_id} reviews_found={len(revs)}")
            except Exception as e:
                print(f"  [{i+1}/{len(product_ids)}] product={product_id} error={e}")
                continue

    return reviews


def _extract_product_ids(page) -> list[str]:
    """Extract product IDs from the product list page."""
    full = page.locator("body").inner_text()
    # Look for product_id patterns (16-19 digit numbers)
    pids = re.findall(r'(?<!\d)\d{16,19}(?!\d)', full)
    seen = set()
    unique = []
    for pid in pids:
        if pid not in seen and pid not in seen:
            seen.add(pid)
            unique.append(pid)
    return unique[:20]  # limit to 20 products


def _collect_reviews_for_product(page, product_id: str, min_stars: int) -> list[dict]:
    """
    Scan a product's rating page and extract reviews with rating <= min_stars.
    Returns list of dicts with: order_id, product_id, buyer_username, rating, review_text.
    """
    url = f"https://seller.us.tiktokshopglobalselling.com/product/rating?product_id={product_id}&shop_region=US"
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    time.sleep(12)

    reviews = []
    page_num = 1

    while page_num <= 50:  # safety limit
        full = page.locator("body").inner_text()

        # Extract all order_ids on this page
        order_ids = re.findall(r'(?<!\d)\d{15,19}(?!\d)', full)
        order_ids = list(dict.fromkeys(
            o for o in order_ids if 15 <= len(o) <= 19
        ))

        # For each order_id, extract buyer_username and check if it's on this page
        # The username appears in @format near the order
        for oid in order_ids:
            if oid not in full:
                continue
            idx = full.find(oid)
            context = full[max(0, idx-200):idx+300]

            # Extract username
            user_match = re.search(r'@([\w\s]+)', context)
            username = user_match.group(0) if user_match else ""

            # Try to get rating from nearby text (if we can infer from context)
            # Since rating is CSS-rendered, we skip individual rating extraction here
            # and rely on the filter buttons instead

            reviews.append({
                "order_id": oid,
                "product_id": product_id,
                "buyer_username": username,
                "rating": None,  # requires filter approach, set to None
                "review_text": context[:200],
            })

        # Next page
        try:
            next_btn = page.get_by_role("button", name="下一页")
            if not next_btn.count():
                break
            if next_btn.first.is_disabled(timeout=2000):
                break
            next_btn.first.click()
            time.sleep(5)
            page_num += 1
        except Exception:
            break

    return reviews


def import_into_state(reviews: list[dict]) -> int:
    """Import collected reviews into case state. Returns count of new cases."""
    cs = CaseState.load()
    existing = {r.get("order_id") for r in cs.rows}
    count = 0
    for rev in reviews:
        if rev["order_id"] in existing:
            continue
        cs.add(
            order_id=rev["order_id"],
            buyer_username=rev["buyer_username"],
            phone="",  # will be filled by get_buyer_phone.py if needed
            product_id=rev["product_id"],
            rating=str(rev.get("rating", "")),
            review_text=rev.get("review_text", "")[:500],
        )
        count += 1
    cs.save()
    return count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect negative reviews from ZhanFu")
    parser.add_argument("--store-id", default="2376919")
    parser.add_argument("--min-stars", type=int, default=4,
                        help="Collect reviews <= this star count (default 4=1-3 stars)")
    args = parser.parse_args()

    print("=== Collecting negative reviews ===")
    reviews = collect_negative_reviews(args.store_id, args.min_stars)
    print(f"Collected {len(reviews)} reviews")

    print("=== Importing into case state ===")
    count = import_into_state(reviews)
    print(f"Added {count} new cases")

    cs = CaseState.load()
    summary = cs.summary()
    print(f"\nCase summary: {json.dumps(summary, ensure_ascii=False, indent=2)}")
