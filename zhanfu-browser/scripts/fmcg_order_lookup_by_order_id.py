#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from zhanfu_runtime import ensure_real_webdriver


OUTPUT_DIR = Path(r"C:\Users\9400\Documents")
INPUT_CSV = OUTPUT_DIR / "fmcg_negative_review_followup.csv"
OUTPUT_CSV = OUTPUT_DIR / "fmcg_order_lookup_safe.csv"
OUTPUT_JSON = OUTPUT_DIR / "fmcg_order_lookup_safe.json"

FMCG_BROWSER_ID = 2376919
SHOP_REGION = "US"
DETAIL_URL_TEMPLATE = (
    "https://seller.us.tiktokshopglobalselling.com/order/detail"
    "?order_no={order_id}&shop_region=US"
)

KEY_LOCATION = "\u4f4d\u7f6e"
KEY_CREATED_TIME = "\u521b\u5efa\u65f6\u95f4"
KEY_LOGISTICS_METHOD = "\u7269\u6d41\u65b9\u5f0f"
KEY_LOGISTICS_OPTION = "\u7269\u6d41\u9009\u9879"
KEY_ORDER_TYPE = "\u8ba2\u5355\u7c7b\u578b"
KEY_FULFILLMENT_TYPE = "\u5c65\u7ea6\u7c7b\u578b"
KEY_WAREHOUSE_NAME = "\u4ed3\u5e93\u540d\u79f0"
KEY_WAREHOUSE_ID = "\u4ed3\u5e93\u7f16\u53f7"
KEY_HISTORY = "\u5386\u53f2\u8ba2\u5355"
KEY_CUSTOMER_PAID = "\u5ba2\u6237\u652f\u4ed8\u7684\u91d1\u989d"
KEY_PAYMENT_METHOD = "\u652f\u4ed8\u65b9\u5f0f"
KEY_TOTAL = "\u5168\u90e8"
KEY_EARNINGS = "\u4f60\u8d5a\u53d6\u7684\u91d1\u989d"
KEY_USERNAME = "\u7528\u6237\u540d"
KEY_CUSTOMER_NICKNAME = "\u5ba2\u6237\u6635\u79f0"
KEY_ADDRESS = "\u6536\u8d27\u5730\u5740"
KEY_TRACK_PACKAGE = "\u8ddf\u8e2a\u5305\u88f9"
KEY_MORE_ACTIONS = "\u66f4\u591a\u64cd\u4f5c"
KEY_REFUND = "\u9000\u6b3e"

EVENT_DELIVERED = "\u8ba2\u5355\u5df2\u9001\u8fbe\u5e76\u7b7e\u6536"
EVENT_PAID = "\u8ba2\u5355\u5df2\u4ed8\u6b3e"
EVENT_READY = "\u8ba2\u5355\u51c6\u5907\u53d1\u8d27"
EVENT_CREATED = "\u5ba2\u6237\u521b\u5efa\u8ba2\u5355"



def read_review_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def cleaned_lines(body_text):
    return [line.strip() for line in body_text.splitlines() if line.strip()]


def line_after(lines, label, start_index=0):
    try:
        idx = lines.index(label, start_index)
    except ValueError:
        return ""
    if idx + 1 < len(lines):
        return lines[idx + 1]
    return ""


def line_startswith(lines, prefix):
    for line in lines:
        if line.startswith(prefix):
            return line
    return ""


def history_time(lines, event_name):
    try:
        idx = lines.index(event_name)
    except ValueError:
        return ""
    if idx + 1 < len(lines):
        return lines[idx + 1]
    return ""


def extract_status(lines, order_id):
    try:
        idx = lines.index(KEY_LOCATION)
    except ValueError:
        return ""

    action_like = {
        order_id,
        KEY_REFUND,
        KEY_MORE_ACTIONS,
    }
    candidates = [line for line in lines[:idx] if line and line not in action_like]
    return candidates[-1] if candidates else ""


def extract_total_paid(lines):
    try:
        paid_idx = lines.index(KEY_CUSTOMER_PAID)
    except ValueError:
        return ""
    try:
        total_idx = lines.index(KEY_TOTAL, paid_idx)
    except ValueError:
        return ""
    if total_idx + 1 < len(lines):
        return lines[total_idx + 1]
    return ""


def extract_earnings(lines):
    try:
        idx = lines.index(KEY_EARNINGS)
    except ValueError:
        return "", ""
    next_one = lines[idx + 1] if idx + 1 < len(lines) else ""
    next_two = lines[idx + 2] if idx + 2 < len(lines) else ""
    if next_one.startswith("$") or next_one.startswith("USD"):
        return "", next_one
    return next_one, next_two


def extract_product_block(lines):
    sku_line = line_startswith(lines, "SKU ID:")
    sku_id = sku_line.split(":", 1)[1].strip() if sku_line else ""

    product_name = ""
    variant_name = ""
    merchant_sku = ""
    package_status = ""

    for index, line in enumerate(lines):
        if line.startswith("\u5305\u88f9") and "\uff1a" in line:
            if index + 1 < len(lines):
                package_status = lines[index + 1]
        if line.startswith("SKU ID:"):
            if index + 1 < len(lines):
                product_name = lines[index + 1]
            if index + 2 < len(lines):
                variant_name = lines[index + 2]
            break

    merchant_line = line_startswith(lines, "\u5546\u5bb6 SKU\uff1a")
    if merchant_line:
        merchant_sku = merchant_line.split("\uff1a", 1)[1].strip()

    return {
        "package_status": package_status,
        "sku_id": sku_id,
        "product_name": product_name,
        "variant_name": variant_name,
        "merchant_sku": merchant_sku,
        "has_tracking_link": KEY_TRACK_PACKAGE in lines,
    }


def extract_safe_fields(order_id, body_text):
    lines = cleaned_lines(body_text)
    earnings_note, earnings_amount = extract_earnings(lines)

    result = {
        "order_id": order_id,
        "detail_url": DETAIL_URL_TEMPLATE.format(order_id=order_id),
        "order_status": extract_status(lines, order_id),
        "location": line_after(lines, KEY_LOCATION),
        "created_time": line_after(lines, KEY_CREATED_TIME),
        "logistics_method": line_after(lines, KEY_LOGISTICS_METHOD),
        "logistics_option": line_after(lines, KEY_LOGISTICS_OPTION),
        "order_type": line_after(lines, KEY_ORDER_TYPE),
        "fulfillment_type": line_after(lines, KEY_FULFILLMENT_TYPE),
        "warehouse_name": line_after(lines, KEY_WAREHOUSE_NAME),
        "warehouse_id": line_after(lines, KEY_WAREHOUSE_ID),
        "payment_method": line_after(lines, KEY_PAYMENT_METHOD),
        "customer_paid_total": extract_total_paid(lines),
        "earnings_note": earnings_note,
        "earnings_amount": earnings_amount,
        "buyer_username": line_after(lines, KEY_USERNAME),
        "buyer_nickname": line_after(lines, KEY_CUSTOMER_NICKNAME),
        "has_address_section": KEY_ADDRESS in lines,
        "history_delivered_at": history_time(lines, EVENT_DELIVERED),
        "history_paid_at": history_time(lines, EVENT_PAID),
        "history_ready_to_ship_at": history_time(lines, EVENT_READY),
        "history_created_at": history_time(lines, EVENT_CREATED),
    }
    result.update(extract_product_block(lines))
    return result


def lookup_orders(review_rows, ws_endpoint: str | None = None, flush_every: int = 1, progress: bool = True):
    if not ws_endpoint:
        ready, error = ensure_real_webdriver(FMCG_BROWSER_ID, startup_wait=90, reopen_once=True)
        if not ready:
            raise RuntimeError(error or "failed to get real webdriver endpoint")
        ws_endpoint = ready.ws_endpoint
    results = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        total = len(review_rows)
        ok_count = 0
        error_count = 0
        for index, row in enumerate(review_rows, start=1):
            order_id = (row.get("order_id") or "").strip()
            if not order_id:
                continue

            detail_url = DETAIL_URL_TEMPLATE.format(order_id=order_id)
            merged = {
                "order_id": order_id,
                "review_date": row.get("review_date", ""),
                "review_star": row.get("star_count", ""),
                "review_username": row.get("username", "") or row.get("platform_contact", ""),
                "review_text": row.get("review_text", ""),
                "seller_reply_present": row.get("has_reply", ""),
                "lookup_result": "ok",
                "lookup_note": "",
            }

            try:
                page.goto(detail_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4500)
                body_text = page.locator("body").inner_text(timeout=30000)
                merged.update(extract_safe_fields(order_id, body_text))
                ok_count += 1
            except Exception as exc:
                merged["detail_url"] = detail_url
                merged["lookup_result"] = "error"
                merged["lookup_note"] = str(exc)
                error_count += 1

            results.append(merged)
            if flush_every and index % flush_every == 0:
                write_csv(results, OUTPUT_CSV)
                OUTPUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            if progress:
                print(json.dumps({"progress": {"current": index, "total": total, "ok": ok_count, "error": error_count, "order_id": order_id}}, ensure_ascii=False))
            page.wait_for_timeout(800)

        page.close()

    return results


def write_csv(rows, path):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    review_rows = read_review_rows(INPUT_CSV)
    results = lookup_orders(review_rows, ws_endpoint=None, flush_every=1)
    write_csv(results, OUTPUT_CSV)
    OUTPUT_JSON.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"csv": str(OUTPUT_CSV), "json": str(OUTPUT_JSON), "count": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
