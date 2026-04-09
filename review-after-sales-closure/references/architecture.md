# Architecture

## Goal
Build a portable after-sales closure workflow that can run on other Windows machines with minimal local assumptions.

## Layers

### 1. Data acquisition
Preferred stable input is CSV exported from ZhanFu or another upstream system.
For direct ZhanFu collection, use `zhanfu-browser/scripts/collector_sales.py` to extract negative reviews and record: `order_id`, `product_id`, `page_number` (on the product rating page at collection time), `rating`, `review_text`.

### 2. Case ingestion
Import into `review_cases` with normalized phone numbers and mapped metadata:
- shop_id
- shop_name
- review_username
- buyer_username
- order_id
- product_id  (needed for review verification)
- review_text
- rating
- phone_number

### 3. Classification
Assign `issue_category` using deterministic rules first:
- logistics
- quality
- not_as_described
- service
- usability
- unknown / manual_review

### 4. Queueing
Generate a send queue from cases that:
- are not stopped
- have not been contacted too recently
- are not duplicates in the same batch
- match allowed statuses

### 5. Messaging
Use Twilio in either auth-token mode or API-key mode.
Prefer auto-template mode for category-aware outreach.

### 6. Status reconciliation
Without a public webhook URL, use active polling / sync of outbound message status.

### 7. Reply processing
Map inbound replies to:
- stop
- refund_request
- interested
- negative
- unknown

### 8. Review deletion verification (CLOSED LOOP)

**Key step.** When a buyer replies agreeing to delete their review:

```
1. Call zhanfu-browser/scripts/verify_review_deleted.py
   verify_review_deleted(order_id, product_id)

2. Result:
   status = 'deleted'    → review not found on any page → eligible for refund
   status = 'present'     → review still exists → re-send SMS or escalate
```

### 9. Closure updates
Manual actions update:
- refund_status
- case_status
- review_followup_status
- notes
- last_refund_amount

## Portability rules

- Avoid dependencies on one machine's logged-in browser session.
- Keep integrations file-based where possible.
- Keep environment config in `.env`.
- Make validation runnable in dry/stable mode without external services.
- Reserve live external validation for smoke tests.
