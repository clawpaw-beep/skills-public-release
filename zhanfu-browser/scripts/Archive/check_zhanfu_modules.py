#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\9400\.openclaw\workspace\skills\zhanfu-browser\scripts')
from zhanfu_runtime import post
import json

# Try to find what modules are available
modules = ['OrderModule', 'ShopModule', 'ProductModule', 'FinanceModule', 'AffiliateModule']
for m in modules:
    resp = post({'module': m, 'action': 'GetList'})
    print(f'{m}: ret={resp.get("ret")} error={resp.get("error", "ok")}')

# Try WebDriverModule with different actions
actions = ['GetBrowserInfo', 'GetShopInfo', 'GetShopList', 'GetMallInfo']
for a in actions:
    resp = post({'module': 'WebDriverModule', 'action': a})
    print(f'WebDriverModule.{a}: ret={resp.get("ret")}')
