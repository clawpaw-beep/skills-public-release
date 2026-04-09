#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from experiment_round_state import claim_next_round, record_round_result

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(r"C:\Users\9400\Documents\zhanfu_collect_runs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_STATE_FILE = OUTPUT_DIR / "experimental_round_state.json"


def run(command: list[str], timeout: int) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def main() -> None:
    parser = argparse.ArgumentParser(description="One-shot daily collection entrypoint")
    parser.add_argument("--config", required=True, help="Path to collect config JSON")
    parser.add_argument("--health-timeout", type=int, default=120)
    parser.add_argument("--collect-timeout", type=int, default=1800)
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--max-rounds", type=int, default=10)
    args = parser.parse_args()

    state_file = Path(args.state_file)
    state, round_number = claim_next_round(state_file, max_rounds=args.max_rounds)
    if round_number is None:
        payload = {
            "status": "round_limit_reached",
            "state_file": str(state_file),
            "rounds_completed": state.get("rounds_completed", 0),
            "max_rounds": state.get("max_rounds", args.max_rounds),
        }
        print(json.dumps(payload, ensure_ascii=True))
        raise SystemExit(4)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"daily_run_r{round_number:02d}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    health_cmd = [sys.executable, str(SCRIPT_DIR / "healthcheck_zhanfu.py"), "--deep"]
    health_code, health_stdout, health_stderr = run(health_cmd, timeout=args.health_timeout)
    (run_dir / "healthcheck.stdout.txt").write_text(health_stdout, encoding="utf-8")
    (run_dir / "healthcheck.stderr.txt").write_text(health_stderr, encoding="utf-8")

    try:
        health_json_line = next((line for line in health_stdout.splitlines() if line.strip().startswith("{")), "{}")
        health_report = json.loads(health_json_line)
    except Exception:
        health_report = {"ready_for_collection": False, "note": "failed to parse healthcheck output"}

    if health_code != 0 or not health_report.get("ready_for_collection", False):
        payload = {
            "status": "healthcheck_failed",
            "health_report": health_report,
            "run_dir": str(run_dir),
            "round": round_number,
            "state_file": str(state_file),
        }
        (run_dir / "daily_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        record_round_result(state_file, round_number, payload["status"], str(run_dir), {"health_report": health_report})
        print(json.dumps(payload, ensure_ascii=True))
        raise SystemExit(2)

    collect_cmd = [sys.executable, str(SCRIPT_DIR / "collect_multi_store.py"), "--config", args.config]
    collect_code, collect_stdout, collect_stderr = run(collect_cmd, timeout=args.collect_timeout)
    (run_dir / "collect.stdout.txt").write_text(collect_stdout, encoding="utf-8")
    (run_dir / "collect.stderr.txt").write_text(collect_stderr, encoding="utf-8")

    payload = {
        "status": "ok" if collect_code == 0 else "collect_failed",
        "health_report": health_report,
        "collect_returncode": collect_code,
        "run_dir": str(run_dir),
        "round": round_number,
        "state_file": str(state_file),
    }
    (run_dir / "daily_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    record_round_result(state_file, round_number, payload["status"], str(run_dir), {"collect_returncode": collect_code})
    print(json.dumps(payload, ensure_ascii=True))
    raise SystemExit(0 if collect_code == 0 else 3)


if __name__ == "__main__":
    main()
