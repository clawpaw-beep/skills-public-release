# Validated State (Public Example)

Use this file as a template for recording a target machine's validated runtime state.

## Example runtime

- Preferred runtime binary: `C:\path\to\ZhanFu\站斧.exe`
- WebDriver HTTP API: `http://127.0.0.1:45008`
- Known-good startup arguments:
  - `--multip --run_type=web_driver --ipc_type=http --httpport=45008`

## Example collection outputs

- Sales export: `C:\path\to\Documents\zhanfu_sales_<timestamp>.csv`
- FMCG review exports: `C:\path\to\Documents\fmcg_reviews_visible.csv`
- Safe order lookup: `C:\path\to\Documents\fmcg_order_lookup_safe.csv`

## Example notes

- Open stores sequentially.
- Require a real `webSocketDebuggerUrl` before Playwright extraction.
- Prefer reusing live CDP sessions over reopening the same store.
