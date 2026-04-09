#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import json, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\9400\Documents\zhanfu_module_explore_20260407"

TARGETS = [
    "触达", "客户群", "促销活动", "店铺广告", "智能营销", "店铺页面",
    "店铺数据分析", "直播和视频数据分析", "商品卡", "商品数据分析",
    "营销数据分析", "客户数据分析", "排行榜", "售后数据分析",
    "店铺健康", "店铺体验分", "达人健康评分",
    "合规看板", "合规资质", "商品合规诊断",
    "经营洞察", "成长权益", "我的任务", "我的奖励",
    "财务概览", "保证金", "收益数据分析", "账单", "钱包"
]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:12627", timeout=30000)
    context = browser.contexts[0]
    page = context.pages[0]

    # Go to a stable page first
    page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing",
              timeout=45000, wait_until="domcontentloaded")
    time.sleep(10)
    print(f"Starting URL: {page.url}")

    # Get ALL 61 menu items with text
    all_items = page.evaluate("""() => {
        var items = document.querySelectorAll('.core-menu-item');
        var result = [];
        for (var i = 0; i < items.length; i++) {
            var el = items[i];
            result.push({i: i, text: el.innerText.trim(), cls: el.className});
        }
        return JSON.stringify(result);
    }""")
    all_items = json.loads(all_items)
    print(f"Total menu items: {len(all_items)}")

    # Show items with text
    with_text = [it for it in all_items if it['text']]
    print(f"Items with text: {len(with_text)}")
    for it in with_text:
        print(f"  [{it['i']}] '{it['text']}'")

    # Build text -> index mapping
    text_map = {}
    for it in all_items:
        t = it['text']
        if t:
            text_map[t] = it['i']

    # Also add partial matches
    for target in TARGETS:
        for it in all_items:
            if target in it['text'] and it['text'] not in text_map:
                text_map[it['text']] = it['i']

    results = {}

    for target in TARGETS:
        print(f"\n--- {target} ---")

        idx = text_map.get(target)
        if idx is None:
            # Try partial
            for it in all_items:
                if target in it['text']:
                    idx = it['i']
                    print(f"  Partial match at [{idx}]: '{it['text']}'")
                    break

        if idx is None:
            print(f"  NOT FOUND")
            results[target] = {"error": "NOT FOUND", "clicked": target}
            continue

        print(f"  Clicking index {idx}...")

        # Click by index
        click_ok = page.evaluate(f"""() => {{
            var items = document.querySelectorAll('.core-menu-item');
            if (items[{idx}]) {{ items[{idx}].click(); return 'ok'; }}
            return 'fail';
        }}""")

        if click_ok != 'ok':
            print(f"  Click failed")
            results[target] = {"error": "Click failed", "clicked": target}
            continue

        time.sleep(12)  # Wait for SPA

        # Extract
        try:
            data = page.evaluate("""() => {
                return JSON.stringify({
                    url: window.location.href,
                    title: document.title,
                    main_text: document.body.innerText.substring(0, 4000),
                    tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab, .ant-segmented-item")).map(t => t.textContent.trim()).filter(t => t && t.length < 100),
                    table_headers: Array.from(document.querySelectorAll("table")).map(t => Array.from(t.querySelectorAll("th")).map(h => h.textContent.trim()).filter(Boolean)).filter(h => h.length > 0),
                    buttons: Array.from(document.querySelectorAll("button")).map(b => b.textContent.trim()).filter(b => b && b.length < 100),
                    inputs: Array.from(document.querySelectorAll("input")).filter(i => i.placeholder).map(i => ({type: i.type || "text", placeholder: i.placeholder})),
                    headings: Array.from(document.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim()).filter(t => t && t.length < 200)
                });
            }""")
            data = json.loads(data)
        except Exception as e:
            data = {"error": str(e)}

        data["clicked"] = target
        data["index"] = idx

        print(f"  URL: {data.get('url')}")
        print(f"  Title: {data.get('title')}")
        print(f"  Tabs: {data.get('tabs', [])[:6]}")
        print(f"  Tables: {data.get('table_headers', [])}")
        print(f"  Buttons: {data.get('buttons', [])[:8]}")
        print(f"  Headings: {data.get('headings', [])[:5]}")
        print(f"  Text: {data.get('main_text', '')[:150]}")

        ss_name = f"ad2_{target[:6]}_{int(time.time())}.png"
        page.screenshot(path=os.path.join(OUTPUT_DIR, ss_name), full_page=True)
        print(f"  Screenshot: {ss_name}")

        results[target] = data
        time.sleep(3)

    out_file = os.path.join(OUTPUT_DIR, "ad_analytics_v2.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n=== 完成 === Saved: {out_file} ({len(results)} items)")
    browser.close()
