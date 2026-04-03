"""
获取TikTok Shop订单详情页中的买家电话
用法: python get_buyer_phone.py <order_no> [cdp_url]
示例: python get_buyer_phone.py 577323576510550851
      python get_buyer_phone.py 577323576510550851 ws://127.0.0.1:12636/devtools/browser/xxx

依赖: pip install playwright && playwright install chromium
"""
import asyncio
import sys
import re
import json
import urllib.request


def get_fmcg_cdp_url():
    """从ZhanFu HTTP API自动获取FMCG店铺的CDP URL"""
    try:
        payload = json.dumps({'module': 'WebDriverModule', 'action': 'GetBrowserWebDriver', 'browserId': '2376919'}).encode()
        req = urllib.request.Request(
            'http://127.0.0.1:45008',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)
            # 键名可能是 webDriverPort 或 WebDriverPort
            ret_obj = data.get('returnObj', {})
            port = ret_obj.get('webDriverPort') or ret_obj.get('WebDriverPort')
            if not port:
                return None
            ver_req = urllib.request.Request(f'http://127.0.0.1:{port}/json/version')
            with urllib.request.urlopen(ver_req, timeout=5) as vresp:
                ver = json.loads(vresp.read())
                return ver.get('webSocketDebuggerUrl')
    except Exception as e:
        print(f"自动获取CDP URL失败: {e}")
        return None


async def get_buyer_phone(order_no: str, cdp_url: str = None):
    """通过ZhanFu CDP连接到订单详情页，提取买家电话"""
    from playwright.async_api import async_playwright

    if not cdp_url:
        cdp_url = get_fmcg_cdp_url()

    if not cdp_url:
        print("错误: 缺少CDP URL，且自动获取失败。请手动传入: python get_buyer_phone.py <order_no> <cdp_url>")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        order_url = f"https://seller.us.tiktokshopglobalselling.com/order/detail?order_no={order_no}&shop_region=US"
        await page.goto(order_url, timeout=30000)
        await page.wait_for_load_state("domcontentloaded", timeout=20000)
        await page.wait_for_timeout(5000)

        text = await page.inner_text("body")

        # 提取买家电话 (e.g. (+1)9547735284)
        phone_match = re.search(r'\(\+\d+\)\d+', text)
        phone = phone_match.group(0) if phone_match else None

        # 提取买家用户名
        username_match = re.search(r'用户名\s*\n?\s*([a-zA-Z0-9._-]+)', text)
        username = username_match.group(1) if username_match else None

        # 提取收货地址
        addr_match = re.search(r'收货地址\s*\n?\s*(.+?)(?=\n\n|\Z)', text, re.DOTALL)
        address = addr_match.group(1).replace('\n', ' ').strip() if addr_match else None

        result = {
            'order_no': order_no,
            'buyer_username': username,
            'buyer_phone': phone,
            'buyer_address': address
        }

        print(f"订单号: {order_no}")
        print(f"买家用户名: {username}")
        print(f"买家电话: {phone}")
        if address:
            print(f"收货地址: {address[:60]}...")

        await browser.close()
        return result


if __name__ == '__main__':
    order_no = sys.argv[1] if len(sys.argv) > 1 else '577323576510550851'
    cdp_url = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(get_buyer_phone(order_no, cdp_url))
