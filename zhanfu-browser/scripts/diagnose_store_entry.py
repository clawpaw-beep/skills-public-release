#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from zhanfu_runtime import connect_browser, diagnose_store_entry, ensure_zhanfu_ready, get_browser_list


def main() -> None:
    parser = argparse.ArgumentParser(description="诊断站斧店铺入口状态")
    parser.add_argument("--store-id", type=int, required=True, help="站斧 mall_id")
    parser.add_argument("--output", help="输出 JSON 路径")
    args = parser.parse_args()

    stores = get_browser_list()
    store = next((s for s in stores if int(s.get("mall_id", 0)) == int(args.store_id)), None)
    if not store:
        raise SystemExit(f"store_id {args.store_id} 不在 GetBrowserList 里")

    ensure = ensure_zhanfu_ready(args.store_id, startup_wait=60, cdp_wait=90, kill_first=False)
    payload: dict[str, object] = {
        "store_id": args.store_id,
        "store_name": store.get("mall_name") or store.get("shop_name") or "",
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "webdriver_ready": bool(ensure.ready),
        "webdriver_error": ensure.error,
    }

    if not ensure.ready:
        payload["status"] = "webdriver_unavailable"
    else:
        browser = connect_browser(ensure.ready.port)
        try:
            payload["status"] = "ok"
            payload["cdp_port"] = ensure.ready.port
            payload["ws_endpoint"] = ensure.ready.ws_endpoint
            payload["diagnosis"] = diagnose_store_entry(browser, try_open_store=True, try_goto_home=True)
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
