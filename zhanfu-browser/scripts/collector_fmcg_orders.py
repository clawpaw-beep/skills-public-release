#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from fmcg_order_lookup_by_order_id import lookup_orders, read_review_rows, write_csv
from zhanfu_runtime import ensure_real_webdriver

FMCG_ID = 2376919


def main() -> None:
    parser = argparse.ArgumentParser(description="Standard FMCG order collector")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--ws-endpoint")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "fmcg_order_lookup_safe.csv"
    output_json = output_dir / "fmcg_order_lookup_safe.json"

    rows = read_review_rows(Path(args.input_csv))
    ws_endpoint = args.ws_endpoint
    if not ws_endpoint:
        ready, error = ensure_real_webdriver(FMCG_ID, startup_wait=90, reopen_once=True)
        if not ready:
            raise SystemExit(error or "failed to get real webdriver endpoint")
        ws_endpoint = ready.ws_endpoint

    results = lookup_orders(
        rows,
        ws_endpoint=ws_endpoint,
        flush_every=args.flush_every,
        progress=True,
        output_csv=output_csv,
        output_json=output_json,
    )
    write_csv(results, output_csv)
    output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "count": len(results), "json": str(output_json), "csv": str(output_csv)}, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
