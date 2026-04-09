# Daily Automation

## Goal
Run ZhanFu collection safely as a daily scheduled task with one command.

## Recommended entrypoint

```powershell
python C:\Users\9400\.openclaw\workspace\skills\zhanfu-browser\scripts\run_daily_collect.py --config C:\path\to\collect_config.json
```

## What it does

1. Runs deep healthcheck first.
2. Aborts early with exit code `2` when healthcheck says the environment is not ready.
3. Runs `collect_multi_store.py` with the provided config.
4. Returns exit code `3` when collection itself fails.
5. Returns exit code `0` on success.

## Stability defaults

The collector now treats **single-store isolation** as the default stability path:

- Reuse an existing live CDP session first when possible.
- Require repeated `/json/version` success with a real `webSocketDebuggerUrl`, not just one lucky response.
- If `OpenBrowser` says success but CDP is fake/unready, it will close + reopen with cooldown/backoff and try again.
- Each store is executed independently even when a batch contains multiple stores, so one bad store does not poison the whole batch.
- Auto-retry focuses on retryable failures like `webdriver_unavailable`, `connection_error`, `extension_only`, and `no_dashboard`.
- Login / verification failures are preserved as terminal human-action states by default and will not be blindly retried.

## Output layout

Under `C:\Users\9400\Documents\zhanfu_collect_runs` it writes:

- `daily_run_<timestamp>\healthcheck.stdout.txt`
- `daily_run_<timestamp>\healthcheck.stderr.txt`
- `daily_run_<timestamp>\collect.stdout.txt`
- `daily_run_<timestamp>\collect.stderr.txt`
- `daily_run_<timestamp>\daily_summary.json`

The orchestrator itself also writes its own run directory with:
- `summary.json`
- `summary.txt`
- `retry_config.json`
- `progress.jsonl`
- `runs_index.json` (global recent-run index)

Per-store result JSON now includes richer fields such as:
- `final_failure_type`
- `keep_open_reason`
- `attempts[].ensure_real_webdriver`
- nested wait/open/reopen diagnostics for real-CDP readiness

## Config knobs

Optional config fields now supported by `collect_multi_store.py`:

- `keep_open_on_success` - keep store windows open after successful extraction for follow-up reuse
- `retry_terminal_failures` - whether to retry login/verification failures too (default false, usually should stay false)
- `max_attempts_per_store` - retries inside a single store collector run
- `sleep_between_batches_seconds` - cooldown between stores/batches

## Cron / scheduler guidance

Use only one scheduled command: `run_daily_collect.py`.
Do not schedule individual sub-scripts separately.

## Exit codes

- `0` = success
- `2` = healthcheck failed, skip collection and inspect environment
- `3` = collection run failed, inspect run summary and retry config

## Recovery workflow

When collection fails:
1. Open the latest `daily_summary.json`
2. Open the orchestrator `summary.txt`
3. Check each failed store's `sales_store_<id>.json` for `final_failure_type` and `ensure_real_webdriver` details
4. Re-run with the generated `retry_config.json` if appropriate
