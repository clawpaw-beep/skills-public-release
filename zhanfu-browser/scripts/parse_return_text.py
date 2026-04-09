#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

# Read the body text
text_file = os.path.join(OUTPUT_DIR, "return_page_body_text.txt")
with open(text_file, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

print(f"Text length: {len(text)}")
print(f"First 500 chars (repr): {repr(text[:500])}")
print()

# Find all order IDs (18-digit numbers)
order_ids = re.findall(r'\b(\d{18})\b', text)
print(f"Found {len(order_ids)} order IDs: {order_ids}")

# Extract order blocks using regex
# Pattern: 订单 ID : number -> followed by username, date, reason, etc.
order_blocks = re.split(r'(?=订单 ID)', text)
print(f"\nOrder blocks: {len(order_blocks)}")

orders = []
for block in order_blocks:
    if '订单 ID' not in block and '5773' not in block:
        continue

    # Extract fields
    order_id_match = re.search(r'订单 ID\s*[:：]\s*(\d{18})', block)
    username_match = re.search(r'([a-zA-Z0-9_]{3,30})\s*(\d{4}[/年]\d{2}[/月]\d{2})', block)
    date_match = re.search(r'(\d{4}[/年]\d{2}[/月]\d{2}\s*\d{2}:\d{2}:\d{2})', block)
    amount_match = re.search(r'\$\s*(\d+\.\d{2})', block)
    reason_match = re.search(r'退款原因\s*[:：]\s*(.+)', block)
    status_match = re.search(r'(仅退款|退货退款|等待.+?处理|已解决|已申诉)', block)
    items_match = re.search(r'(\d+)\s*个?商品', block)
    tab_match = re.search(r'(等待.+?|已.+?)', block)

    if order_id_match:
        order = {
            'order_id': order_id_match.group(1),
            'username': username_match.group(1) if username_match else '',
            'date': date_match.group(1) if date_match else '',
            'amount': amount_match.group(1) if amount_match else '',
            'reason': reason_match.group(1).strip() if reason_match else '',
            'items': items_match.group(1) if items_match else '',
            'type': '仅退款' if '仅退款' in block else ('退货退款' if '退货退款' in block else ''),
            'status': tab_match.group(1).strip() if tab_match else '',
        }
        orders.append(order)
        print(f"\nOrder: {order['order_id']}")
        for k, v in order.items():
            if v:
                print(f"  {k}: {v}")

print(f"\n\n=== Total orders found: {len(orders)} ===")

# Save
import json
out_file = os.path.join(OUTPUT_DIR, "parsed_return_orders.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(orders, f, ensure_ascii=False, indent=2)
print(f"Saved: {out_file}")
