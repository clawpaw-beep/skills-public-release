#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from collect_report import classify_error, normalize_status, summarize_run
from zhanfu_runtime import get_browser_list

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(r"C:\Users\9400\Documents\zhanfu_collect_runs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_STORES = [2779003, 2515382, 2376919, 2353141, 2346095, 2337386, 2280875, 2276389, 2276096, 2273435, 2272896, 2264045, 2250317, 2210139, 1967657]
TARGET_STORE_COUNT = 16
TERMINAL_FAILURES = {"login_required", "verification_required"}
RETRYABLE_FAILURES = {"webdriver_unavailable", "connection_error", "timeout", "missing", "error", "empty"}


def run_subprocess(
    command: list[str],
    timeout: int,
    on_stdout_line=None,
    on_stderr_line=None,
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def _reader(pipe, collector: list[str], callback) -> None:
        if pipe is None:
            return
        try:
            for line in iter(pipe.readline, ""):
                collector.append(line)
                if callback is not None:
                    callback(line.rstrip("\r\n"))
        finally:
            pipe.close()

    stdout_thread = threading.Thread(target=_reader, args=(process.stdout, stdout_lines, on_stdout_line), daemon=True)
    stderr_thread = threading.Thread(target=_reader, args=(process.stderr, stderr_lines, on_stderr_line), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        returncode = 124
        process.wait(timeout=5)

    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)

    stdout = "".join(stdout_lines)
    stderr = "".join(stderr_lines)
    if timed_out:
        stderr = f"{stderr}\nTIMEOUT: command exceeded {timeout} seconds".strip()
    return returncode, stdout, stderr


def parse_store_ids(raw: str | None) -> list[int]:
    if not raw:
        return DEFAULT_STORES
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_progress(log_path: Path, event: dict) -> None:
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def child_progress_callback(log_path: Path, summary_path: Path, summary: dict, event_name: str):
    def _callback(line: str) -> None:
        line = (line or "").strip()
        if not line:
            return
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return
        progress = payload.get("progress")
        if not isinstance(progress, dict):
            return
        event = {
            "event": event_name,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        event.update(progress)
        append_progress(log_path, event)
        summary[f"{event_name}_latest"] = progress
        save_json(summary_path, summary)

    return _callback


def read_store_result(run_dir: Path, store_id: int) -> dict:
    path = run_dir / f"sales_store_{store_id}" / f"sales_store_{store_id}.json"
    if not path.exists():
        return {"store_id": store_id, "status": "missing", "note": "result file missing"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data[0]
    except Exception as exc:
        return {"store_id": store_id, "status": "error", "note": f"read result failed: {exc}"}
    return {"store_id": store_id, "status": "empty", "note": "empty result"}


def choose_stores(requested: list[int], available_map: dict[int, dict], target_count: int = TARGET_STORE_COUNT) -> list[int]:
    chosen: list[int] = []
    seen: set[int] = set()
    for store_id in requested:
        if store_id in available_map and store_id not in seen:
            chosen.append(store_id)
            seen.add(store_id)
        if len(chosen) >= target_count:
            return chosen
    for store_id in sorted(available_map.keys(), reverse=True):
        if store_id not in seen:
            chosen.append(store_id)
            seen.add(store_id)
        if len(chosen) >= target_count:
            break
    return chosen


def build_sales_table_rows(run_dir: Path, stores: list[int], available_map: dict[int, dict]) -> list[dict]:
    rows = []
    for store_id in stores:
        item = read_store_result(run_dir, store_id)
        status = normalize_status(item.get("final_failure_type") or item.get("status"), note=item.get("note", ""))
        meta = available_map.get(store_id, {})
        rows.append(
            {
                "store_id": store_id,
                "store_name": item.get("store_name") or meta.get("mall_name", ""),
                "status": status,
                "gmv": item.get("gmv", ""),
                "orders": item.get("orders", ""),
                "gmv_change": item.get("gmv_change", ""),
                "attempt_count": item.get("attempt_count", len(item.get("attempts", []) or [])),
                "reason": item.get("note", "") or item.get("raw_text_excerpt", "")[:120],
            }
        )
    return rows


def write_sales_report_md(run_dir: Path, rows: list[dict]) -> Path:
    md_path = run_dir / "sales_report.md"
    lines = [
        "# 店铺销售额日报",
        "",
        "| 店铺ID | 店铺名 | 状态 | GMV | 订单数 | GMV变化 | 抓取尝试次数 | 备注/失败原因 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['store_id']} | {(row['store_name'] or '-').replace('|', '/')} | {row['status']} | {row['gmv'] or '-'} | {row['orders'] or '-'} | {row['gmv_change'] or '-'} | {row['attempt_count'] or '-'} | {(row['reason'] or '-').replace('|', '/')} |"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def build_sales_command(script_path: Path, store_id: int, output_dir: Path, max_attempts_per_store: int, keep_open_on_success: bool) -> list[str]:
    cmd = [
        sys.executable,
        str(script_path),
        "--store-id",
        str(store_id),
        "--output-dir",
        str(output_dir),
        "--flush-every",
        "1",
        "--max-attempts",
        str(max_attempts_per_store),
    ]
    if keep_open_on_success:
        cmd.append("--keep-open-on-success")
    return cmd


def collect_store_once(
    run_dir: Path,
    store_id: int,
    timeout_sales: int,
    max_attempts_per_store: int,
    keep_open_on_success: bool,
) -> tuple[dict, dict]:
    cmd = build_sales_command(
        SCRIPT_DIR / "collector_sales.py",
        store_id,
        run_dir / f"sales_store_{store_id}",
        max_attempts_per_store,
        keep_open_on_success,
    )
    code, stdout, stderr = run_subprocess(cmd, timeout=timeout_sales)
    result_row = read_store_result(run_dir, store_id)
    failure_type = normalize_status(
        result_row.get("final_failure_type") or result_row.get("status") or (None if code == 0 else classify_error(stdout, stderr)),
        note=result_row.get("note", ""),
        stdout=stdout,
        stderr=stderr,
    )
    payload = {
        "batch": [store_id],
        "store_id": store_id,
        "command": cmd,
        "returncode": code,
        "stdout": stdout,
        "stderr": stderr,
        "error_type": None if code == 0 and normalize_status(result_row.get("status"), note=result_row.get("note", "")) == "ok" else failure_type,
        "store_result": result_row,
    }
    return payload, result_row


def should_retry_store(store_result: dict, retry_terminal_failures: bool = False) -> bool:
    status = normalize_status(store_result.get("final_failure_type") or store_result.get("status"), note=store_result.get("note", ""))
    if status == "ok":
        return False
    if status in TERMINAL_FAILURES and not retry_terminal_failures:
        return False
    return status in RETRYABLE_FAILURES or retry_terminal_failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Stable multi-store collector for ZhanFu sales + FMCG diagnostics")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--retry-config", help="Path to retry_config.json generated by a previous run")
    parser.add_argument("--stores", help="Comma-separated mall_id list. Default is curated stable order.")
    parser.add_argument("--sales-limit", type=int, default=1, help="How many stores to include in each sales batch")
    parser.add_argument("--skip-sales", action="store_true")
    parser.add_argument("--skip-fmcg-diagnose", action="store_true")
    parser.add_argument("--run-fmcg-order-lookup", action="store_true")
    parser.add_argument("--timeout-sales", type=int, default=240)
    parser.add_argument("--timeout-diagnose", type=int, default=180)
    parser.add_argument("--timeout-fmcg-order-lookup", type=int, default=300)
    parser.add_argument("--retry-failed-sales-batches", action="store_true")
    parser.add_argument("--retry-failed-batches-once", action="store_true")
    parser.add_argument("--sleep-between-batches-seconds", type=int, default=3)
    parser.add_argument("--max-attempts-per-store", type=int, default=3)
    parser.add_argument("--keep-open-on-success", action="store_true")
    parser.add_argument("--retry-terminal-failures", action="store_true")
    args = parser.parse_args()

    config = {}
    if args.retry_config:
        config = json.loads(Path(args.retry_config).read_text(encoding="utf-8"))
    elif args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    requested_stores = parse_store_ids(args.stores) if args.stores else config.get("stores") or DEFAULT_STORES
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    available = {int(item.get("mall_id", 0)): item for item in get_browser_list()}
    stores = choose_stores(requested_stores, available, target_count=int(config.get("target_store_count", TARGET_STORE_COUNT)))
    skip_sales = args.skip_sales or bool(config.get("skip_sales", False))
    skip_fmcg_diagnose = args.skip_fmcg_diagnose or bool(config.get("skip_fmcg_diagnose", False))
    run_fmcg_order_lookup = args.run_fmcg_order_lookup or bool(config.get("run_fmcg_order_lookup", False))
    sales_limit = args.sales_limit if "--sales-limit" in sys.argv[1:] else int(config.get("sales_limit", 1))
    timeout_sales = args.timeout_sales if "--timeout-sales" in sys.argv[1:] else int(config.get("timeout_sales", 240))
    timeout_diagnose = args.timeout_diagnose if "--timeout-diagnose" in sys.argv[1:] else int(config.get("timeout_diagnose", 180))
    timeout_fmcg_order_lookup = args.timeout_fmcg_order_lookup if "--timeout-fmcg-order-lookup" in sys.argv[1:] else int(config.get("timeout_fmcg_order_lookup", 300))
    retry_failed_sales_batches = args.retry_failed_sales_batches or bool(config.get("retry_failed_sales_batches", False))
    retry_failed_batches_once = args.retry_failed_batches_once or bool(config.get("retry_failed_batches_once", False))
    sleep_between_batches_seconds = args.sleep_between_batches_seconds if "--sleep-between-batches-seconds" in sys.argv[1:] else int(config.get("sleep_between_batches_seconds", 3))
    max_attempts_per_store = args.max_attempts_per_store if "--max-attempts-per-store" in sys.argv[1:] else int(config.get("max_attempts_per_store", 3))
    keep_open_on_success = args.keep_open_on_success or bool(config.get("keep_open_on_success", False))
    retry_terminal_failures = args.retry_terminal_failures or bool(config.get("retry_terminal_failures", False))

    progress_log = run_dir / "progress.jsonl"

    summary = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "config": {
            "stores": stores,
            "requested_stores": requested_stores,
            "sales_limit": sales_limit,
            "skip_sales": skip_sales,
            "skip_fmcg_diagnose": skip_fmcg_diagnose,
            "run_fmcg_order_lookup": run_fmcg_order_lookup,
            "timeout_sales": timeout_sales,
            "timeout_diagnose": timeout_diagnose,
            "timeout_fmcg_order_lookup": timeout_fmcg_order_lookup,
            "retry_failed_sales_batches": retry_failed_sales_batches,
            "retry_failed_batches_once": retry_failed_batches_once,
            "sleep_between_batches_seconds": sleep_between_batches_seconds,
            "max_attempts_per_store": max_attempts_per_store,
            "keep_open_on_success": keep_open_on_success,
            "retry_terminal_failures": retry_terminal_failures,
        },
        "stores_requested": requested_stores,
        "stores_selected": stores,
        "stores_available": sorted([store_id for store_id in stores if store_id in available]),
        "sales_batches": [],
        "store_runs": {},
        "fmcg_diagnose": None,
        "fmcg_order_lookup": None,
        "fmcg_order_lookup_progress_latest": None,
        "fmcg_order_lookup_retry": None,
        "sales_retry_batches": [],
        "human_summary": {},
    }
    save_json(run_dir / "summary.json", summary)
    append_progress(progress_log, {"event": "run_started", "stores_requested": requested_stores, "stores_selected": stores, "ts": datetime.now().isoformat(timespec="seconds")})

    if not skip_fmcg_diagnose and 2376919 in stores:
        cmd = [sys.executable, str(SCRIPT_DIR / "fmcg_single_store_diagnose.py")]
        code, stdout, stderr = run_subprocess(cmd, timeout=timeout_diagnose)
        payload = {
            "command": cmd,
            "returncode": code,
            "stdout": stdout,
            "stderr": stderr,
            "error_type": None if code == 0 else classify_error(stdout, stderr),
        }
        summary["fmcg_diagnose"] = payload
        append_progress(progress_log, {"event": "fmcg_diagnose", "returncode": code, "error_type": payload.get("error_type"), "ts": datetime.now().isoformat(timespec="seconds")})
        save_json(run_dir / "fmcg_diagnose.json", payload)
        save_json(run_dir / "summary.json", summary)

    if run_fmcg_order_lookup:
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "collector_fmcg_orders.py"),
            "--input-csv",
            str(Path(r"C:\Users\9400\Documents\fmcg_negative_review_followup.csv")),
            "--output-dir",
            str(run_dir / "fmcg_orders"),
            "--flush-every",
            "1",
        ]
        append_progress(progress_log, {"event": "fmcg_order_lookup_started", "ts": datetime.now().isoformat(timespec="seconds")})
        summary["fmcg_order_lookup_progress_latest"] = {"current": 0, "status": "started"}
        save_json(run_dir / "summary.json", summary)
        code, stdout, stderr = run_subprocess(
            cmd,
            timeout=timeout_fmcg_order_lookup,
            on_stdout_line=child_progress_callback(
                progress_log,
                run_dir / "summary.json",
                summary,
                "fmcg_order_lookup_progress",
            ),
        )
        payload = {
            "command": cmd,
            "returncode": code,
            "stdout": stdout,
            "stderr": stderr,
            "error_type": None if code == 0 else classify_error(stdout, stderr),
        }
        summary["fmcg_order_lookup"] = payload
        append_progress(progress_log, {"event": "fmcg_order_lookup", "returncode": code, "error_type": payload.get("error_type"), "ts": datetime.now().isoformat(timespec="seconds")})
        save_json(run_dir / "fmcg_order_lookup.json", payload)
        save_json(run_dir / "summary.json", summary)

    if not skip_sales:
        batch_size = max(1, sales_limit)
        for i in range(0, len(stores), batch_size):
            batch = stores[i : i + batch_size]
            append_progress(progress_log, {"event": "sales_batch_started", "batch": batch, "batch_index": i // batch_size + 1, "ts": datetime.now().isoformat(timespec="seconds")})
            batch_payload = {"batch": batch, "stores": [], "returncode": 0, "error_type": None}

            for store_id in batch:
                store_payload, store_result = collect_store_once(
                    run_dir=run_dir,
                    store_id=store_id,
                    timeout_sales=timeout_sales,
                    max_attempts_per_store=max_attempts_per_store,
                    keep_open_on_success=keep_open_on_success,
                )
                batch_payload["stores"].append(store_payload)
                summary["store_runs"][str(store_id)] = store_payload
                save_json(run_dir / f"store_{store_id}.json", store_payload)
                if store_payload.get("returncode") != 0 or store_result.get("status") != "ok":
                    batch_payload["returncode"] = max(batch_payload["returncode"], store_payload.get("returncode") or 1)
                    batch_payload["error_type"] = batch_payload.get("error_type") or store_payload.get("error_type")

            summary["sales_batches"].append(batch_payload)
            append_progress(progress_log, {
                "event": "sales_batch_finished",
                "batch": batch,
                "batch_index": i // batch_size + 1,
                "returncode": batch_payload.get("returncode"),
                "error_type": batch_payload.get("error_type"),
                "ts": datetime.now().isoformat(timespec="seconds"),
            })
            save_json(run_dir / f"sales_batch_{i // batch_size + 1}.json", batch_payload)
            save_json(run_dir / "summary.json", summary)
            time.sleep(sleep_between_batches_seconds)

        if retry_failed_sales_batches:
            if summary.get("fmcg_order_lookup") and summary["fmcg_order_lookup"].get("returncode") != 0:
                retry_cmd = summary["fmcg_order_lookup"]["command"]
                retry_payload = {"command": retry_cmd, "attempt": 2}
                if retry_failed_batches_once:
                    code, stdout, stderr = run_subprocess(retry_cmd, timeout=timeout_fmcg_order_lookup)
                    retry_payload.update({
                        "returncode": code,
                        "stdout": stdout,
                        "stderr": stderr,
                        "error_type": None if code == 0 else classify_error(stdout, stderr),
                    })
                summary["fmcg_order_lookup_retry"] = retry_payload
                append_progress(progress_log, {"event": "fmcg_order_lookup_retry", "returncode": retry_payload.get("returncode"), "error_type": retry_payload.get("error_type"), "ts": datetime.now().isoformat(timespec="seconds")})
                save_json(run_dir / "fmcg_order_lookup_retry.json", retry_payload)
                save_json(run_dir / "summary.json", summary)
                time.sleep(sleep_between_batches_seconds)

    failed_store_ids = []
    for store_id in stores:
        result_row = read_store_result(run_dir, store_id)
        if should_retry_store(result_row, retry_terminal_failures=retry_terminal_failures):
            failed_store_ids.append(store_id)

    auto_retry_results = []
    if failed_store_ids:
        append_progress(progress_log, {"event": "auto_retry_started", "stores": failed_store_ids, "ts": datetime.now().isoformat(timespec="seconds")})
        for store_id in failed_store_ids:
            result_row_before = read_store_result(run_dir, store_id)
            if not should_retry_store(result_row_before, retry_terminal_failures=retry_terminal_failures):
                continue
            retry_payload, _result_row_after = collect_store_once(
                run_dir=run_dir,
                store_id=store_id,
                timeout_sales=timeout_sales,
                max_attempts_per_store=max_attempts_per_store,
                keep_open_on_success=keep_open_on_success,
            )
            retry_payload["attempt"] = 2
            retry_payload["previous_status"] = result_row_before.get("status")
            auto_retry_results.append(retry_payload)
            save_json(run_dir / f"store_{store_id}_auto_retry.json", retry_payload)
            append_progress(progress_log, {"event": "auto_retry_finished", "store_id": store_id, "returncode": retry_payload.get("returncode"), "error_type": retry_payload.get("error_type"), "ts": datetime.now().isoformat(timespec="seconds")})
            time.sleep(sleep_between_batches_seconds)

    sales_report_rows = build_sales_table_rows(run_dir, stores, available)
    sales_report_md = write_sales_report_md(run_dir, sales_report_rows)
    summary["sales_table_rows"] = sales_report_rows
    summary["sales_report_md"] = str(sales_report_md)
    summary["auto_retry_results"] = auto_retry_results
    summary["finished_at"] = datetime.now().isoformat(timespec="seconds")
    summary["human_summary"] = summarize_run(summary)

    failed_store_ids = []
    for store_id in stores:
        result_row = read_store_result(run_dir, store_id)
        if should_retry_store(result_row, retry_terminal_failures=retry_terminal_failures):
            failed_store_ids.append(store_id)

    retry_config = {
        "stores": sorted(set(failed_store_ids)),
        "sales_limit": summary["config"]["sales_limit"],
        "skip_sales": False,
        "skip_fmcg_diagnose": summary["config"]["skip_fmcg_diagnose"],
        "run_fmcg_order_lookup": bool(summary.get("fmcg_order_lookup") and summary["fmcg_order_lookup"].get("returncode") != 0),
        "timeout_sales": summary["config"]["timeout_sales"],
        "timeout_diagnose": summary["config"]["timeout_diagnose"],
        "timeout_fmcg_order_lookup": summary["config"]["timeout_fmcg_order_lookup"],
        "retry_failed_sales_batches": True,
        "retry_failed_batches_once": True,
        "sleep_between_batches_seconds": summary["config"]["sleep_between_batches_seconds"],
        "max_attempts_per_store": summary["config"]["max_attempts_per_store"],
        "keep_open_on_success": summary["config"]["keep_open_on_success"],
        "retry_terminal_failures": summary["config"]["retry_terminal_failures"],
    }
    summary["retry_config_path"] = str(run_dir / "retry_config.json")
    save_json(run_dir / "retry_config.json", retry_config)
    save_json(run_dir / "summary.json", summary)
    (run_dir / "summary.txt").write_text(json.dumps(summary["human_summary"], ensure_ascii=False, indent=2), encoding="utf-8")
    append_progress(progress_log, {"event": "run_finished", "ts": datetime.now().isoformat(timespec="seconds"), "retry_config_path": str(run_dir / "retry_config.json")})
    index_path = OUTPUT_DIR / "runs_index.json"
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(index_data, list):
                index_data = []
        except Exception:
            index_data = []
    else:
        index_data = []
    index_data.append({
        "run_dir": str(run_dir),
        "started_at": summary.get("started_at"),
        "finished_at": summary.get("finished_at"),
        "stores": summary.get("stores_requested", []),
        "summary_txt": str(run_dir / "summary.txt"),
        "retry_config": str(run_dir / "retry_config.json"),
        "human_summary": summary.get("human_summary", {}),
    })
    index_data = index_data[-50:]
    index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "run_dir": str(run_dir), "runs_index": str(index_path)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
