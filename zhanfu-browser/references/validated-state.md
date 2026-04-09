# Validated State

> Machine-specific validated runtime state. Populate from `bootstrap_zhanfu_skill.py` or manually.
> Keep this file updated; remove secrets before sharing.

## Runtime

- **Preferred binary**: `C:\Program Files\ZhanFu\zhanfu.exe` (192MB, 英文路径安装版)
- **Fallback binary**: `C:\Users\9400\ZhanFu_5_2_88_portable\站斧.exe` (老版本便携)
- **Version**: `5.2.9` (旧版为 `5.2.88`)
- **WebDriver HTTP API**: `http://127.0.0.1:45008` (固定端口)
- **Startup args**: `--multip --run_type=web_driver --ipc_type=http --httpport=45008`

## CDP 端口说明（新版本重要）

- **CDP 端口范围**: `12620-12640`，**每次 OpenBrowser 动态分配**，无固定值
- **发现方式**: 必须通过 `GET http://127.0.0.1:<port>/json` 遍历扫描
- **老版本固定端口**: `12631`（新版不再适用）
- **OpenBrowser 后需等待**: 5-10 秒后再扫描，否则可能找不到端口

## Startup Behavior

- On this machine, the installed binary at `C:\Program Files\ZhanFu\zhanfu.exe` is preferred (英文路径).
- The portable binary at `C:\Users\9400\ZhanFu_5_2_88_portable\站斧.exe` is the fallback.
- 使用 `find_cdp()` 函数动态发现 CDP 端口，**不要写死端口号**。

## Known Drift Notes

_Update when you encounter new failure modes on this machine._

## Verified Workflow

1. Open stores sequentially; keep open if CDP follow-up is likely.
2. After `OpenBrowser`, call `find_cdp()` to discover the dynamic CDP port.
3. **Use DrissionPage** for CDP connection — Playwright is not supported.
4. Do not rely on `OpenBrowser` success response alone; always verify with `find_cdp()`.

## Output Paths (this machine)

- Sales exports: `C:\Users\9400\Documents\zhanfu_sales_<timestamp>.csv/.json`
- Review exports: `C:\Users\9400\Documents\reviews_visible.csv`, `negative_review_followup.csv`
- Safe order lookup: `C:\Users\9400\Documents\order_lookup_safe.csv/.json`
- Daily run output: `C:\Users\9400\Documents\zhanfu_collect_runs\daily_run_<timestamp>\`

## Primary Stores

- **FMCG**: mall_id `2376919`
- **SopamiPro**: mall_id `2276096`
- **Tools**: mall_id `2273435`
- **Hardware**: mall_id `2337386`
