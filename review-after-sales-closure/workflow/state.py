#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case state file manager.
State file: data/cases.csv

Fields:
  order_id, buyer_username, phone, product_id, rating,
  review_text, sms_sent, sms_reply, sms_reply_at,
  verification_status, verification_at, refund_eligible, refund_status, notes, updated_at

Usage:
  from state import CaseState, CaseStatus
  cases = CaseState.load()
  cases.add(order_id=..., product_id=..., ...)
  cases.update(order_id, sms_reply="interested")
  cases.mark_refund_eligible(order_id)
  cases.save()
"""

import csv, os, json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


CASE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "cases.csv")
CASE_FIELDS = [
    "order_id", "buyer_username", "phone", "product_id", "rating",
    "review_text", "sms_sent", "sms_reply", "sms_reply_at",
    "verification_status", "verification_at", "refund_eligible",
    "refund_status", "notes", "created_at", "updated_at"
]


@dataclass
class CaseStatus:
    # SMS status
    SMS_PENDING = "sms_pending"
    SMS_SENT = "sms_sent"
    SMS_REPLIED = "sms_replied"
    SMS_STOPPED = "sms_stopped"

    # Verification
    VERIFY_PENDING = "verify_pending"
    VERIFIED_DELETED = "verified_deleted"
    VERIFIED_PRESENT = "verified_present"

    # Refund
    REFUND_ELIGIBLE = "refund_eligible"
    REFUND_PENDING = "refund_pending"
    REFUND_APPROVED = "refund_approved"
    REFUND_DENIED = "refund_denied"

    # Closure
    CLOSED = "closed"
    ESCALATED = "escalated"


class CaseState:
    def __init__(self):
        self.rows: list[dict] = []
        self._index = {}  # order_id -> row index

    @classmethod
    def load(cls, path: str = None) -> "CaseState":
        path = path or CASE_CSV
        cs = cls()
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cs.rows.append(row)
                    if row.get("order_id"):
                        cs._index[row["order_id"]] = len(cs.rows) - 1
        return cs

    def save(self, path: str = None):
        path = path or CASE_CSV
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CASE_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)

    def add(self, **kwargs) -> dict:
        now = datetime.now().isoformat()
        row = {f: kwargs.get(f, "") for f in CASE_FIELDS}
        row["created_at"] = now
        row["updated_at"] = now
        row["sms_sent"] = CaseStatus.SMS_PENDING
        row["verification_status"] = CaseStatus.VERIFY_PENDING
        row["refund_eligible"] = "no"
        row["refund_status"] = ""
        if row["order_id"]:
            self._index[row["order_id"]] = len(self.rows)
        self.rows.append(row)
        return row

    def get(self, order_id: str) -> Optional[dict]:
        idx = self._index.get(order_id)
        return self.rows[idx] if idx is not None else None

    def update(self, order_id: str, **kwargs):
        row = self.get(order_id)
        if not row:
            return
        now = datetime.now().isoformat()
        for k, v in kwargs.items():
            if k in CASE_FIELDS:
                row[k] = v
        row["updated_at"] = now

    def mark_sms_sent(self, order_id: str, message_sid: str = ""):
        self.update(order_id, sms_sent=CaseStatus.SMS_SENT)

    def mark_sms_reply(self, order_id: str, reply: str):
        self.update(order_id,
                    sms_reply=reply,
                    sms_reply_at=datetime.now().isoformat(),
                    verification_status=CaseStatus.VERIFY_PENDING)

    def mark_verified(self, order_id: str, status: str):
        self.update(order_id,
                    verification_status=status,
                    verification_at=datetime.now().isoformat())

    def mark_refund_eligible(self, order_id: str, notes: str = ""):
        self.update(order_id,
                    refund_eligible="yes",
                    refund_status=CaseStatus.REFUND_ELIGIBLE,
                    notes=notes)

    def get_eligible_for_refund(self) -> list[dict]:
        return [r for r in self.rows if r.get("refund_eligible") == "yes"]

    def get_pending_verification(self) -> list[dict]:
        return [r for r in self.rows
                if r.get("sms_reply") and
                r.get("verification_status") == CaseStatus.VERIFY_PENDING]

    def summary(self) -> dict:
        total = len(self.rows)
        sms_sent = sum(1 for r in self.rows if r.get("sms_sent") == CaseStatus.SMS_SENT)
        sms_replied = sum(1 for r in self.rows if r.get("sms_reply"))
        eligible = sum(1 for r in self.rows if r.get("refund_eligible") == "yes")
        return {
            "total": total,
            "sms_sent": sms_sent,
            "sms_replied": sms_replied,
            "refund_eligible": eligible,
            "by_status": {
                r["order_id"]: {
                    "sms": r.get("sms_sent", ""),
                    "reply": r.get("sms_reply", ""),
                    "verified": r.get("verification_status", ""),
                    "refund_eligible": r.get("refund_eligible", "")
                }
                for r in self.rows
            }
        }
