---
name: review-after-sales-closure
description: End-to-end negative-review after-sales closure workflow. Use when the goal is to import negative-review exports (especially from ZhanFu), classify issue reasons, queue and send SMS via Twilio, sync delivery status, process replies, and track refund/resolution/review-followup state in a portable way across machines.
---

# review-after-sales-closure

Use this skill when you want a portable, repeatable workflow for:
- importing negative-review/contact CSVs
- classifying review reasons
- generating a send queue
- sending after-sales SMS via Twilio
- syncing message delivery status
- processing replies into manual follow-up / refund review
- tracking closure state across refund, resolution, and review follow-up

## Package location

The skill lives at:
- `~/.openclaw/skills/review-after-sales-closure/`

Project root (where the full workflow app lives on the machine):
- Set by the machine owner; typically `~/.openclaw/workspace/review-after-sales-closure/` or a custom path

Portable skill assets:
- `skills\review-after-sales-closure\references\architecture.md`
- `skills\review-after-sales-closure\references\csv-schema.md`
- `skills\review-after-sales-closure\scripts\self_test.py`
- `skills\review-after-sales-closure\scripts\bootstrap.ps1`
- `skills\review-after-sales-closure\scripts\run_server.ps1`

## Working rules

- Keep the workflow split into layers:
  1. import/classification
  2. send queue generation
  3. Twilio sending
  4. status sync
  5. reply handling
  6. manual closure state updates
- Prefer stable CSV-based integration for portability. Do not hard-couple the skill to one machine's live browser session.
- Use real-send validation only against an explicitly approved verified test number.
- Treat refund as a manual approval/process state, not a fully automatic financial action.
- Treat review follow-up as an optional voluntary update request after resolution; do not hard-bind it as a required condition inside the automation.

## Standard operating flow

1. Export negative-review/contact data from ZhanFu or another source into CSV.
2. Import with:
   - `python -m app.scripts.import_zhanfu_reviews --csv <path>`
3. Review queue with:
   - `GET /campaign/queue`
4. Send in small batches with:
   - `python -m app.scripts.send_sms --auto-template --limit <n>`
5. Sync delivery state with:
   - `python -m app.scripts.sync_message_status --limit <n>`
6. Process inbound replies and update cases.
7. Mark refund/resolution/review-followup states manually.
8. Use summary endpoints to track closure progress.

## Validation modes

### Stable self-test
Use `scripts\self_test.py` to validate:
- environment
- DB init
- sample CSV import
- classification
- queue generation
- case state flow

This mode does not require live ZhanFu or real SMS delivery.

### Live Twilio smoke test
Use only when a verified test number is available and the user wants real-send validation.

## References

- `references\architecture.md`
- `references\csv-schema.md`
