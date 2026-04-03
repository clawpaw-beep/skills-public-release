#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zhanfu_runtime import ensure_real_webdriver, get_browser_list

OUTPUT = Path(r"C:\Users\9400\Documents\zhanfu_collect_runs\healthcheck_latest.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="ZhanFu healthcheck")
    parser.add_argument("--deep", action="store_true", help="Also verify FMCG real CDP readiness")
    args = parser.parse_args()

    report = {
        "api_reachable": False,
        "store_count": 0,
        "fmcg_present": False,
        "fmcg_ready_hint": False,
        "fmcg_cdp_ready": False,
        "ready_for_collection": False,
        "mode": "deep" if args.deep else "basic",
        "note": "",
    }
    try:
        stores = get_browser_list()
        report["api_reachable"] = True
        report["store_count"] = len(stores)
        report["fmcg_present"] = any(int(item.get("mall_id", 0)) == 2376919 for item in stores)
        report["fmcg_ready_hint"] = report["fmcg_present"]
        if args.deep and report["fmcg_present"]:
            ready, error = ensure_real_webdriver(2376919, startup_wait=60, reopen_once=True)
            report["fmcg_cdp_ready"] = bool(ready)
            if not ready:
                report["note"] = error
        report["ready_for_collection"] = report["api_reachable"] and report["fmcg_present"] and (report["fmcg_cdp_ready"] if args.deep else True)
    except Exception as exc:
        report["note"] = str(exc)

    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    print(f"OUTPUT={OUTPUT}")


if __name__ == "__main__":
    main()
