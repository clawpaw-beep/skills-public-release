---
name: review-after-sales-closure
description: End-to-end negative-review after-sales closure workflow. Use when the goal is to collect negative reviews from ZhanFu, send SMS via Twilio to buyers, verify review deletion via zhanfu-browser, and track refund eligibility in a file-based case state.
---

# review-after-sales-closure

## Overview

An **OpenClaw-native** after-sales skill. No external FastAPI app needed.

**Dependencies:** `zhanfu-browser` skill (for ZhanFu WebDriver access)

## Workflow

```
采集差评 → 发短信 → 追踪回复 → 验证评价删除 → 退款审批
     ↓
  飞书通知
```

## Scripts

### `workflow/state.py`
File-based case state (CSV: `data/cases.csv`).
Fields: order_id, buyer_username, phone, product_id, rating, review_text, sms_sent, sms_reply, verification_status, refund_eligible, notes.

### `workflow/collect_negative_reviews.py`
Collects negative reviews from the FMCG store's product rating pages via `zhanfu-runtime`. Records: order_id, product_id, buyer_username, review_text.

```
python workflow/collect_negative_reviews.py --store-id 2376919 --min-stars 4
```

### `workflow/send_sms.py`
Sends SMS via Twilio to cases with `sms_sent == sms_pending`. Reads phone numbers from case state. Requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` env vars.

```
python workflow/send_sms.py --dry-run          # test without sending
python workflow/send_sms.py --limit 20
```

### `workflow/verify_review.py`
Calls `zhanfu-browser/scripts/verify_review_deleted.py` for each case with a buyer reply. Updates `verification_status` and `refund_eligible`.

```
python workflow/verify_review.py
python workflow/verify_review.py --limit 10
```

### `workflow/notify.py`
Sends Feishu interactive card to configured webhook (`FEISHU_WEBHOOK` env var).

```
python workflow/notify.py --type daily_summary
python workflow/notify.py --type refund_queue
```

### `workflow/run_workflow.py`
Full orchestrator. Run all steps or individual steps.

```
python workflow/run_workflow.py --collect --send-sms --verify --notify
python workflow/run_workflow.py --collect --send-sms --verify --notify --dry-run
```

## State Flow

```
sms_pending → sms_sent → sms_replied → verify_pending
                                         ↓
                               verified_deleted → refund_eligible=yes
                               verified_present → escalate
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Twilio sender number |
| `FEISHU_WEBHOOK` | Feishu webhook URL for notifications |

## Case State

`data/cases.csv` — file-based state, portable across machines.

| Field | Description |
|-------|-------------|
| `order_id` | TikTok order ID (primary key) |
| `product_id` | Product ID (for review verification) |
| `buyer_username` | Buyer's display name |
| `phone` | Buyer's phone (for SMS) |
| `sms_sent` | `sms_pending` / `sms_sent` |
| `sms_reply` | Buyer's reply text |
| `verification_status` | `verify_pending` / `verified_deleted` / `verified_present` / `escalated` |
| `refund_eligible` | `yes` / `no` |
| `notes` | Free-text notes |

## Notes

- Buyer phone numbers are only accessed for legitimate after-sales SMS outreach.
- Refund approval is always manual — the system marks eligibility, never auto-approves.
- Review verification relies on `zhanfu-browser/scripts/verify_review_deleted.py`.
