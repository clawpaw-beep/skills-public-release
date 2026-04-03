---
name: zhanfu-browser
description: Use when working with 站斧/ZhanFu WebDriver automation on a Windows machine, especially for starting or diagnosing the local 5.x WebDriver HTTP service, resolving mall_id values, opening stores, waiting for a real CDP endpoint, and extracting safe sales or order-mapping data from already logged-in stores.
---

# zhanfu-browser

Use this skill for a validated ZhanFu setup on a Windows machine.

## Preferred runtime

- Prefer a validated local ZhanFu runtime binary recorded in `references/validated-state.md`.
- Fall back to another installed ZhanFu copy only if the preferred runtime is unavailable.
- Start ZhanFu in WebDriver HTTP mode with:
  - `--multip --run_type=web_driver --ipc_type=http --httpport=45008`
- Talk to the local HTTP API at `http://127.0.0.1:45008` unless the target machine documents a different port.
- Read `references/validated-state.md` before changing startup behavior or debugging drift.
- Read `references/store-map.md` when the user names a store and needs its `mall_id`.

## Working rules

- Open stores sequentially.
- After `OpenBrowser`, do not trust the success response alone.
- Poll `GetBrowserWebDriver`, then verify `http://127.0.0.1:<port>/json/version` returns a real `webSocketDebuggerUrl`.
- Do not close stores immediately after obtaining the port.
- Prefer reusing a live CDP session over reopening the same store.
- Keep exports in the validated documents/output directory for the current machine unless the user asks for another path.
- Never expose buyer phone numbers, street addresses, or emails in exports or casual queries. After-sales service scenarios are exception — the business justification must be stated.

## Standard HTTP actions

Send POST JSON to `http://127.0.0.1:45008` with `"module": "WebDriverModule"`.

- `GetBrowserList`
- `OpenBrowser`
- `GetBrowserWebDriver`
- `CloseBrowser`
- `ExitClient`

Use `browserId = mall_id`.

## Preferred workflow

1. For scheduled runs, first execute `scripts/healthcheck_zhanfu.py --deep`.
2. For cron/daily automation, prefer `scripts/run_daily_collect.py --config <config.json>` as the single entrypoint.
3. For manual multi-store collection, prefer `scripts/collect_multi_store.py` instead of manually sweeping every store in one raw script run.
4. For FMCG or unstable runs, execute `scripts/fmcg_single_store_diagnose.py` when you need a store-specific diagnosis.
5. Require `/json/version` to expose a real `webSocketDebuggerUrl` before any Playwright step.
6. Keep the store open if follow-up scraping or CDP refresh is likely.
7. Export results and report the exact output paths.

## Bundled scripts

- `scripts/zhanfu_runtime.py`
  - Shared runtime helpers for WebDriver HTTP API, real-CDP verification, reopen-once recovery, and connection diagnostics.
- `scripts/zhanfu_sales_export.py`
  - Use for sales extraction.
  - Prefer `--mall-id <id>` or `--limit <n>` for small stable batches; avoid large all-store runs unless needed.
  - Writes incremental timestamped CSV and JSON exports to the validated documents/output directory after each store, so partial progress survives failures.
- `scripts/fmcg_single_store_diagnose.py`
  - Use before FMCG scraping when stability is in doubt.
  - Verifies the configured FMCG store exists, can open, and exposes a real CDP endpoint.
  - Writes a diagnose JSON report under the validated documents/output directory.
- `scripts/fmcg_order_lookup_by_order_id.py`
  - Use for safe FMCG order lookup from a review-followup CSV.
  - Keep only safe fields such as usernames, order IDs, status, amounts, timestamps, product info, and detail URLs.
  - Now uses shared real-CDP runtime verification and incremental output flushes.
  - Run only after FMCG single-store diagnosis or real-CDP verification succeeds.
- `scripts/collect_multi_store.py`
  - Use as the stable multi-store controller.
  - Runs per-batch sales collection with isolated subprocesses and live summary JSON output.
  - Can also run FMCG diagnosis and FMCG safe order lookup as part of the same orchestrated run.
  - Supports `--config <path>` and `--retry-config <path>`.
  - Writes run artifacts under the validated run-output directory and updates `runs_index.json` for recent run history.
- `scripts/run_daily_collect.py`
  - Use as the single cron-ready entrypoint.
  - Runs deep healthcheck first, aborts early when not ready, then runs the orchestrator with one config file.
  - Produces a dedicated `daily_run_*` folder with stdout/stderr captures and `daily_summary.json`.
- `scripts/healthcheck_zhanfu.py`
  - Use for health checks before scheduled runs.
  - Supports `--deep` to verify FMCG real-CDP readiness before starting collection.
- `scripts/get_buyer_phone.py`
  - Fetches buyer contact info (phone, username, address) from a TikTok Shop order detail page via ZhanFu CDP.
  - Usage: `python scripts/get_buyer_phone.py <order_no> [cdp_url]`
  - If `cdp_url` is omitted, auto-detects from the configured FMCG store via ZhanFu HTTP API.
  - Returns: order_no, buyer_username, buyer_phone, buyer_address.
  - Use only for after-sales service with stated business justification.

## Common failure recovery

- If `45008` is down, start ZhanFu in WebDriver mode and retry.
- If the fallback runtime fails with a path/permission issue during ChromeDriver initialization, switch back to the preferred validated runtime before retrying.
- If `GetBrowserWebDriver` returns a port but `/json/version` fails, do not proceed; require a real `webSocketDebuggerUrl`.
- Prefer diagnosing FMCG first with `scripts/fmcg_single_store_diagnose.py` before running FMCG order-lookup exports.
- For sales export, prefer small batches (`--mall-id` or `--limit`) over full-store sweeps.
- If many stores are being processed, avoid opening all of them at once.
- If results look stale, refresh through the live CDP page before reopening the store.
- If OpenClaw automation itself fails because the local node is missing or disconnected, read `references/openclaw-notes.md`.

## References

- `references/validated-state.md` (machine-specific validated runtime notes; keep public-safe if publishing)
- `references/validated-state.public-example.md` (public-safe example)
- `references/store-map.md` (machine-specific store map; keep public-safe if publishing)
- `references/store-map.public-example.md` (public-safe example)
- `references/openclaw-notes.md`
- `references/daily-automation.md`
- `references/collector-spec.md`
- `references/migration.md`

## Extending with new collection tasks

When adding a new task, do not clone-and-hack an old script blindly.
Use `scripts/collector_template.py` as the starting point and follow `references/collector-spec.md`.
Reuse the shared runtime, incremental flushing, progress JSON lines, and orchestrator integration patterns.

## Migration helpers

- `scripts/local_config.sample.json` - public-safe starting template for another machine
- `scripts/bootstrap_zhanfu_skill.py` - create `local_config.json` from sample
- `scripts/self_test_zhanfu_skill.py` - validate required config keys before running on a new machine

## Public repo note

Before uploading publicly, prefer the public example references over private/local notes, and do not commit `local_config.json`, run outputs, or environment-specific exports.
