#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"C:\Users\9400\Documents\zhanfu_sales_all_stores_20260409")
OUT_JSON = ROOT / "summary_success_only.json"
OUT_CSV = ROOT / "summary_success_only.csv"


def main() -> None:
    rows = []
    for path in sorted(ROOT.glob("*/sales_store_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data:
            continue
        item = data[0]
        if item.get("status") != "ok":
            continue
        rows.append(
            {
                "store_id": item.get("store_id", ""),
                "store_name": item.get("store_name", ""),
                "platform_name": item.get("platform_name", ""),
                "page_url": item.get("page_url", ""),
                "gmv": item.get("gmv", ""),
                "gmv_change": item.get("gmv_change", ""),
                "customers": item.get("customers", ""),
                "customers_change": item.get("customers_change", ""),
                "sku_orders": item.get("sku_orders", ""),
                "sku_orders_change": item.get("sku_orders_change", ""),
                "visitors": item.get("visitors", ""),
                "visitors_change": item.get("visitors_change", ""),
                "ip_address": item.get("ip_address", ""),
            }
        )

    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["store_id"])
        writer.writeheader()
        if rows:
            writer.writerows(rows)

    print(json.dumps({"status": "ok", "count": len(rows), "json": str(OUT_JSON), "csv": str(OUT_CSV)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
