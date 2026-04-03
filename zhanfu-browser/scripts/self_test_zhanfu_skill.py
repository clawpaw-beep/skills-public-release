#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_CONFIG = SCRIPT_DIR / "local_config.json"


def main() -> None:
    report = {
        "local_config_exists": LOCAL_CONFIG.exists(),
        "fields_present": {},
        "ready": False,
        "note": "",
    }

    required = [
        "zhanfu_api_url",
        "zhanfu_binary_path",
        "output_dir",
        "documents_dir",
        "fmcg_store_id",
        "default_store_ids",
        "default_input_csv",
    ]

    if not LOCAL_CONFIG.exists():
        report["note"] = "local_config.json missing; run bootstrap_zhanfu_skill.py first"
        print(json.dumps(report, ensure_ascii=True))
        raise SystemExit(1)

    config = json.loads(LOCAL_CONFIG.read_text(encoding="utf-8"))
    for key in required:
        report["fields_present"][key] = key in config and config.get(key) not in (None, "", [])

    report["ready"] = all(report["fields_present"].values())
    report["note"] = "ok" if report["ready"] else "fill missing values in local_config.json"
    print(json.dumps(report, ensure_ascii=True))
    raise SystemExit(0 if report["ready"] else 2)


if __name__ == "__main__":
    main()
