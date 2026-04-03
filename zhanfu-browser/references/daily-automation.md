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
3. Re-run with the generated `retry_config.json` if appropriate
