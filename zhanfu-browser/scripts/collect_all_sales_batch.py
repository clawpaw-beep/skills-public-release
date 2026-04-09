#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

STORE_IDS = [2376919, 2273435, 2337386, 2210139, 2264045, 2779003]
SCRIPT = Path(r"C:\Users\9400\.openclaw\workspace\skills\zhanfu-browser\scripts\collector_sales.py")
OUTPUT_ROOT = Path(r"C:\Users\9400\Documents\zhanfu_sales_all_stores_20260409")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary: list[dict[str, object]] = []

    for idx, store_id in enumerate(STORE_IDS, start=1):
        store_dir = OUTPUT_ROOT / str(store_id)
        store_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--store-id",
            str(store_id),
            "--output-dir",
            str(store_dir),
        ]
        started = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        elapsed = round(time.time() - started, 1)
        summary.append(
            {
                "store_id": store_id,
                "index": idx,
                "returncode": proc.returncode,
                "elapsed_seconds": elapsed,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
        )
        print(json.dumps({"progress": {"current": idx, "total": len(STORE_IDS), "item_id": store_id, "returncode": proc.returncode, "elapsed_seconds": elapsed}}, ensure_ascii=False))

    summary_path = OUTPUT_ROOT / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": str(summary_path), "output_root": str(OUTPUT_ROOT)}, ensure_ascii=True))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
