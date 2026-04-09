# Sales Minimal Workflow

目标：把站斧链路收敛到“进店并抓到销售额（GMV）”这一步。

## 1. 判断该走哪条链路

优先级：

1. **已有 CDP 可复用**
   - 优先用 DrissionPage 直接连接现成端口
   - 本机曾实测可用：`127.0.0.1:12627`
2. **CDP 不通，但 WebDriver API 可用**
   - 再尝试 `45008 -> OpenBrowser -> GetBrowserWebDriver -> CDP`
3. **两条都不通**
   - 先排障，不要直接承诺能抓数据

## 2. 最短验证步骤

### A. 连接现有站斧浏览器

示例：

```python
import os
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
from DrissionPage import Chromium

browser = Chromium('127.0.0.1:12627')
print('Connected!', len(browser.tab_ids))
```

### B. 看当前页签是不是店铺后台

如果页签全是这些，说明还没进店：
- `chrome://newtab/`
- `chrome://omnibox-popup.top-chrome/`
- `chrome://omnibox-popup.top-chrome/omnibox_popup_aim.html`

如果是登录页，也不能继续采：
- `https://seller.tiktokshopglobalselling.com/account/login?...`

### C. 进入卖家后台首页

```python
tab = browser.latest_tab
tab.get('https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US')
```

等待 8-12 秒后读取：
- `tab.url`
- `tab.title`
- `document.body.innerText`

## 3. 分支判断

### 情况 1：跳到登录页

说明登录态失效。

处理：
- 停止自动采集
- 明确告诉用户：请先手动登录站斧里的 TikTok Shop 店铺
- 用户说“已进入后台”后再继续

### 情况 2：进入后台但没到经营数据

继续导航到首页或经营数据页，再读取页面文本。

### 情况 3：读到经营数据

从页面文本中提取：
- `GMV`
- `订单数`
- `页面浏览数`
- `平均访客数`

## 4. 输出标准

最少要给出：
- 是否成功进入店铺后台
- 当前页面 URL
- 是否读到 `GMV`
- 若成功，保存路径
- 若失败，失败阶段（未连上浏览器 / 未进入店铺 / 登录态失效 / 页面没有经营数据）

## 5. 推荐脚本

### 首选
- `scripts/collector_sales.py`
  - 适合在店铺已打开、链路基本通畅时做结构化销售额采集

### 辅助排障
- `C:\Users\9400\get_drission.py`
  - 最短验证：只验证 DrissionPage 是否能连上站斧
- `C:\Users\9400\get_drission_full.py`
  - 读取当前页全文，适合快速看页面到底是什么

## 6. 经验结论

本机最近一次实测说明：
- DrissionPage 直连成功，不代表已经打开店铺
- 能连到浏览器但页签全是默认页，说明只是“连上空浏览器”
- 用户口头说“登录好了”也不够，必须重新读取页签 URL 和正文确认已经进入后台
