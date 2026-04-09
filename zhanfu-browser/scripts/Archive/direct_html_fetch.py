#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, json, re, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

# Load cookies
cookies_file = os.path.join(OUTPUT_DIR, "tiktok_cookies.json")
with open(cookies_file, "r", encoding="utf-8") as f:
    cookies = json.load(f)
cookie_str = '; '.join(c['name'] + '=' + c['value'] for c in cookies)

def fetch_url(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
    req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    req.add_header('Accept-Language', 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7')
    req.add_header('Cookie', cookie_str)
    req.add_header('Referer', 'https://seller.us.tiktokshopglobalselling.com/')
    req.add_header('Upgrade-Insecure-Requests', '1')
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace'), {}
    except Exception as e:
        return 0, str(e), {}

print("=== Fetch order/return page HTML ===")
status, html, headers = fetch_url('https://seller.us.tiktokshopglobalselling.com/order/return')
print(f"Status: {status}")
print(f"Content-Type: {headers.get('Content-Type', '?')}")
print(f"HTML length: {len(html)}")

# Search for order data in HTML
print("\n=== Search for order data ===")

# Look for __NEXT_DATA__ or similar
next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if next_data:
    print("Found __NEXT_DATA__!")
    data = json.loads(next_data.group(1))
    out_file = os.path.join(OUTPUT_DIR, "next_data.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_file}")
    # Look for order-related data
    data_str = json.dumps(data)
    if 'order' in data_str.lower():
        print("Contains 'order' references!")
        # Find order-related keys
        def find_keys(obj, path=''):
            results = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'order' in k.lower():
                        results.append((path + '.' + k, str(v)[:200]))
                    results.extend(find_keys(v, path + '.' + k))
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    results.extend(find_keys(v, path + f'[{i}]'))
            return results
        order_keys = find_keys(data)
        print(f"Order-related keys: {len(order_keys)}")
        for k, v in order_keys[:10]:
            print(f"  {k}: {v}")

# Look for orderList
order_list_match = re.search(r'"orderList"\s*:\s*(\[.*?\])', html, re.DOTALL)
if order_list_match:
    print("\nFound orderList!")
    try:
        order_list = json.loads(order_list_match.group(1))
        print(f"Order list length: {len(order_list)}")
        out_file = os.path.join(OUTPUT_DIR, "order_list.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(order_list, f, ensure_ascii=False, indent=2)
        print(f"Saved: {out_file}")
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Content: {order_list_match.group(1)[:500]}")

# Look for reverseOrders
reverse_match = re.search(r'"reverseOrders"\s*:\s*(\[.*?\])', html, re.DOTALL)
if reverse_match:
    print("\nFound reverseOrders!")
    try:
        reverse = json.loads(reverse_match.group(1))
        print(f"Length: {len(reverse)}")
        out_file = os.path.join(OUTPUT_DIR, "reverse_orders.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(reverse, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Parse error: {e}")

# Look for any large JSON arrays in scripts
print("\n=== Look for embedded data in scripts ===")
script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
order_data_found = []
for i, script in enumerate(script_matches):
    if len(script) > 1000 and ('order' in script.lower() or 'return' in script.lower()):
        # Try to find JSON data
        json_matches = re.findall(r'\\{[^{}]{50,}\\}', script)
        for jm in json_matches[:3]:
            if 'order' in jm.lower() or 'return' in jm.lower():
                try:
                    parsed = json.loads(jm)
                    if any('order' in str(k).lower() or 'return' in str(k).lower() for k in parsed.keys()):
                        order_data_found.append(parsed)
                except:
                    pass

print(f"Order data found in scripts: {len(order_data_found)}")

# Save HTML
out_file = os.path.join(OUTPUT_DIR, "return_page.html")
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nHTML saved: {out_file}")
