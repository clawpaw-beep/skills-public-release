# 首页销售 KPI 字段标准

当前 `collector_sales.py` 与 `minimal_zhanfu_gmv.py` 输出以下首页 KPI 字段。

## 标准字段

- `gmv`：销售额 / GMV
- `gmv_change`：GMV 变化率
- `customers`：客户数（英文页常见为 `Customers`；部分中文页可能没有完全对齐）
- `customers_change`：客户数变化率
- `sku_orders`：订单数（中文页常见为 `订单数`，英文页常见为 `SKU orders`）
- `sku_orders_change`：订单数变化率
- `visitors`：访客/浏览类指标（英文页常见为 `Visitors`，中文页可能来自 `页面浏览数` 或 `访客数`）
- `visitors_change`：访客/浏览类指标变化率

## 注意事项

### 1. 字段是“统一输出名”，不是平台原始名
平台页面中英版本文案不同，因此 collector 会做统一映射。

例如：
- `订单数` → `sku_orders`
- `SKU orders` → `sku_orders`
- `Visitors` / `页面浏览数` / `访客数` → `visitors`

### 2. `customers` 不保证每个店铺都稳定有值
有些店铺首页结构不同，可能：
- 不显示该卡片
- 或文案位置不稳定
- 或当前页面版本与其他店铺不一致

因此 `customers` 允许为空字符串，不应因此判定整体采集失败。

### 3. verification 页面不一定代表失败
如果页面仍带验证特征，但 KPI 文本已能读到，则 collector 仍可视为成功。

## 推荐判断规则

当以下字段至少满足其一时，可认为首页 KPI 已成功读取：
- `gmv`
- `sku_orders`
- `visitors`

如果三者都为空，再判定为首页 KPI 读取失败。
