#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_order_explore_20260407"

# Load cookies
cookies_file = os.path.join(OUTPUT_DIR, "tiktok_cookies.json")
with open(cookies_file, "r", encoding="utf-8") as f:
    cookies = json.load(f)
cookie_list = [c['name'] + '=' + c['value'] for c in cookies]
cookie_str = '; '.join(cookie_list)
csrf = next((c['value'] for c in cookies if c['name'] == 'csrftoken'), '')
ms_token = next((c['value'] for c in cookies if c['name'] == 'msToken'), '')
seller_token = next((c['value'] for c in cookies if c['name'] == 'SELLER_TOKEN'), '')

print(f"csrf: {csrf[:20]}")
print(f"msToken: {ms_token[:20]}")
print(f"SELLER_TOKEN: {seller_token[:30]}")

# Build SELLER_TOKEN payload for extra headers
try:
    token_payload = json.loads(urllib.parse.unquote(seller_token))
    seller_id = token_payload.get('seller_id', '')
    print(f"Seller ID from token: {seller_id}")
except:
    seller_id = '7494148854457534288'

def make_request(url, method='GET', body=None, extra_headers=None):
    req = urllib.request.Request(url, data=body.encode() if body else None, method=method)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
    req.add_header('Accept', 'application/json, text/plain, */*')
    req.add_header('Accept-Language', 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7')
    req.add_header('Cookie', cookie_str)
    req.add_header('Referer', 'https://seller.us.tiktokshopglobalselling.com/order/manage')
    req.add_header('Origin', 'https://seller.us.tiktokshopglobalselling.com')
    req.add_header('x-csrftoken', csrf)
    req.add_header('x-sousaa', ms_token)
    req.add_header('x-tos-client-id', 'tts_seller_pc')
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body_resp = resp.read()
            headers = dict(resp.headers)
            return {'status': status, 'headers': headers, 'body': body_resp}
    except urllib.error.HTTPError as e:
        return {'status': e.code, 'error': str(e), 'body': e.read() if e.fp else None}
    except Exception as e:
        return {'status': 0, 'error': str(e)}

# Test the open-api endpoint with different variations
print("\n=== Testing /open-api/order/list ===")

test_cases = [
    # POST with various body formats
    ('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list',
     json.dumps({"shop_region":"US","mall_id":2376919,"page":1,"page_size":20}),
     {'Content-Type': 'application/json'}),
    ('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list',
     json.dumps({"shop_region":"US","page":1,"page_size":20,"sort":"update_time_desc"}),
     {'Content-Type': 'application/json'}),
    ('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list',
     json.dumps({"shop_region":"US","seller_id":7494148854457534288,"page":1,"page_size":20}),
     {'Content-Type': 'application/json'}),
    ('POST', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list',
     json.dumps({}), {'Content-Type': 'application/json'}),
    # GET
    ('GET', 'https://seller.us.tiktokshopglobalselling.com/open-api/order/list?shop_region=US&mall_id=2376919&page=1&page_size=20', None, {}),
]

for method, url, body, extra in test_cases:
    result = make_request(url, method, body, extra)
    status = result.get('status')
    if status == 200:
        body_bytes = result.get('body', b'')
        resp_headers = result.get('headers', {})
        ct = resp_headers.get('Content-Type', '')
        cl = resp_headers.get('Content-Length', '?')
        print(f"\n[{status}] {method} {url[:80]}")
        print(f"  Content-Type: {ct}, Content-Length: {cl}")
        print(f"  Body ({len(body_bytes)} bytes): {body_bytes[:200]}")
    else:
        print(f"\n[{status}] {method} {url[:80]}: {result.get('error', result.get('body', '')[:100])}")

# Try other potentially valid API paths
print("\n=== Testing other API paths ===")
other_paths = [
    'GET',
    'https://seller.us.tiktokshopglobalselling.com/api/v2/order/list?shop_region=US&seller_id=7494148854457534288&page=1&page_size=20',
    'POST',
    'https://seller.us.tiktokshopglobalselling.com/api/v2/order/list',
    json.dumps({"shop_region":"US","seller_id":7494148854457534288,"page":1,"page_size":20}),
    'GET',
    'https://seller.us.tiktokshopglobalselling.com/api/v1/orders?shop_region=US&seller_id=7494148854457534288',
    'GET',
    'https://seller.us.tiktokshopglobalselling.com/api/v1/seller/orders?shop_region=US&seller_id=7494148854457534288',
    'POST',
    'https://seller.us.tiktokshopglobalselling.com/api/v1/order/list',
    json.dumps({"shop_region":"US","seller_id":7494148854457534288}),
]

for i in range(0, len(other_paths), 3):
    method = other_paths[i]
    url = other_paths[i+1]
    body = other_paths[i+2] if i+2 < len(other_paths) else None
    result = make_request(url, method, body, {'Content-Type': 'application/json'} if body else {})
    status = result.get('status')
    if status == 200:
        body_bytes = result.get('body', b'')
        print(f"\n[{status}] {method} {url[:100]}")
        print(f"  Body ({len(body_bytes)}): {body_bytes[:300]}")
    else:
        print(f"\n[{status}] {method} {url[:100]}")

print("\n=== Done ===")
