# Store Map

Store name → `mall_id` mapping for the current machine.

## All Stores

| mall_id | Store Name | Region |
|---------|-----------|--------|
| 2376919 | Sopami FMCG | US |
| 2273435 | Tools | US |
| 2337386 | Hardware | US |
| 2210139 | US8 | US |
| 2264045 | US7 | US |
| 2779003 | Sopamibox | US |

## Frequently Used

- **FMCG**: `2376919`
- **Tools**: `2273435`
- **Hardware**: `2337386`
- **US8**: `2210139`
- **US7**: `2264045`
- **Sopamibox**: `2779003`

## mall_id Resolution via ZhanFu API

If you need to find the `mall_id` for a store by name, use:

```python
from zhanfu_runtime import get_browser_list
stores = get_browser_list()
# returns list of dicts with 'mall_id', 'shop_name', etc.
```

## Adding New Stores

When a new store is added:
1. Run `get_browser_list()` to retrieve its `mall_id`
2. Add it to this table above
3. Do not commit real store names/IDs to public examples
