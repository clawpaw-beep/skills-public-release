#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> None:
    sample = SCRIPT_DIR / "local_config.sample.json"
    target = SCRIPT_DIR / "local_config.json"

    payload = {
        "created": False,
        "local_config": str(target),
        "note": "",
    }

    if not sample.exists():
        payload["note"] = "local_config.sample.json not found"
        print(json.dumps(payload, ensure_ascii=True))
        raise SystemExit(1)

    if not target.exists():
        shutil.copyfile(sample, target)
        payload["created"] = True
        payload["note"] = "local_config.json created from sample; edit it for this machine"
    else:
        payload["note"] = "local_config.json already exists"

    print(json.dumps(payload, ensure_ascii=True))


if __name__ == "__main__":
    main()
