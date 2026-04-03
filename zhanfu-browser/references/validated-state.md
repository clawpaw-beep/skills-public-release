# Validated State (Publish-Safe Template)

Use this file to record a target machine's validated runtime state.
Keep it updated for the current machine, but remove secrets and personal identifiers before publishing.

## Runtime

- Preferred runtime binary: `C:\path\to\ZhanFu\站斧.exe`
- Optional fallback binary: `C:\Program Files\ZhanFu\站斧.exe`
- Installed version: `5.x.x`
- WebDriver HTTP API: `http://127.0.0.1:45008`
- Known-good startup arguments:
  - `--multip --run_type=web_driver --ipc_type=http --httpport=45008`

## Known drift or failure notes

- Record startup-path, permission, or ChromeDriver init problems here.
- Record how a broken session behaves on this machine.
- Record the recovery preference order.

## Proven workflow

- Open stores sequentially, not all at once.
- Keep stores open if later CDP refresh or follow-up scraping is likely.
- Do not trust `OpenBrowser` success alone.
- Wait for a real `webSocketDebuggerUrl` from `http://127.0.0.1:<port>/json/version`.
- Reuse an existing live CDP session whenever possible.

## Known-good outputs

- Sales export:
  - `C:\path\to\Documents\zhanfu_sales_<timestamp>.csv`
  - `C:\path\to\Documents\zhanfu_sales_<timestamp>.json`
- Review exports:
  - `C:\path\to\Documents\reviews_visible.csv`
  - `C:\path\to\Documents\negative_review_followup.csv`
- Safe order lookup:
  - `C:\path\to\Documents\order_lookup_safe.csv`
  - `C:\path\to\Documents\order_lookup_safe.json`

## Store-specific notes

- Primary FMCG store name: `example-store-fmcg`
- Primary FMCG `mall_id`: `1000000`
- Record any validated route hints or UI notes here.
- Do not include phone numbers, full addresses, emails, or other buyer-private data.
