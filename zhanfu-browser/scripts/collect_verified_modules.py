#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Shop 商家后台 - 已验证模块自动化采集
支持的模块：
  1. 商品评分 (product/rating)
  2. 联盟 (affiliate/landing)
  3. 直播管理平台 (live/overview)
  4. 退货管理 (order/return)
  5. 合规看板 (compliance/dashboard)
  6. 应用商店 (appstore/gs-my)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import time
from datetime import datetime

# Import from zhanfu_runtime
from zhanfu_runtime import (
    open_browser, get_browser_webdriver, wait_for_real_webdriver
)

MALL_ID = "2376919"  # FMCG store
OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_collected_20260407"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def extract_page_data(page, wait=8):
    """Extract structured data from a page."""
    import time as t
    t.sleep(wait)
    try:
        data = page.evaluate("""() => {
            var result = {
                url: window.location.href,
                title: document.title,
                main_text: document.body.innerText.substring(0, 8000),
                tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item"))
                    .map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                table_headers: Array.from(document.querySelectorAll("table"))
                    .map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean))
                    .filter(h => h.length > 0),
                table_rows: Array.from(document.querySelectorAll("table")).map(t => {
                    return Array.from(t.querySelectorAll("tbody tr")).slice(0, 50).map(r =>
                        Array.from(r.querySelectorAll("td")).map(d => d.textContent.trim())
                    );
                }),
                buttons: Array.from(document.querySelectorAll("button"))
                    .map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                inputs: Array.from(document.querySelectorAll("input"))
                    .filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                headings: Array.from(document.querySelectorAll("h1, h2, h3, h4"))
                    .map(h => h.textContent.trim()).filter(t => t && t.length < 200),
                metrics: [],
                iframes: Array.from(document.querySelectorAll("iframe")).map(f => f.src)
            };

            // Extract metric cards (numbers with labels)
            var cards = document.querySelectorAll("[class*='metric'], [class*='card'], [class*='stat']");
            cards.forEach(function(c) {
                var text = c.textContent.trim();
                if (text && text.length < 200) result.metrics.push(text);
            });

            return JSON.stringify(result);
        }""")
        return json.loads(data)
    except Exception as e:
        return {"error": str(e)}

def collect_product_rating(page):
    """采集商品评分数据."""
    print("\n=== 采集: 商品评分 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/product/rating"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    # Extract specific fields
    result = {
        "module": "商品评分",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    # Try to extract key metrics from text
    text = data.get("main_text", "")
    lines = text.split("\n")

    # Find rating summary lines
    for i, line in enumerate(lines):
        if "总评价" in line or "差评" in line or "商责差评率" in line:
            result.setdefault("summary_lines", []).append(line.strip())

    out_file = os.path.join(OUTPUT_DIR, f"product_rating_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"product_rating_{int(time.time())}.png"), full_page=True)
    return result

def collect_affiliate(page):
    """采集联盟数据."""
    print("\n=== 采集: 联盟 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/affiliate/landing"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    result = {
        "module": "联盟",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    out_file = os.path.join(OUTPUT_DIR, f"affiliate_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"affiliate_{int(time.time())}.png"), full_page=True)
    return result

def collect_live(page):
    """采集直播管理平台数据."""
    print("\n=== 采集: 直播管理平台 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/live/overview"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    result = {
        "module": "直播管理平台",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    out_file = os.path.join(OUTPUT_DIR, f"live_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"live_{int(time.time())}.png"), full_page=True)
    return result

def collect_return_orders(page):
    """采集退货管理数据."""
    print("\n=== 采集: 退货管理 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/order/return"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    result = {
        "module": "退货管理",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    out_file = os.path.join(OUTPUT_DIR, f"order_return_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"order_return_{int(time.time())}.png"), full_page=True)
    return result

def collect_compliance(page):
    """采集合规看板数据."""
    print("\n=== 采集: 合规看板 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/compliance/dashboard"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    result = {
        "module": "合规看板",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    out_file = os.path.join(OUTPUT_DIR, f"compliance_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"compliance_{int(time.time())}.png"), full_page=True)
    return result

def collect_appstore(page):
    """采集应用商店数据."""
    print("\n=== 采集: 应用商店 ===")
    url = "https://seller.us.tiktokshopglobalselling.com/appstore/gs-my"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    data = extract_page_data(page, wait=10)

    result = {
        "module": "应用商店",
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "page": data
    }

    out_file = os.path.join(OUTPUT_DIR, f"appstore_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_file}")
    page.screenshot(path=os.path.join(OUTPUT_DIR, f"appstore_{int(time.time())}.png"), full_page=True)
    return result

def main():
    ensure_output_dir()
    print(f"=== TikTok Shop 已验证模块自动化采集 ===")
    print(f"Store: {MALL_ID}")
    print(f"Output: {OUTPUT_DIR}")

    # Open browser and get CDP
    print("\nOpening FMCG store...")
    open_result = open_browser(MALL_ID)
    print(f"Open result: {open_result}")

    ready, error = wait_for_real_webdriver(MALL_ID, timeout_seconds=60)
    if not ready:
        print(f"ERROR: {error}")
        return

    print(f"WebDriver ready: {ready.ws_endpoint}")

    # Import playwright here (heavy)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ready.ws_endpoint, timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0]

        results = {}

        # Collect all modules
        try:
            results["商品评分"] = collect_product_rating(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["商品评分"] = {"error": str(e)}

        try:
            results["联盟"] = collect_affiliate(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["联盟"] = {"error": str(e)}

        try:
            results["直播管理平台"] = collect_live(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["直播管理平台"] = {"error": str(e)}

        try:
            results["退货管理"] = collect_return_orders(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["退货管理"] = {"error": str(e)}

        try:
            results["合规看板"] = collect_compliance(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["合规看板"] = {"error": str(e)}

        try:
            results["应用商店"] = collect_appstore(page)
        except Exception as e:
            print(f"  Error: {e}")
            results["应用商店"] = {"error": str(e)}

        browser.close()

    # Save combined summary
    summary_file = os.path.join(OUTPUT_DIR, f"combined_summary_{int(time.time())}.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 ===")
    print(f"Summary: {summary_file}")
    print(f"Collected modules: {[k for k, v in results.items() if 'error' not in v]}")

if __name__ == "__main__":
    main()
