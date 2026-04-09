# ZhanFu 技能链路优化方案

基于 2026-04-08 实测，当前技能要想把链路跑顺，重点不是继续加单点脚本，而是把整套链路统一成同一个运行时协议。

## 1. 当前实际断点

### A. API 层
- `45008` 不是总能直接连通
- 有些脚本一上来就 `GetBrowserList()`，API 没起来时会直接死

### B. WebDriver / CDP 层
- `OpenBrowser` 成功不代表浏览器可控
- `GetBrowserWebDriver` 返回端口，不代表端口真的监听
- 同一台机器、不同店铺，CDP readiness 表现不一致

### C. 页面层
- CDP 已就绪，不代表已经进入 TikTok Shop seller 页
- 实际可能停在：
  - 站斧扩展页
  - 空白页 / newtab
  - TikTok 登录页
  - seller 页但未落到目标页面

### D. 技能层
- 文档已经知道“优先 DrissionPage、动态发现 CDP、不要信 OpenBrowser 成功”，但不是所有脚本都严格遵守
- 一部分脚本仍然默认：
  - 直接 `OpenBrowser`
  - 直接信 `GetBrowserWebDriver`
  - 默认第一页就是业务页
  - 用 Playwright 作为默认连接层

## 2. 应统一成的标准链路

所有站斧脚本统一走：

1. 检查 `45008`
2. 不通则自动启动站斧，并等待 API readiness
3. `OpenBrowser(browserId)`
4. 等待 5-10 秒
5. 校验 `GetBrowserWebDriver` 返回端口是否真实可连
6. 若失败，则扫描 `12620-12660` 寻找真实 CDP
7. 用 DrissionPage 建立连接
8. 枚举全部标签页并分类：扩展页 / 空白页 / 登录页 / seller 页
9. 必要时点击“打开店铺”或主动跳 seller 首页
10. 确认进入目标业务页后再开始采集

## 3. 建议修改优先级

### P0 必做

#### 3.1 强化 `zhanfu_runtime.py`
统一提供：
- `ensure_api_ready()`
- `ensure_store_cdp_ready()`
- `snapshot_tabs()`
- `classify_tabs()`
- `open_store_from_extension_if_needed()`
- `goto_seller_home_if_needed()`

目标：以后 collector 不再自己写页面连接逻辑。

#### 3.2 把“假 ready”作为显式状态
`GetBrowserWebDriver` 返回端口但端口未监听时，不要只写成普通 error，应该明确标注：
- `fake_ready`
- `webdriver_port_unreachable`

这样后面统计时能一眼看出是站斧假成功，不是脚本写挂了。

#### 3.3 统一页面诊断输出
每个 collector 第一次连上浏览器后，都输出：
- 当前 tab 数量
- 每个 tab 的 url
- title
- body_excerpt（前若干行）
- page_kind

这样定位“扩展页卡死”会非常快。

### P1 应做

#### 3.4 `collector_sales.py` 去 Playwright 依赖化
现在这脚本虽然做了不少诊断，但默认底座还是 Playwright connect_over_cdp。
建议改成：
- DrissionPage 做连接与页面获取
- Playwright 仅保留为可选实验分支

#### 3.5 新增通用诊断脚本
建议加一个：
- `scripts/diagnose_store_entry.py`

只做：
- 打开店铺
- 建立 CDP
- 输出 tabs 诊断
- 尝试点“打开店铺”
- 尝试跳首页
- 输出最终页面分类

这会比直接跑业务 collector 更适合排查。

#### 3.6 healthcheck 分层
`healthcheck_zhanfu.py` 应拆成：
- API ready
- store exists
- cdp ready
- page entry ready

不要只停在 FMCG 是否能拿到 CDP。

### P2 可做

#### 3.7 建立店铺稳定性画像
为不同店铺记录：
- 是否经常 fake-ready
- 是否经常停扩展页
- 是否经常掉登录态
- 首次打开平均耗时

这样调度时可以优先选稳定店铺验证链路。

## 4. 对 SKILL.md 的建议

SKILL.md 里应该继续强化这几个原则：
- 不要把 `OpenBrowser` 成功当成可用
- 不要把 `GetBrowserWebDriver` 返回端口当成可用
- 默认优先 DrissionPage
- 先判定是运行时问题还是页面问题
- 调试新链路时先测稳定店铺，再回 FMCG

## 5. 推荐下一步实际动作

1. 先改 `zhanfu_runtime.py`，补齐页面层辅助函数
2. 新建 `diagnose_store_entry.py`
3. 用 Tools / Hardware 跑页面诊断
4. 页面入口跑顺后，再回头修 FMCG
5. 最后再改 `collector_sales.py` 和其他 collector 全量复用统一 runtime

## 6. 判断标准

当下面这 4 项都稳定时，才能算技能链路顺畅：

- API 能自动拉起
- CDP 能真实连通
- 店铺页能稳定进入
- 业务页能稳定读取

只做到前两项，不算真正可用。
