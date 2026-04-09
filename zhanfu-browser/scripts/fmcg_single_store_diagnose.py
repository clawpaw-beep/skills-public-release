#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import time
from pathlib import Path

from zhanfu_runtime import ensure_real_webdriver_detailed, get_browser_list, open_browser

OUTPUT = Path(r"C:\Users\9400\Documents\fmcg_store_diagnose.json")
FMCG_ID = 2376919


def main() -> None:
    payload: dict[str, object] = {
        "mall_id": FMCG_ID,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "browser_present": False,
        "open_ret": None,
        "webdriver_ready": False,
        "port": None,
        "ws_endpoint": "",
        "note": "",
        "webdriver_detail": None,
    }

    stores = get_browser_list()
    store = next((s for s in stores if int(s.get("mall_id", 0)) == FMCG_ID), None)
    payload["browser_present"] = bool(store)
    if not store:
        payload["note"] = "FMCG store not found in GetBrowserList"
    else:
        open_result = open_browser(FMCG_ID)
        payload["open_ret"] = open_result.get("ret")
        ensure = ensure_real_webdriver_detailed(FMCG_ID, startup_wait=90, reopen_once=True, reuse_existing_first=True)
        payload["webdriver_detail"] = {
            "error": ensure.error,
            "used_reopen": ensure.used_reopen,
            "reused_existing": ensure.reused_existing,
            "attempts": [
                {
                    "attempt": item.attempt,
                    "phase": item.phase,
                    "ok": item.ok,
                    "port": item.port,
                    "ws_endpoint": item.ws_endpoint,
                    "error": item.error,
                    "waited_seconds": item.waited_seconds,
                    "version_checks": item.version_checks,
                    "reused_existing": item.reused_existing,
                    "reopened_browser": item.reopened_browser,
                    "open_response_ret": item.open_response_ret,
                    "close_response_ret": item.close_response_ret,
                    "version_payload": item.version_payload,
                }
                for item in ensure.attempts
            ],
        }
        if ensure.ready:
            payload["webdriver_ready"] = True
            payload["port"] = ensure.ready.port
            payload["ws_endpoint"] = ensure.ready.ws_endpoint
        else:
            payload["note"] = ensure.error

    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    print(f"OUTPUT={OUTPUT}")


if __name__ == "__main__":
    main()
