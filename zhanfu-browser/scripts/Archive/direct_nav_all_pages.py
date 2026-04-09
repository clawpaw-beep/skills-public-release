#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direct URL navigation to target pages + full page text extraction."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

# Try various URL patterns for each module
URL_PATTERNS = {
    # 触达/客户
    "触达": [
        "https://seller.us.tiktokshopglobalselling.com/marketing/reach",
        "https://seller.us.tiktokshopglobalselling.com/reach/overview",
        "https://seller.us.tiktokshopglobalselling.com/cm/marketing/reach",
    ],
    "客户群": [
        "https://seller.us.tiktokshopglobalselling.com/buyer/group",
        "https://seller.us.tiktokshopglobalselling.com/customer/group",
    ],
    # 促销
    "促销活动": [
        "https://seller.us.tiktokshopglobalselling.com/marketing/promotion",
        "https://seller.us.tiktokshopglobalselling.com/spark/overview",
        "https://seller.us.tiktokshopglobalselling.com/marketing/campaigns",
    ],
    "店铺广告": [
        "https://seller.us.tiktokshopglobalselling.com/shop-ad/overview",
        "https://seller.us.tiktokshopglobalselling.com/shop-ad",
    ],
    "智能营销": [
        "https://seller.us.tiktokshopglobalselling.com/marketing/smart",
        "https://seller.us.tiktokshopglobalselling.com/smart-marketing",
    ],
    "店铺页面": [
        "https://seller.us.tiktokshopglobalselling.com/shop/display",
        "https://seller.us.tiktokshopglobalselling.com/shop-page",
    ],
    # 数据分析
    "店铺数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/store",
        "https://seller.us.tiktokshopglobalselling.com/analytics/overview",
    ],
    "直播和视频数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/live",
        "https://seller.us.tiktokshopglobalselling.com/analytics/video",
    ],
    "商品卡": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/product-card",
        "https://seller.us.tiktokshopglobalselling.com/product/analytics",
    ],
    "商品数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/product",
        "https://seller.us.tiktokshopglobalselling.com/analytics/goods",
    ],
    "营销数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/marketing",
        "https://seller.us.tiktokshopglobalselling.com/analytics/campaign",
    ],
    "客户数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/customer",
        "https://seller.us.tiktokshopglobalselling.com/analytics/users",
    ],
    "排行榜": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/ranking",
        "https://seller.us.tiktokshopglobalselling.com/rank",
    ],
    "售后数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/analytics/after-sales",
        "https://seller.us.tiktokshopglobalselling.com/analytics/refund",
    ],
    # 账号健康
    "店铺健康": [
        "https://seller.us.tiktokshopglobalselling.com/accountHealth/health",
        "https://seller.us.tiktokshopglobalselling.com/health",
    ],
    "店铺体验分": [
        "https://seller.us.tiktokshopglobalselling.com/accountHealth/score",
        "https://seller.us.tiktokshopglobalselling.com/experience-score",
    ],
    "达人健康评分": [
        "https://seller.us.tiktokshopglobalselling.com/affiliate/health",
        "https://seller.us.tiktokshopglobalselling.com/creator-health",
    ],
    "明星商家认证计划": [
        "https://seller.us.tiktokshopglobalselling.com/accountHealth/certification",
        "https://seller.us.tiktokshopglobalselling.com/star-merchant",
    ],
    # 合规
    "合规看板": [
        "https://seller.us.tiktokshopglobalselling.com/compliance/dashboard",
        "https://seller.us.tiktokshopglobalselling.com/compliance/overview",
    ],
    "合规资质": [
        "https://seller.us.tiktokshopglobalselling.com/compliance/qualification",
        "https://seller.us.tiktokshopglobalselling.com/compliance/cert",
    ],
    "商品合规诊断": [
        "https://seller.us.tiktokshopglobalselling.com/compliance/product",
        "https://seller.us.tiktokshopglobalselling.com/compliance/diagnosis",
    ],
    # 成长
    "经营洞察": [
        "https://seller.us.tiktokshopglobalselling.com/growth/insight",
        "https://seller.us.tiktokshopglobalselling.com/insight",
    ],
    "成长权益": [
        "https://seller.us.tiktokshopglobalselling.com/growth/benefits",
        "https://seller.us.tiktokshopglobalselling.com/benefits",
    ],
    "我的任务": [
        "https://seller.us.tiktokshopglobalselling.com/growth/task",
        "https://seller.us.tiktokshopglobalselling.com/task",
    ],
    "我的奖励": [
        "https://seller.us.tiktokshopglobalselling.com/growth/reward",
        "https://seller.us.tiktokshopglobalselling.com/reward",
    ],
    # 财务
    "财务概览": [
        "https://seller.us.tiktokshopglobalselling.com/finance/overview",
        "https://seller.us.tiktokshopglobalselling.com/finance",
    ],
    "保证金": [
        "https://seller.us.tiktokshopglobalselling.com/finance/deposit",
        "https://seller.us.tiktokshopglobalselling.com/deposit",
    ],
    "收益数据分析": [
        "https://seller.us.tiktokshopglobalselling.com/finance/revenue",
        "https://seller.us.tiktokshopglobalselling.com/analytics/revenue",
    ],
    "账单": [
        "https://seller.us.tiktokshopglobalselling.com/finance/bill",
        "https://seller.us.tiktokshopglobalselling.com/bill",
    ],
    "钱包": [
        "https://seller.us.tiktokshopglobalselling.com/finance/wallet",
        "https://seller.us.tiktokshopglobalselling.com/wallet",
    ],
}

def extract(page, wait=10):
    time.sleep(wait)
    try:
        data = page.evaluate("""() => {
            return JSON.stringify({
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 5000),
                tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item")).map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                table_headers: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean)).filter(h => h.length > 0),
                buttons: Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                inputs: Array.from(document.querySelectorAll("input")).filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                page_url: window.location.href
            });
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    all_results = {}

    for module_name, urls in URL_PATTERNS.items():
        print(f"\n### {module_name} ###")

        best_result = None
        for url in urls:
            print(f"  Trying: {url}")
            try:
                page.goto(url, timeout=40000, wait_until="domcontentloaded")
                data = extract(page, wait=12)

                # Check if page actually loaded content
                main_text = data.get('main_text', '')
                has_content = len(main_text.strip()) > 100 and '404' not in data.get('title', '')

                print(f"    Title: {data.get('title')}")
                print(f"    URL: {data.get('url')}")
                print(f"    Has content: {has_content} (chars: {len(main_text)})")
                print(f"    Tabs: {data.get('tabs', [])[:4]}")
                print(f"    Tables: {data.get('table_headers', [])}")
                print(f"    Buttons: {data.get('buttons', [])[:6]}")
                print(f"    Text preview: {main_text[:100]}")

                if has_content:
                    print(f"    *** GOT CONTENT! ***")
                    ss_name = f"direct_{module_name}_{int(time.time())}.png"
                    page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
                    print(f"    Screenshot: {ss_name}")
                    best_result = {**data, "working_url": url}
                    break
                else:
                    # Still save this result
                    ss_name = f"direct_{module_name}_404_{int(time.time())}.png"
                    page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name))

            except Exception as e:
                print(f"    ERROR: {e}")

        if best_result:
            all_results[module_name] = best_result
        else:
            all_results[module_name] = {"error": "No working URL found", "tried_urls": urls}

        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "direct_nav_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 === Saved: {out_file}")
    browser.close()
