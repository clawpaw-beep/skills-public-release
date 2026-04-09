#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from zhanfu_runtime import (
    connect_browser,
    ensure_zhanfu_ready,
    snapshot_tabs_dict,
    pick_best_tab,
    tab_body_text,
    tab_url,
    tab_title,
    classify_page,
    goto_seller_home_if_needed,
)

CHECKPOINTS = [5, 10, 15, 20, 30, 45, 60]


def evaluate_best(browser):
    tab, score = pick_best_tab(browser)
    if tab is None:
        return {
            "score": -999,
            "page_kind": "none",
            "url": "",
            "title": "",
            "body_length": 0,
            "dashboard_ready": False,
        }
    body = tab_body_text(tab)
    return {
        "score": score,
        "page_kind": classify_page(tab_url(tab), tab_title(tab), body),
        "url": tab_url(tab),
        "title": tab_title(tab),
        "body_length": len(body),
        "dashboard_ready": ("经营数据" in body) or ("GMV" in body and "订单数" in body),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="测量站斧店铺页面拉起耗时")
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--output", help="输出 JSON 路径")
    parser.add_argument("--goto-home", action="store_true", help="连接后主动跳 seller 首页")
    args = parser.parse_args()

    ensure = ensure_zhanfu_ready(args.store_id, startup_wait=60, cdp_wait=120, kill_first=False)
    payload: dict[str, object] = {
        "store_id": args.store_id,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "webdriver_ready": bool(ensure.ready),
        "webdriver_error": ensure.error,
        "checkpoints": [],
    }

    if not ensure.ready:
        payload["status"] = "webdriver_unavailable"
    else:
        browser = connect_browser(ensure.ready.port)
        started = time.time()
        try:
            if args.goto_home:
                payload["goto_home"] = goto_seller_home_if_needed(browser, wait_seconds=10)
            for seconds in CHECKPOINTS:
                remain = seconds - (time.time() - started)
                if remain > 0:
                    time.sleep(remain)
                best = evaluate_best(browser)
                payload["checkpoints"].append({
                    "elapsed": seconds,
                    "best": best,
                    "tabs": snapshot_tabs_dict(browser, excerpt_lines=8),
                })
            payload["status"] = "ok"
            payload["cdp_port"] = ensure.ready.port
            payload["ws_endpoint"] = ensure.ready.ws_endpoint
        finally:
            try:
                browser.quit()
            except Exception:
                pass

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
