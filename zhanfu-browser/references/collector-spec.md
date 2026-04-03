# Collector Spec

## Goal
Standardize how new ZhanFu collection tasks plug into the existing runtime, orchestrator, retry, and reporting layers.

## Collector contract

Every collector should follow this contract:

### Inputs
- `store_id` or task-specific target id
- `config` object or command-line args
- `output_dir`
- optional `ws_endpoint` if the runtime already resolved a real CDP session

### Outputs
Each collector should write:
- task result JSON
- optional CSV if tabular output is useful
- structured stdout line(s) for progress
- machine-readable final summary JSON

### Exit semantics
- `0` = success
- non-zero = failure
- stderr should include useful diagnostics
- stdout may include progress JSON lines

## Required behavior

### 1. Runtime usage
Do not implement custom raw WebDriver polling in each collector unless strictly needed.
Prefer `zhanfu_runtime.py` for:
- `OpenBrowser`
- `GetBrowserWebDriver`
- real-CDP verification
- connection error handling

### 2. Incremental persistence
Collectors should flush partial results during long runs.
Do not hold all work in memory until the end if the task can run for minutes.

### 3. Progress logging
Collectors should emit progress JSON lines in stdout, for example:

```json
{"progress":{"current":12,"total":100,"ok":11,"error":1,"item_id":"ORDER-123"}}
```

### 4. Deterministic paths
Collectors should use deterministic output file names when they are task-specific, or timestamped file names when each run should be preserved.

### 5. Safe field handling
Collectors for order/buyer workflows must avoid exposing sensitive fields unless the current task explicitly requires them for justified after-sales use.

## Recommended file layout

- `scripts/collector_<task>.py`
- `references/<task>.md` (optional task-specific notes)

Examples:
- `collector_sales.py`
- `collector_fmcg_orders.py`
- `collector_inventory.py`
- `collector_reviews.py`

Current in-repo standard collectors:
- `scripts/collector_sales.py`
- `scripts/collector_fmcg_orders.py`
- `scripts/collector_template.py`

## Suggested collector CLI pattern

```powershell
python collector_<task>.py --store-id 2376919 --output-dir C:\path\to\out
```

Optional:
- `--config <json>`
- `--ws-endpoint <url>`
- `--flush-every <n>`
- `--limit <n>`

## Integration with orchestrator

`collect_multi_store.py` should treat collectors as subprocess tasks and capture:
- `returncode`
- `stdout`
- `stderr`
- `error_type`

If the collector is store-scoped, the orchestrator should also emit a per-store result file.

## Minimal checklist for a new collector

- Uses shared runtime or explains why not
- Writes partial outputs during long runs
- Emits progress JSON lines
- Returns machine-readable final summary
- Handles reconnect/retry boundaries clearly
- Avoids leaking sensitive fields beyond the current task scope
