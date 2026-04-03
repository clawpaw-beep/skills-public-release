#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zhanfu_runtime import ensure_real_webdriver


def main() -> None:
    parser = argparse.ArgumentParser(description="Template for new ZhanFu collectors")
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--ws-endpoint")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_json = output_dir / f"collector_{args.store_id}.json"

    ws_endpoint = args.ws_endpoint
    if not ws_endpoint:
        ready, error = ensure_real_webdriver(args.store_id, startup_wait=90, reopen_once=True)
        if not ready:
            raise SystemExit(error or "failed to get real webdriver endpoint")
        ws_endpoint = ready.ws_endpoint

    items = []
    total = 0
    ok = 0
    error = 0

    # TODO: replace this block with real collector logic.
    sample_item = {
        "store_id": args.store_id,
        "status": "ok",
        "ws_endpoint": ws_endpoint,
        "note": "replace collector_template.py with task-specific extraction logic",
    }
    items.append(sample_item)
    total += 1
    ok += 1
    result_json.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"progress": {"current": total, "total": total, "ok": ok, "error": error, "item_id": args.store_id}}, ensure_ascii=False))
    print(json.dumps({"status": "ok", "count": len(items), "output": str(result_json)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
