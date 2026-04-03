# CSV Schema

## Recommended canonical columns

At minimum:
- `phone_number`
- `review_text`
- `rating`
- `order_id`

Recommended full schema:
- `external_id`
- `customer_name`
- `phone_number`
- `review_text`
- `rating`
- `source`
- `order_id`
- `sku`
- `shop_id`
- `shop_name`
- `review_username`
- `buyer_username`

## Accepted aliases already supported by importer

### phone_number
- `phone`
- `mobile`
- `customer_phone`
- `tel`

### review_text
- `review`
- `comment`
- `negative_review`
- `content`

### rating
- `stars`
- `score`

### order_id
- `order`
- `order_no`

### shop_id
- `mall_id`
- `store_id`

### shop_name
- `store_name`
- `shop`

### review_username
- `review_user`
- `review_name`

### buyer_username
- `buyer_name`
- `buyer`

## Validation note
For portable validation, prefer exporting into this canonical schema before import.
