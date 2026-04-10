---
name: zhanfu-browser
description: Use when working with 站斧/ZhanFu WebDriver automation on a Windows machine, especially for starting or diagnosing the local 5.x WebDriver HTTP service, resolving mall_id values, opening stores, waiting for a real CDP endpoint, and extracting safe sales or order-mapping data from already logged-in stores.
---

# zhanfu-browser

Validated ZhanFu 5.x setup on Windows. Store map and runtime state are maintained in `references/`.

## Preferred runtime

- **Preferred binary**: `C:\Program Files\ZhanFu\zhanfu.exe`
- **Fallback binary**: `C:\Users\9400\ZhanFu_5_2_88_portable\zhanfu.exe`
- **Store map**: read `references/store-map.md`
- **Machine notes**: read `references/validated-state.md`

## 当前机器的实测结论

先记住这几个事实,别绕远路:

- 站斧主程序能启动,但 `45008` 的 WebDriver HTTP API **不是总能立即就绪**,脚本必须先探活,必要时自动拉起站斧并等待。
- `OpenBrowser` 成功 **不等于** 真实 CDP 已就绪;有时会返回一个端口,但端口根本没监听。
- 新版站斧的 CDP 端口是**动态分配**的,不能依赖单一固定端口,也不能只信 `GetBrowserWebDriver` 返回值,必须做真实连通校验。
- 已验证可用的最短链路是:`45008 API -> OpenBrowser -> 动态发现真实 CDP -> DrissionPage`。
- Playwright 的 CDP/WebSocket 握手在站斧环境里不稳定,**优先用 DrissionPage**,Playwright 仅用于页面层探索,不能作为默认底座。
- 如果打开 TikTok Shop 后跳到登录页,说明不是脚本坏了,是**店铺登录态失效**,必须先让用户手动登录。
- 不同店铺状态可能不同：有的店铺会卡在 WebDriver/CDP 就绪，有的店铺 CDP 能通但页面还停在扩展页或空白页，所以脚本必须区分"连接层失败"和"页面层失败"。

## ⚠️ 运行模式：GUI 模式 ≠ WebDriver API 模式

从桌面/开始菜单/快捷方式打开 ZhanFu → 普通浏览器，**不监听 45008 HTTP API**。

自动化脚本依赖的 HTTP API 必须用以下方式之一启动：

**方式一：命令行（推荐）**
```
zhanfu.exe --multip --run_type=web_driver --ipc_type=http --httpport=45008
```
**方式二：GUI 里启动临时模式**
店铺管理 → 找到目标店铺 → 更多 → **临时模式启动**

⚠️ 注意事项：
- 已用 GUI 模式运行时，再用同样参数启动会冲突，需先退出再启动
- 打开店铺后需等待内核启动完成（约 5-15 秒），`OpenBrowser` 返回成功不代表店铺页已就绪
- 如果 45008 端口不通，先确认 ZhanFu 是否以 WebDriver 模式运行

## 最小可用目标

当用户要"继续站斧自动化""采销售额""先把链路跑通"时,优先只做到这条:

1. 连上现有站斧浏览器
2. 进入 TikTok Shop 卖家后台
3. 读到经营数据页里的销售额(GMV)

先把这条跑通,再扩展评价、订单、退货等后续模块。

## Working rules

- 先复用已存在的站斧浏览器和 CDP 连接,不要一上来就重启站斧。
- 优先尝试 DrissionPage 直连现成端口,必要时再回退到 WebDriver HTTP API。
- 如果页签里只有 `chrome://newtab/` 或 `omnibox-popup`,说明浏览器是空的,不是店铺页。
- 如果页面跳到 TikTok Shop 登录页,立刻停下并让用户手动登录,不要假装还能继续采集。
- 只有在确认进入卖家后台后,才继续采销售额。
- 不要导出买家手机号、地址、邮箱等敏感信息,除非用户明确在售后场景要求。

## Standard HTTP actions

POST JSON to `http://127.0.0.1:45008` with `"module": "WebDriverModule"`.

- `GetBrowserList`
- `OpenBrowser`
- `GetBrowserWebDriver`
- `CloseBrowser`
- `ExitClient`

Use `browserId = mall_id`.

## CDP 端口动态发现(新版必须)

老版本固定端口 `12631` 可以写死;**新版本必须扫描**:

```python
import urllib.request, json, time

def find_cdp(timeout=15):
    """
    扫描 12620-12640 范围,发现第一个有 targets 的 CDP 端口。
    OpenBrowser 后等待 5-10 秒再调用此函数。
    """
    start = time.time()
    while time.time() - start < timeout:
        for port in range(12620, 12640):
            try:
                r = urllib.request.urlopen(f'http://127.0.0.1:{port}/json', timeout=2)
                targets = json.loads(r.read())
                if targets:
                    return port, targets
            except:
                pass
        time.sleep(2)
    return None, []

# 使用流程:
# 1. api('OpenBrowser', 'WebDriverModule', browserId='2376919')
# 2. time.sleep(5)  # 等待页面加载
# 3. port, targets = find_cdp()
# 4. browser = DrissionPage.Chromium(f'127.0.0.1:{port}')
```

## 推荐工作流(新版本)

```
检查 45008 是否可用
    ↓
不可用则自动拉起站斧 WebDriver 模式,并等待 API 就绪
    ↓
OpenBrowser (browserId)
    ↓
等待 5-10 秒
    ↓
优先校验 GetBrowserWebDriver 返回端口是否真实可连
    ↓
若不可连,则 find_cdp() 扫描 12620-12660 发现真实 CDP 端口
    ↓
DrissionPage.Chromium(f'127.0.0.1:{port}')
    ↓
检查当前 tabs:扩展页 / 空白页 / 登录页 / seller 页
    ↓
必要时点击"打开店铺"或主动跳转 seller 首页
    ↓
数据提取 (run_js)
```

## Preferred workflow

1. For scheduled runs, first execute `scripts/healthcheck_zhanfu.py --deep`.
2. For cron/daily automation, use `scripts/run_daily_collect.py --config <config.json>` as the single entrypoint.
3. For manual multi-store collection, use `scripts/collect_multi_store.py` instead of sweeping manually.
4. For FMCG or unstable runs, execute `scripts/fmcg_single_store_diagnose.py` before scraping.
5. Keep exports in the validated output directory; report exact paths after each run.

## Standard collectors

Use these instead of writing one-off scripts:

| Script | Purpose |
|--------|---------|
| `scripts/collector_sales.py` | **已验证正式链路**:首页销售/KPI 采集。自动打开店铺、等待 seller 页、提取首页 KPI,支持中英页面 |
| `scripts/collector_fmcg_orders.py` | FMCG order extraction |
| `scripts/collector_template.py` | Start here when adding a new collector |

## Bundled scripts

### Runtime
- `scripts/zhanfu_runtime.py` - Shared helpers: `open_browser`, `close_browser`, `find_cdp`, `get_browser_list`, `is_connection_error`

### Orchestration
- `scripts/collect_multi_store.py` - Stable multi-store controller with per-batch isolation, live summary JSON, and orchestrator integration
- `scripts/run_daily_collect.py` - Cron-ready entrypoint; runs deep healthcheck first, then the orchestrator

### Diagnosis
- `scripts/healthcheck_zhanfu.py` - Pre-run health check; `--deep` verifies FMCG real-CDP readiness
- `scripts/fmcg_single_store_diagnose.py` - Per-store FMCG diagnosis before scraping
- `scripts/diagnose_store_entry.py` - **正式入口诊断脚本**:验证扩展页 → 打开店铺 → seller 页 → business wait 链路
- `scripts/measure_store_entry_timing.py` - 测量店铺页面拉起耗时,适合判断等待时间策略
- `scripts/minimal_zhanfu_gmv.py` - 最小链路验证脚本,适合先确认单店首页 KPI 是否可读

### Safe data extraction
- `scripts/collector_sales.py` - Sales export via structured collector,当前输出首页 KPI:`gmv`, `gmv_change`, `customers`, `customers_change`, `sku_orders`, `sku_orders_change`, `visitors`, `visitors_change`
- `scripts/fmcg_order_lookup_by_order_id.py` - Safe order lookup (usernames, order IDs, status, amounts, timestamps, product info, detail URLs only)
- `scripts/get_buyer_phone.py` - Fetches buyer contact info (phone, username, address) from order detail page. Usage: `python get_buyer_phone.py <order_no> [cdp_url]`. Only for after-sales service with stated business justification.
- `scripts/verify_review_deleted.py` - Verifies if a buyer's review has been deleted. Searches all pages of the product rating page for the order_id. Returns: `deleted` (not found) / `present` (found). Usage: `python verify_review_deleted.py <order_id> <product_id>`

### Page data
- `scripts/extract_page_data.py` - Captures DOM-rendered text after JavaScript loads: `page.goto(url); time.sleep(6); body_text = page.run_js('return document.body.innerText')`
- `scripts/parse_return_text.py` - Parses 退货管理 page body text into structured order records. Input: `return_page_body_text.txt` → Output: `parsed_return_orders.json`
- `scripts/lookup_order_by_id.py` - Single-order detail via `/order/detail?order_no={id}&shop_region=US`

### Exploration / Multi-module collection
- `scripts/collect_verified_modules.py` - 批量采集已验证模块(商品评分/联盟/直播/退货/合规/应用商店);支持截图 + 结构化 DOM 提取;硬编码 FMCG store,可按需修改

### Utility
- `scripts/extract_cookies_and_test.py` - Extracts all 27 auth cookies from ZhanFu browser context; tests API endpoints
- `scripts/bootstrap_zhanfu_skill.py` - Creates `local_config.json` from `local_config.sample.json`
- `scripts/self_test_zhanfu_skill.py` - Validates required config keys before running on a new machine

## Common failure recovery

- If port `45008` is down, start ZhanFu in WebDriver mode and wait for API readiness before calling `GetBrowserList`.
- If `GetBrowserWebDriver` returns a port but that port is not accepting TCP, treat it as a **fake-ready** state and fall back to `find_cdp()` scanning plus retry.
- If CDP is ready but no seller page is found, classify it as a **page-layer** problem, not a runtime problem. Capture all tab URLs/titles/body excerpts, then try clicking `打开店铺` or navigating to seller home.
- If the page lands on TikTok login, stop and ask the user to manually restore login state.
- If the page shows verification hints **but KPI text is already visible**, do not fail immediately; treat it as readable and continue extraction.
- For homepage KPI parsing, do not assume one fixed language. Current collector supports both Chinese and English KPI labels.
- **Playwright is not supported as the default runtime** - use DrissionPage for CDP connections; Playwright only for targeted exploration when necessary.
- Prefer diagnosing one stable non-FMCG store first when testing a new chain, then return to FMCG after the runtime is proven.
- For sales export, prefer small batches (`--mall-id` or `--limit`) over full-store sweeps.
- If OpenClaw automation fails because the local node is missing/disconnected, read `references/openclaw-notes.md`.

## References

- `references/validated-state.md` - Machine-specific runtime notes
- `references/store-map.md` - Store name → `mall_id` mapping
- `references/openclaw-notes.md` - OpenClaw gateway/node state and boundary rules
- `references/daily-automation.md` - Cron/scheduler guidance, exit codes, output layout
- `references/collector-spec.md` - Collector contract (inputs, outputs, incremental persistence, progress logging)
- `references/tiktok-shop-module-map.md` - TikTok Shop后台页面链路树、URL路由、iframe架构、自动化入口建议

## Extending with new collection tasks

Do not clone an old script blindly. Use `scripts/collector_template.py` as the starting point and follow `references/collector-spec.md`. Reuse the shared runtime, incremental flushing, progress JSON lines, and orchestrator integration patterns.

## Migration helpers

- `scripts/local_config.sample.json` - Public-safe starting template for another machine
- `scripts/bootstrap_zhanfu_skill.py` - Create `local_config.json` from sample
- `scripts/self_test_zhanfu_skill.py` - Validate required config keys before running on a new machine

## Public repo note

Before uploading publicly, prefer the public example references over private/local notes, and do not commit `local_config.json`, run outputs, or environment-specific exports.
