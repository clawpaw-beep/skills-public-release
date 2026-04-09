#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send SMS to buyers via Twilio.

Reads cases from state file, sends SMS to those with no sms_reply yet,
updates case state with message_sid.

Usage:
  python send_sms.py [--limit N] [--dry-run]
"""

import sys, os, json, csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from state import CaseState, CaseStatus


# Twilio config (load from environment)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")


def get_twilio_client():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise RuntimeError("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set in environment")
    from twilio.rest import Client
    return Client(TWILIO_AUTH_TOKEN, TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID)


SMS_TEMPLATES = {
    "negative": (
        "Dear Customer, we noticed you had a concern with your recent order. "
        "We'd love to make it right — please reply YES and we'll process a full refund. "
        "Thank you for giving us a chance to improve!"
    ),
    "followup": (
        "Hi! Just following up on our message earlier. "
        "Reply YES if you'd like us to process a refund for your recent order. "
        "We value your feedback and want to make things right."
    ),
}


def send_sms(to_phone: str, template_key: str = "negative") -> str:
    """Send SMS. Returns message_sid."""
    client = get_twilio_client()
    body = SMS_TEMPLATES.get(template_key, SMS_TEMPLATES["negative"])
    message = client.messages.create(
        body=body,
        from_=TWILIO_FROM_NUMBER,
        to=to_phone,
    )
    return message.sid


def process_pending_cases(limit: int = None, dry_run: bool = False) -> dict:
    """
    Send SMS to all cases with sms_sent == 'sms_pending'.
    Returns summary dict.
    """
    cs = CaseState.load()
    pending = [
        r for r in cs.rows
        if r.get("sms_sent") == CaseStatus.SMS_PENDING
        and r.get("phone")
    ]
    if limit:
        pending = pending[:limit]

    sent, failed, skipped = 0, 0, 0
    for row in pending:
        order_id = row["order_id"]
        phone = row["phone"]
        buyer = row.get("buyer_username", "")

        if dry_run:
            print(f"[DRY RUN] Would send SMS to {phone} ({buyer}), order={order_id}")
            sent += 1
            cs.update(order_id, sms_sent=CaseStatus.SMS_SENT)
            continue

        try:
            sid = send_sms(phone)
            cs.update(order_id, sms_sent=CaseStatus.SMS_SENT)
            print(f"Sent: order={order_id} sid={sid}")
            sent += 1
        except Exception as e:
            cs.update(order_id, notes=f"SMS failed: {e}")
            print(f"Failed: order={order_id} error={e}")
            failed += 1

    cs.save()
    return {"sent": sent, "failed": failed, "skipped": skipped, "total": len(pending)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send SMS to pending review cases")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of SMS to send")
    parser.add_argument("--dry-run", action="store_true", help="Print without actually sending")
    args = parser.parse_args()

    print("=== Sending SMS ===")
    result = process_pending_cases(limit=args.limit, dry_run=args.dry_run)
    print(f"\nResult: sent={result['sent']} failed={result['failed']}")
