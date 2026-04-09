# TikTok Shop 后台模块链路树（站斧探索版）

> 目的：为 `zhanfu-browser` skill 提供页面地图、只读探索规则、自动化入口建议。
>
> 当前状态：第二版，基于 2026-04-06~07 对 FMCG 店铺（`mall_id=2376919`）的只读探索结果整理。
>
> 原则：
> - 默认只读探索
> - 不提交、不保存、不创建、不发货、不退款、不营销投放
> - 先建立页面链路树，再决定自动化入口

---

## 1. 总体导航骨架

当前已在首页左侧确认的一级模块：

- 首页
- 常用
- 商品
- 订单
- 物流
- 广告营销
- 客户
- 联盟
- 直播和视频
- 成长中心
- 应用和服务商
- 数据分析
- 账号健康
- 合规中心
- 财务
- 商家中心（顶部/导航语义出现）
- 客户消息（顶部入口）

---

## 2. 一级链路树（第二版骨架）

```text
TikTok Shop 商家后台
├─ 首页
│  ├─ 经营数据（概览）
│  ├─ 重要待办
│  ├─ 成长激励任务
│  ├─ 营销活动
│  ├─ 商机中心
│  ├─ 购物短视频
│  ├─ 达人联盟
│  ├─ 店铺装修
│  ├─ 广告投放
│  ├─ 店铺健康评分
│  └─ 平台政策与指南
├─ 常用
│  └─ 常用入口聚合区（待拆）
├─ 商品
│  ├─ 商品列表 / 商品管理（推测）
│  ├─ 商品审核 / 被拒商品（推测）
│  ├─ 库存相关（推测）
│  └─ 商品编辑 / 上新（高风险）
├─ 订单
│  ├─ 订单列表（推测）
│  ├─ 待发货 / 已发货 / 异常订单（推测）
│  ├─ 售后订单联动（推测）
│  └─ 发货 / 取消 / 售后处理（高风险）
├─ 物流
│  ├─ 物流看板（推测）
│  ├─ 发货相关配置（推测）
│  └─ 物流模板 / 配送设置（高风险）
├─ 广告营销
│  ├─ 活动 / 广告 / 投放入口（推测）
│  ├─ 优惠 / 促销 / campaign（推测）
│  └─ 投放 / 创建营销（高风险）
├─ 客户
│  ├─ 客服 / 会话 / 用户互动（推测）
│  ├─ 售后触点（推测）
│  └─ 消息发送 / 人工处理（高风险）
├─ 联盟
│  ├─ 达人合作入口
│  ├─ 联盟营销 / 达人管理（推测）
│  └─ 发起合作 / 邀请（高风险）
├─ 直播和视频
│  ├─ 直播运营（推测）
│  ├─ 短视频带货（推测）
│  └─ 创作 / 发布（高风险）
├─ 成长中心
│  ├─ 成长任务
│  ├─ 激励任务
│  └─ 任务执行入口（谨慎）
├─ 应用和服务商
│  ├─ 插件 / 服务商 / 外部工具入口（推测）
│  └─ 授权 / 安装 / 配置（高风险）
├─ 数据分析
│  └─ 深层经营分析入口
├─ 账号健康
│  ├─ 健康评分
│  ├─ 风险提示
│  └─ 诊断 / 详情页（只读优先）
├─ 合规中心
│  ├─ 违规项
│  ├─ 申诉入口
│  └─ 整改流程（高风险）
├─ 财务
│  └─ 财务与结算域入口
├─ 商家中心
│  └─ 商家运营支持 / 中台入口（待拆）
└─ 客户消息
   └─ 客服消息入口（高风险）
```

### 2.1 一级模块功能定位（给 skill 用）

| 模块 | 主要作用 | 自动化价值 | 默认风险 |
|---|---|---|---|
| 首页 | 店铺总览、待办与增长入口聚合 | 高 | 低 |
| 常用 | 快捷入口聚合 | 中 | 中 |
| 商品 | 商品管理、库存、审核 | 高 | 高 |
| 订单 | 订单履约与状态管理 | 很高 | 很高 |
| 物流 | 发货链路与物流配置 | 高 | 很高 |
| 广告营销 | 活动、投放、促销 | 高 | 很高 |
| 客户 | 客服、售后、沟通 | 高 | 很高 |
| 联盟 | 达人合作、联盟带货 | 中高 | 高 |
| 直播和视频 | 内容与直播运营 | 中高 | 高 |
| 成长中心 | 激励任务、成长目标 | 中 | 中高 |
| 应用和服务商 | 插件、服务商、授权 | 中 | 很高 |
| 数据分析 | 指标、趋势、报表 | 很高 | 低 |
| 账号健康 | 风险、评分、诊断 | 中高 | 低 |
| 合规中心 | 违规、申诉、整改 | 高 | 很高 |
| 财务 | 结算、账单、对账 | 很高 | 高 |
| 商家中心 | 运营支持与中台入口 | 中 | 中 |
| 客户消息 | 客服消息处理 | 中高 | 很高 |

---

## 3. 首页模块树（已拆清）

### 3.1 页面定位

- 页面类型：`dashboard`
- 典型 URL：
  - `https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US`
- 作用：
  - 首页总览
  - 店铺经营概览
  - 待办提醒
  - 平台活动与增长入口聚合页

### 3.2 首页内部模块树

```text
首页
├─ 经营数据
│  ├─ 今天（时间维度）
│  ├─ 更多
│  ├─ GMV
│  ├─ 订单数
│  ├─ 页面浏览数
│  └─ 平均访客数
├─ 重要待办
│  ├─ 订单待发货
│  ├─ 售后待处理
│  ├─ 商品低库存
│  ├─ 被拒商品
│  ├─ 待整改违规
│  └─ 可申诉违规
├─ 成长激励任务
│  ├─ 直播任务
│  └─ 短视频任务
├─ 营销活动
│  ├─ 可报名活动
│  ├─ 平台邀请活动
│  └─ 活动日历
├─ 商机中心
│  ├─ 热门商品/趋势词
│  └─ 发同款品（高风险，不自动点）
├─ 购物短视频
│  └─ 去创作视频（高风险，不自动点）
├─ 达人联盟
│  └─ 去查看（谨慎）
├─ 店铺装修
│  └─ 去查看（谨慎）
├─ 广告投放
│  └─ 去查看（谨慎）
├─ 店铺健康评分
└─ 平台政策与指南
```

### 3.3 首页已确认指标

当前探索样本中已看到：

- GMV
- 订单数
- 页面浏览数
- 平均访客数

### 3.4 首页自动化建议

适合：
- 只读截图归档
- 首页 KPI 抓取
- 重要待办数量抓取
- 活动卡片抓取
- 商机中心趋势词抓取

不适合默认自动点击：
- `去完成`
- `发同款品`
- `去创作视频`
- `立即报名`
- 各种 `去查看`

---

## 4. 数据分析模块（Compass 平台 ✅ 已精拆 2026-04-07）

### 4.1 发现

数据分析不在 `seller.us.tiktokshopglobalselling.com`，而在独立的 **Compass 平台**：

```
域名重定向：seller.tiktokshopglobalselling.com → seller.us.tiktokshopglobalselling.com/compass/*
```

### 4.2 URL 路由（已验证）

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **数据概览** | `/compass/data-overview` | ✅ | KPI + PEAKS + 排行榜 |
| **营销数据分析** | `/compass/promotion-analytics` | ✅ | 促销工具 + 活动详情表 |
| **分析排行** | `/compass/analytics-rankings` | ✅ | GMV 排行榜（可筛选类目/指标） |
| 店铺数据分析 | `/compass/data-overview` Tab | — | 数据概览页 Tab，无独立路由 |
| 直播和视频数据 | — | — | 前端 Tab 切换，无独立 URL |
| 商城页和搜索 | — | — | 前端 Tab 切换，无独立 URL |
| 商品数据分析 | — | — | 前端 Tab 切换，无独立 URL |
| 客户数据分析 | — | — | 前端 Tab 切换，无独立 URL |
| 售后数据分析 | — | — | 前端 Tab 切换，无独立 URL |

> **注意：** 大部分子页面是前端 Tab 切换，不是独立路由。直接访问 `/product-analytics` 等 URL 会 302 重定向回 `/data-overview`。

### 4.3 数据概览（/compass/data-overview）

**时间范围：** 支持日/周/月筛选，当前默认昨天

**KPI 指标（2026-04-06）：**

| 指标 | 数值 |
|------|------|
| GMV | $1,316.47 |
| 订单数 | 90 |
| 客户数 | 89 |
| 商品成交件数 | 105 |
| 平均客单价 | $14.63 |
| SKU 订单数 | 91 |
| 直播 GMV | $0.00 |
| 视频 GMV | $73.70 |
| 商品卡 GMV | $1,259.75（84.71%） |

**GMV 拆解（内容类型分布）：**

| 类型 | 金额 | 占比 |
|------|------|------|
| 直播 | $0.00 | 0% |
| 视频 | $1,259.75 | 84.71% |
| 商品卡 | $73.70 | 78.32% |

**GMV 排行榜（家居用品类目，过去 30 天）：**
- Sopami FMCG 排名第 **36** / 前 5,000 名
- 类目内上升 ▲1 位

**PEAKS 经营洞察（五维雷达图）：**

| 维度 | 类型 | 具体指标 |
|------|------|---------|
| Premium Products 高品质商品 | 平台牵引 | 缺货商品数、爆款商品平均数 |
| Engaging Content 内容加速 | 负向因子 | 优质商品页面率(100%)、20+评价商品占比(100%) |
| Activities & Advertising | 高影响力 | 品牌授权商品占比(0%) |
| KOL Collaboration | 高影响力 | 平均商品评分(4.3)、新上架商品数 |
| Service Guarantee | 高影响力 | 平均发货天数(1天) |

### 4.4 营销数据分析（/compass/promotion-analytics）

**时间范围：** 支持近7天/近30天等筛选

**KPI（近7天 2026-03-31 ~ 2026-04-06）：**

| 指标 | 数值 | 环比变化 |
|------|------|---------|
| GMV | $43,593.24 | +128.58% |
| 占店铺 GMV | 89.71% | — |
| 成交订单数 | 3,034 | +150.95% |
| 占总订单 | 90.62% | — |
| 笔单价 | $14.37 | -8.88% |
| 折扣金额 | $33,903.29 | +150.78% |

**促销工具排行：**

| 工具 | 占促销 GMV | GMV |
|------|-----------|------|
| 秒杀 | 99.09% | $43,197.82 |
| 运费折扣 | 4.8% | $2,094.01 |

**我的促销（活动详情表）：**

| 活动名 | 类型 | 状态 | GMV | 成交订单 | 折扣金额 | ROI |
|--------|------|------|------|---------|---------|-----|
| 地板清洁片4.3 | 秒杀 | 已结束 | $20,643.47 | 1,437 | $15,760 | 1.31 |
| 地板清洁片4.6 | 秒杀 | 已结束 | $20,025.94 | 1,428 | $16,130 | 1.24 |
| 全店包邮 | 包邮 | 进行中 | $19,408.34 | 542 | $2,202.58 | 8.81 |
| 地板泡腾片3.31 | 秒杀 | 已结束 | $6,514.67 | 396 | $4,430 | 1.47 |
| 地板清洁片4.9 | 秒杀 | 进行中 | $927.48 | 65 | $750 | 1.24 |

**表格列：** 活动名称 / 类型 / 状态 / 活动时间 / GMV / 成交订单数 / 日均客户数 / 笔单价 / 折扣金额 / ROI / 商品成交件数 / 平均折扣率 / 操作（详情）

### 4.5 分析排行（/compass/analytics-rankings）

**筛选条件：**
- 类目：家居用品（下拉选择）
- 指标：整体 GMV / 商品卡 GMV / 直播 GMV / 视频 GMV

**排行榜（过去 30 天）：**

| 排名 | 店铺 | 变化 |
|------|------|------|
| 36 | **Sopami FMCG**（当前商家） | ▲1 |
| 1 | R & W Co. | — |
| 2 | UFORU NEST | — |
| 3 | QVC, Inc | — |
| 4 | ONAIL HOME | — |
| 5 | Mavwicks Fragrances | — |
| 6 | Gubercen | — |
| 7 | SONGMICS HOME | — |
| 8 | VTOPMART-TT | ▲1 |
| 9 | Mississippi Candle Company | ▼1 |

**表格列：** 排名 / 店铺信息 / 排名变化

### 4.6 数据分析自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 数据概览 KPI | 很高 | 低 | 每日定时采集 |
| PEAKS 五维评分 | 高 | 低 | 成长监控 |
| GMV 排行榜 | 高 | 低 | 竞品跟踪 |
| 营销分析 KPI | 很高 | 低 | 促销效果监控 |
| 促销工具排行 | 高 | 低 | 工具效果对比 |
| 促销活动详情表 | 高 | 低 | 活动 ROI 分析 |
| 导出数据按钮 | 高 | **中风险** | 需单独审批 |

### 4.7 采集方法

```python
# 数据概览
page.goto("https://seller.us.tiktokshopglobalselling.com/compass/data-overview", timeout=60000)
time.sleep(12)  # 站斧加载慢，等待充分渲染
body_text = page.locator("body").inner_text(timeout=15000)

# 营销分析
page.goto("https://seller.us.tiktokshopglobalselling.com/compass/promotion-analytics", timeout=60000)
time.sleep(12)
body_text = page.locator("body").inner_text(timeout=15000)

# 分析排行
page.goto("https://seller.us.tiktokshopglobalselling.com/compass/analytics-rankings", timeout=60000)
time.sleep(12)
body_text = page.locator("body").inner_text(timeout=15000)
```

---

## 5. 财务模块 ✅ 已精拆 2026-04-07

### 5.1 发现

财务模块不在 `seller.us.tiktokshopglobalselling.com`，而在 **`seller.tiktokshopglobalselling.com`**。

### 5.2 URL 路由（已验证）

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **财务概览** | `seller.tiktokshopglobalselling.com/finance/overview` | ✅ | 资金流水表 + 付款记录 |
| **账单** | `seller.tiktokshopglobalselling.com/finance/bills` | ✅ | 本周账单 + 账单明细 |
| **账单支付** | `seller.tiktokshopglobalselling.com/finance/bill-payment` | ✅ | 付款记录表 |
| **保证金** | `seller.tiktokshopglobalselling.com/deposit` | ✅ | 保证金状态（当前免支付） |
| **钱包** | `seller.tiktokshopglobalselling.com/seller-wallet` | ✅ | 可访问 |
| **收益数据分析** | `seller.tiktokshopglobalselling.com/finance/analysis` | ✅ | 可访问 |

### 5.3 财务概览（Finance Overview）

**KPI 指标：**

| 指标 | 数值 |
|------|------|
| 净利润 | $0.00 |
| 本周已付 | $4,142.63 |
| 处理中 | — |
| 未结清 | $25,058.65 |

**资金流水：**

| 类型 | 金额 |
|------|------|
| 总收入 | +$4,403.25 |
| 平台服务费 | -$345.06 |
| 退款手续费 | -$1.25 |
| 商家配送费 | +$111.00 |
| 联盟佣金 | -$2.60 |
| 联盟店铺广告佣金 | -$4.55 |
| 活动服务费 | -$18.16 |

**最近付款记录：**

| 付款日期 | 金额 | 方式 | PingPong ID |
|----------|------|------|-------------|
| 2026/04/06 | $4,142.63 | 已付 | ********ff8d |

### 5.4 账单（Bills）

**账户概览：**

| 指标 | 数值 |
|------|------|
| 可用余额 | $4,142.63 |
| 待处理 | $25,058.65 |
| 本周账单（04/06~04/12）账单总访问 | $4,403.25 |
| 净收入 | -$260.62 |

### 5.5 保证金（Deposit）

| 指标 | 数值 |
|------|------|
| 已付 | $0.00 |
| 待处理 | $0.00 |
| 状态 | 不需要支付保证金 |

### 5.6 账单支付（Bill Payment）

Tab：全部 / 处理中 / 已支付 / 已过期

表格列：账单创建时间 / 账单类型 / 应付金额 / 已支付金额 / 总计 / 付款目的 / 状态 / 操作

### 5.7 采集方法

```python
# 财务概览
page.goto("https://seller.tiktokshopglobalselling.com/finance/overview", timeout=60000)
time.sleep(15)

# 账单
page.goto("https://seller.tiktokshopglobalselling.com/finance/bills", timeout=60000)
time.sleep(15)

# 账单支付
page.goto("https://seller.tiktokshopglobalselling.com/finance/bill-payment", timeout=60000)
time.sleep(15)

# 保证金
page.goto("https://seller.tiktokshopglobalselling.com/deposit", timeout=60000)
time.sleep(15)
```

### 5.8 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 资金流水 | 很高 | 低 | 对账核心 |
| 账单明细 | 很高 | 低 | 定期采集 |
| 付款记录 | 高 | 低 | 付款状态跟踪 |
| 账单支付 | 高 | **中风险** | 含付款操作 |
| 提现/充值 | 高 | **高风险** | 禁止默认自动化 |

---

## 6. 联盟模块 ✅ 已精拆 2026-04-07

### 6.1 URL 路由（已验证）

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **联盟概览** | `/affiliate/landing` | ✅ | KPI + 视频 + 收益数据 |
| 带货视频 | Tab 跳转 | — | 前端 Tab，非独立 URL |
| 直播管理平台 | Tab 跳转 | — | 前端 Tab，非独立 URL |
| 收益数据 | Tab 跳转 | — | 前端 Tab，非独立 URL |
| 达人管理 | Tab 跳转 | — | 前端 Tab，非独立 URL |

### 6.2 联盟概览（Affiliate Landing）

**KPI（近7天）：**

| 指标 | 数值 |
|------|------|
| 预估收益 | $1,242.37 |
| 成交订单 | 87 |
| 带货视频数 | 5 |
| 关联商品数 | 6 |
| 新增合作达人 | 0 |
| 引导成交客户数 | 87 |

**带货视频 Tab：**
- 视频标题 / 关联商品数 / 发布时间 / 订单数 / 预估收益 / 操作（查看详情）

**关联商品 Tab：**
- 商品图片 / 商品名称 / 商品状态 / 联盟专属价 / 操作

### 6.3 采集方法

```python
# 联盟概览
page.goto("https://seller.us.tiktokshopglobalselling.com/affiliate/landing", timeout=60000)
time.sleep(15)
```

### 6.4 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 联盟 KPI | 高 | 低 | 每周采集 |
| 带货视频列表 | 高 | 低 | 达人效果跟踪 |
| 关联商品 | 高 | 低 | 商品联盟状态 |
| 创建合作/推广 | 高 | **高风险** | 禁止默认自动化 |


---

## 7. 订单模块链路树（已完成 ✅ 2026-04-07）

### 6.1 当前确认状态

- 探索日期：2026-04-07
- 店铺：FMCG（mall_id=2376919）
- 关键发现：**订单模块采用双层 iframe 架构**，不同子页面走不同的加载策略

### 6.2 子页面分层

| 子页面 | URL 路径 | 架构 | 可采集性 |
|--------|---------|------|---------|
| 管理订单 | `/order/manage` | 主页面 + ZTI iframe | ❌ 需要站斧 ZTI 授权 |
| 批量发货 | `/order/batch-ship` | 主页面 + ZTI iframe | ❌ 需要站斧 ZTI 授权 |
| 电子面单 | `/order/intercept` | 主页面 + ZTI iframe | ❌ 需要站斧 ZTI 授权 |
| **管理退货** | `/order/return` | 独立页面，无 iframe | ✅ **可直接采集** |
| **管理取消申请** | `/order/cancellation` | 独立页面，无 iframe | ✅ **可直接采集** |
| **管理物流** | `/order/logistics-manage` | 独立页面，无 iframe | ✅ **可直接采集** |
| **管理取消申请** | `/order/cancel` | 独立页面，无 iframe | ✅ **可直接采集** |
| **订单详情** | `/order/detail?order_no={id}&shop_region=US` | 独立页面，无 iframe | ✅ **可直接采集** |

### 6.3 iframe 架构说明（ZTI 安全验证）

**触发条件：** `/order/manage`、`/order/batch-ship`、`/order/intercept` 强制加载

**架构组件：**
```
主页面（seller.us.tiktokshopglobalselling.com/order/manage）
└── iframe#1: chrome-extension://dbhcfopojlklmgfaldcggjamimlbjloo/contentPage/check.html?mallId=2376919
    ├── iframe#2: https://www.tiktok.com/ucenter_web/zti_web（ZTI 登录态）
    └── postMessage 通信通道
```

**站斧扩展检测项目：**
| 检测项 | 状态 |
|--------|------|
| 店铺绑定 | ✅ SopamiFMCG |
| 设备安全检测 | ✅ 成功 |
| 路径伪装检测 | ✅ 成功 |
| 设备绑定 IP | 103.160.50.206 |

**站斧认证 Cookie（27个）：**
- `msToken` - 站斧扩展生成，用于 API 认证
- `SELLER_TOKEN` - base64 JSON，内含 `seller_id: 7494148854457534288`
- `csrftoken` - TikTok CSRF token
- `ttwid`, `odin_tt`, `sid_guard` 等标准 TikTok session cookie

**为什么部分页面能工作？**
- 退货/物流/取消页面：**不走 iframe**，直接通过主页面 URL 加载，数据在 DOM 中直接渲染
- 订单管理/批量发货：**强制走 ZTI iframe**，需要站斧设备授权才能建立 iframe 内的 TikTok session

### 6.4 订单详情页（单订单查询）

**URL 模板：**
```
https://seller.us.tiktokshopglobalselling.com/order/detail?order_no={order_id}&shop_region=US
```

**已验证可用字段（2026-04-07）：**

| 字段 | 说明 | 示例 |
|------|------|------|
| order_id | 订单号（18位） | 577330037834354834 |
| order_status | 订单状态 | 待揽收 |
| location | 收货国家 | United States |
| created_time | 创建时间 | 2026/03/30 13:53:01 |
| logistics_method | 物流方式 | TikTok 物流（升级版） |
| logistics_option | 物流选项 | 标准运输 |
| order_type | 订单类型 | 普通 |
| fulfillment_type | 履约类型 | 由商家履约 |
| warehouse_name | 仓库名称 | 黑马 美西CA仓 |
| warehouse_id | 仓库编号 | 7561535280710453012 |
| product_name | 商品名称 | SOPAMI Floor Cleaning Tablets... |
| variant_name | SKU变体名 | 2-Pack (24 Tablets) |
| merchant_sku | 商家SKU | 2-SPDBQJP |
| sku_id | SKU ID | 1732215258184258384 |
| quantity | 数量 | 2 |
| item_price | 单价 | $16.13 |
| customer_paid | 客户实付总额 | $32.25 |
| earnings | 商家收益 | $23.88 |
| buyer_username | 买家用户名 | gilbertmartinez5894 |
| buyer_name | 买家姓名 | Gilbert Martinez |
| buyer_phone | 买家电话 | (+1)5052035835 |
| buyer_address | 收货地址 | 608 Delamar Ave NW... |
| history_created | 订单创建时间戳 | 2026/03/30 13:53:04 |
| history_paid | 付款时间戳 | 2026/03/30 14:58:34 |
| history_ready_to_ship | 准备发货时间戳 | 2026/03/30 13:54:14 |
| refund_reason | 退款原因 | 商品无法按时送达 |
| refund_apply_time | 申请退款时间 | 2026/04/07 02:09:45 |

### 6.5 退货管理页（/order/return）

**URL：** `https://seller.us.tiktokshopglobalselling.com/order/return?order_sort_comp=OrderSort_UPDATE_TIME_DESC&sub_tab_pending=sub_tab_pending_all&tab=800`

**页面结构：**
- Tab：全部 / 等待商家处理 / 等待TikTok Shop处理 / 已申诉/有争议 / 已解决
- 搜索框：支持退货订单ID、订单ID、物流单号搜索
- 表格列：选中 / 退货ID / 订单ID / 用户名 / 售后类型 / 退款金额 / 退款原因 / 申请时间 / 状态 / 操作
- 操作按钮：退货设置 / 拒付 / 回复 / 接收退货包裹 / 申诉

**数据提取方式：** 直接读取 DOM 的 `page.locator("body").inner_text()`，用正则解析结构化文本

**已知数据（2026-04-07 样本）：**
- 全部：25
- 等待商家处理：4
- 等待TikTok Shop/客户处理：20
- 已解决：1

### 6.6 取消管理页（/order/cancellation）

**URL：** `https://seller.us.tiktokshopglobalselling.com/order/cancellation`

**页面结构：**
- Tab：全部 / 等待商家处理 / 等待TikTok Shop处理 / 已取消 / 已申诉
- 搜索框：支持取消ID、订单ID、物流单号搜索
- Tab 标签：全部(0) / 等待商家处理(0) / 等待TikTok Shop处理(0) / 已取消 / 已申诉(0)
- **注意：当前示例账号无取消订单**

**表格列：** 勾选 / 取消ID / 订单ID / 用户名 / 取消类型 / 订单金额 / 申请时间 / 状态 / 操作

### 6.7 订单模块自动化价值评估（完整版）

| 子页面 | 可采集性 | 自动化价值 | 风险 |
|--------|---------|-----------|------|
| 退货管理 `/order/return` | ✅ 直接 DOM | 很高 | 低 |
| 取消管理 `/order/cancellation` | ✅ 直接 DOM | 高 | 低 |
| 订单详情 `/order/detail` | ✅ URL 参数 | 很高 | 低 |
| 订单管理 `/order/manage` | ❌ ZTI iframe | 很高 | — |
| 批量发货 `/order/batch-ship` | ❌ ZTI iframe | 高 | — |
| 电子面单 `/order/intercept` | ❌ ZTI iframe | 高 | — |
| 管理物流 `/order/logistics-manage` | ⚠️ 直接 URL 无数据 | 高 | — |

### 6.6 已知 API 端点

| 端点 | 方法 | 状态 | 备注 |
|------|------|------|------|
| `/open-api/order/list` | POST | 200 streaming（空内容） | 参数格式未确认 |
| `/api/order/list` | POST | 404 | nginx 拒绝 |
| `/api/v2/order/list` | POST | 404 | nginx 拒绝 |

### 6.7 订单模块自动化建议

**优先采集目标（无需 ZTI 授权）：**
1. 退货管理页 `/order/return` - 售后订单只读采集
2. 订单详情页 `/order/detail?order_no=` - 单订单精确查询
3. 管理物流 `/order/logistics-manage` - 物流状态跟踪
4. 管理取消申请 `/order/cancel` - 取消请求跟踪

**需要站斧 ZTI 授权才能采集：**
- 订单管理 `/order/manage` - 在售订单列表（当前无法自动化）
- 批量发货 `/order/batch-ship` - 批量发货操作
- 电子面单 `/order/intercept` - 物流面单

---

## 7. 风险分层规则（给 skill 用）

### 7.1 低风险（默认可探索）

- 一级菜单导航
- 二级只读 tab
- 纯展示型卡片
- 图表切换
- 页面筛选（不提交）
- 查看详情（需逐页确认）

### 7.2 中风险（谨慎）

- 更多
- 查看详情
- 导出
- 下载
- 账单下载
- 报表下载

### 7.3 高风险（默认禁止）

- 保存
- 提交
- 删除
- 创建
- 编辑
- 修改
- 发货
- 退款
- 提现
- 付款
- 充值
- 同步
- 发送
- 广告投放
- 发同款品
- 去创作视频
- 立即报名

---

## 8. 给 skill 的执行建议

### 8.1 探索顺序

推荐未来探索顺序：

1. 首页
2. 数据分析
3. 财务
4. **订单（已确认链路）**
5. 商品
6. 客户
7. 广告营销
8. 联盟
9. 直播和视频
10. 账号健康 / 合规中心

### 8.2 每个页面的标准探索动作

对每个页面执行：

1. 记录 URL
2. 记录页面标题
3. 截图
4. 抓取可见 heading
5. 抓取左侧/顶部/二级 tab
6. 抓取 KPI 卡片
7. 抓取表格列名
8. 抓取筛选器
9. 标记风险按钮
10. 输出结构化 JSON

### 8.3 标准输出建议

每个模块建议输出：

- `module_name`
- `page_url`
- `page_kind`
- `headings[]`
- `tabs[]`
- `filters[]`
- `metrics[]`
- `tables[]`
- `risk_controls[]`
- `safe_controls[]`
- `automation_notes`

---

## 9. 当前探索产物位置

本轮只读探索输出目录：

- 首页/基础探索：
  - `C:\Users\9400\Documents\zhanfu_store_readonly_explore_20260406_fmcg`
- 数据分析 / 财务精确探索：
  - `C:\Users\9400\Documents\zhanfu_data_finance_precise_20260406_fmcg`
- 商品模块精确探索（2026-04-07）：
  - `C:\Users\9400\Documents\zhanfu_store_readonly_explore_20260407_fmcg`
- 订单模块精确探索（2026-04-07）：
  - `C:\Users\9400\Documents\zhanfu_order_explore_20260407`
  - 关键文件：
    - `tiktok_cookies.json` - 完整认证 cookie（27个）
    - `parsed_return_orders.json` - 退货订单结构化数据
    - `return_page_body_text.txt` - 退货页完整文本
    - `order_detail_577330037834354834.txt` - 订单详情页文本（验证可用）

---

## 10. 商品模块链路树（已完成 ✅）

### 10.1 当前确认状态

- 探索页面：`https://seller.us.tiktokshopglobalselling.com/product/list`
- 状态：2026-04-07 FMCG 店铺只读探索完成
- 侧边栏共 60 个菜单项（顶级 + 展开子项）

### 10.2 完整侧边栏结构（60项）

```text
首页
常用
  ├─ 管理全球商品
  ├─ 商品管理
  ├─ 添加商品
  ├─ 商品优化工具
  ├─ 商品评分
  ├─ 媒体中心
  ├─ 商品机会
  ├─ 管理库存
  ├─ 管理订单
  ├─ 批量发货
  ├─ 管理物流
  ├─ 管理取消申请
  ├─ 管理退货
  ├─ 履约表现
  ├─ 包邮
  ├─ 退货设置
  ├─ 概览
  ├─ 仓库管理
  ├─ 履约设置
  ├─ 物流服务
  └─ Fulfilled by TikTok（FBT）
促销 & 营销
  ├─ 促销活动
  ├─ 营销活动
  ├─ 店铺广告
  ├─ 智能营销
  └─ 店铺页面
触达 & 客户
  ├─ 触达
  └─ 客户群
联盟
  ├─ 带货视频
  └─ 直播管理平台
成长 & 任务
  ├─ 经营洞察
  ├─ 成长权益
  ├─ 我的任务
  ├─ 我的奖励
  └─ 应用商店
服务商
  ├─ TikTok Shop 服务商
  └─ 物流服务市场
数据分析
  ├─ 店铺数据分析
  ├─ 直播和视频数据分析
  ├─ 商品卡
  ├─ 商品数据分析
  ├─ 营销数据分析
  ├─ 客户数据分析
  ├─ 排行榜
  └─ 售后数据分析
账号健康
  ├─ 店铺健康
  ├─ 店铺体验分
  ├─ 达人健康评分
  └─ 明星商家认证计划
合规
  ├─ 合规看板
  ├─ 合规资质
  └─ 商品合规诊断
财务
  ├─ 财务概览
  ├─ 保证金
  ├─ 收益数据分析
  ├─ 账单
  └─ 钱包
商品
  └─ 商品卡 / 商品数据分析（见上方数据分析节点）
```

### 10.3 商品管理页面子结构（product/list）

页面 URL：`https://seller.us.tiktokshopglobalselling.com/product/list?shop_region=US`
页面标题：`TikTok Shop Seller Center | Cross Border`

**商品表格（已确认列）：**
| 列名 | 说明 | 自动化价值 |
|------|------|-----------|
| 商品 | 商品名称/图片 | 高 |
| 状态 | 上架/下架/审核中 | 高 |
| 价格 | SKU价格 | 高 |
| 商品类目 | 所属类目 | 中 |
| 操作 | 编辑/删除等 | **高风险** |

**筛选器（已确认）：**
- 商品名称/ID/SKU 搜索框
- 商品类目筛选
- 状态筛选
- 价格区间筛选（最低价～最高价）
- 批量操作按钮

**操作按钮（已确认）：**
- 批量操作、批量删除、批量编辑（均为**高风险**）
- 筛选、重置（低风险）

### 10.4 商品模块自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 商品列表/管理 | 很高 | 很高 | 含批量编辑/删除，**禁止**默认自动化 |
| 添加商品 | 高 | 很高 | 创建类操作，**禁止** |
| 商品评分 | 中 | 低 | 适合只读采集 |
| 媒体中心 | 中 | 中 | 涉及图片/视频资产 |
| 商品数据分析 | 很高 | 低 | 高价值只读目标 |
| 商品合规诊断 | 高 | 低 | 适合异常监控 |

### 10.5 商品模块已知 URL 模式

```text
https://seller.us.tiktokshopglobalselling.com/product/list
https://seller.us.tiktokshopglobalselling.com/product/manage
```

后续写 skill / collector 时，应优先参考这些探索产物，而不是靠记忆手写。

---

## 11. 商品评分模块 ✅ 已精拆

### 11.1 URL 路由

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **商品评分** | `/product/rating` | ✅ | 只读评分数据 |

### 11.2 页面结构

- Tab：全部 / 好评 / 中评 / 差评 / 商责差评
- 搜索框：支持商品名称/ID 搜索
- 表格列：商品 / 评分 / 评价内容 / 评价者 / 发布时间
- 操作：回复

### 11.3 数据提取方式

```python
page.goto("https://seller.us.tiktokshopglobalselling.com/product/rating", timeout=45000, wait_until="domcontentloaded")
time.sleep(10)
data = page.evaluate("""() => ({
    tabs: Array.from(document.querySelectorAll("[role='tab'], .ant-tabs-tab")).map(t => t.textContent.trim()),
    table_headers: Array.from(document.querySelectorAll("table th")).map(h => h.textContent.trim()),
    table_rows: Array.from(document.querySelectorAll("table tbody tr")).slice(0, 50).map(r =>
        Array.from(r.querySelectorAll("td")).map(d => d.textContent.trim())
    ),
    summary_lines: Array.from(document.querySelectorAll("script")).map(s => s.textContent).filter(t => t.includes("总评价") || t.includes("差评"))
})""")
```

### 11.4 评价验证脚本

已实现 `scripts/verify_review_deleted.py`：

```
verify_review_deleted(order_id, product_id, known_page=None)
```

**采集时**：记录每个差评的 `order_id + product_id + page_number`（因为差评分散在不同页）

**验证时**：
- 有 known_page → 直接翻到该页确认 order_id 是否还在
- 无 known_page → 从第1页开始逐页搜索，直到找到 order_id 或到达末页

**返回值**：`deleted`（未找到）/ `negative`（1-3星）/ `positive`（4-5星）/ `not_found`

### 11.5 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 商品评分列表采集 | 高 | 低 | 适合定期采集监控 |
| 差评监控 | 很高 | 低 | 高价值预警目标 |
| 商责差评率 | 高 | 低 | 店铺健康指标 |
| **评价删除验证** | 很高 | 低 | 售后闭环核心环节 |

---

## 12. 直播管理平台模块 ✅ 已精拆

### 12.1 URL 路由

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **直播管理平台** | `/live/overview` | ✅ | 直播数据概览 |

### 12.2 页面结构

- Tab：概览 / 直播记录 / 我的带货视频（推测）
- KPI 卡片：直播场次 / GMV / 观看人数 / 平均在线人数
- 表格：直播标题 / 开播时间 / 时长 / GMV / 观看人数 / 操作（查看详情）

### 12.3 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 直播概览 KPI | 高 | 低 | 每周采集 |
| 直播记录表 | 高 | 低 | 效果跟踪 |
| 创建直播/发布 | 高 | **很高** | 禁止默认自动化 |

---

## 13. 合规看板模块 ✅ 已精拆

### 13.1 URL 路由

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **合规看板** | `/compliance/dashboard` | ✅ | 违规/整改/申诉 |

### 13.2 页面结构

- Tab：全部 / 商品合规 / 知识产权保护 / 营销合规 / 物流合规（推测）
- KPI 卡片：违规数 / 待整改 / 待申诉
- 表格：违规类型 / 商品 / 处罚 / 状态 / 截止时间 / 操作

### 13.3 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 合规看板总览 | 很高 | 低 | 高价值监控 |
| 违规项列表 | 很高 | 低 | 整改跟踪 |
| 申诉提交 | 高 | **很高** | 禁止默认自动化 |

---

## 14. 应用商店模块 ✅ 已精拆

### 14.1 URL 路由

| 页面 | URL | 可采集 | 备注 |
|------|-----|--------|------|
| **应用商店** | `/appstore/gs-my` | ✅ | 已安装/已购买应用 |

### 14.2 页面结构

- Tab：我已购买 / 我安装的 / 免费应用
- 卡片列表：应用图标 / 名称 / 开发商 / 操作按钮
- 筛选：免费/付费

### 14.3 自动化价值评估

| 子模块 | 自动化价值 | 风险 | 备注 |
|--------|-----------|------|------|
| 已安装应用列表 | 中 | 低 | 配置盘点 |
| 应用安装/卸载 | 中 | **高** | 需审批 |

---

## 15. 全模块补全路线

### 15.1 已完成

- ~~首页结构第一版~~ ✅
- ~~数据分析入口确认~~ ✅ — Compass 平台 URL + KPI + PEAKS + 营销分析 + 排行榜
- ~~财务入口确认~~ ✅ — seller.tiktokshopglobalselling.com/finance/* 域名 + KPI + 账单 + 资金流水
- ~~一级模块功能定位第二版骨架~~ ✅
- ~~商品模块链路树~~ ✅ — 侧边栏 60 项 + 商品评分/数据分析/合规诊断子模块
- ~~订单模块链路树~~ ✅ — ZTI iframe 架构 + 退货/取消/物流/订单详情可直接采集
- ~~数据分析模块链路树~~ ✅
- ~~财务模块链路树~~ ✅
- ~~联盟模块链路树~~ ✅ — 联盟概览 KPI + 带货视频
- ~~商品评分模块~~ ✅ — `/product/rating` + 差评监控
- ~~直播管理平台模块~~ ✅ — `/live/overview` + 直播概览
- ~~合规看板模块~~ ✅ — `/compliance/dashboard` + 违规/整改/申诉
- ~~应用商店模块~~ ✅ — `/appstore/gs-my` + 已安装应用列表

### 15.2 正在补完

- 一级模块的风险分层与自动化价值标注

### 15.3 待继续补完

- 物流模块链路树
- 广告营销模块链路树
- 客户模块链路树
- 直播和视频模块链路树（直播管理平台已达，其余待补）
- 账号健康模块链路树
- 商家中心模块链路树
- 每个模块的 URL 模式总结
- 表格字段级采集说明
- 页面识别规则（DOM / 文案 / URL）
- 适合封装成 collector 的页面列表
- 哪些适合截图采集，哪些适合结构化采集，哪些只适合人工处理
