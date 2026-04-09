#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify review deletion by calling zhanfu-browser's verify_review_deleted.py.

Reads cases with sms_reply set and verification_status == 'verify_pending',
calls verify_review_deleted for each, updates state.

Usage:
  python verify_review.py [--limit N]
"""

import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(__file__))
from state import CaseState, CaseStatus

VERIFY_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "zhanfu-browser", "scripts", "verify_review_deleted.py"
)


def verify_review_deleted(order_id: str, product_id: str, browser_id: str = "2376919") -> dict:
    """
    Call verify_review_deleted.py and parse its JSON output.
    Returns: {"status": "deleted" | "present", "found_on_page": int or None}
    """
    cmd = [
        sys.executable,
        VERIFY_SCRIPT,
        order_id,
        product_id,
        browser_id,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    # Parse JSON from stdout
    lines = result.stdout.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("{") and '"order_id"' in line:
            # Find the start of JSON
            start = result.stdout.find("{")
            if start >= 0:
                try:
                    return json.loads(result.stdout[start:])
                except json.JSONDecodeError:
                    pass
    return {"status": "unknown", "error": result.stdout[:200] + result.stderr[:200]}


def process_pending_verifications(limit: int = None) -> dict:
    """
    For each case with sms_reply set and verification_status == verify_pending,
    run verify_review_deleted.
    """
    cs = CaseState.load()
    pending = [
        r for r in cs.rows
        if r.get("sms_reply")
        and r.get("verification_status") == CaseStatus.VERIFY_PENDING
        and r.get("product_id")
    ]
    if limit:
        pending = pending[:limit]

    deleted, present, errors = 0, 0, 0
    for row in pending:
        order_id = row["order_id"]
        product_id = row["product_id"]
        reply = row.get("sms_reply", "").lower()

        print(f"Verifying: order={order_id} product={product_id} reply={reply}")

        # Only verify if buyer gave a positive reply
        if reply not in ("yes", "interested", "ok", "good", "okay"):
            print(f"  Skipping: reply '{reply}' not a confirmation")
            cs.mark_verified(order_id, CaseStatus.ESCALATED)
            continue

        try:
            result = verify_review_deleted(order_id, product_id)
            status = result.get("status", "unknown")

            if status == "deleted":
                cs.mark_verified(order_id, CaseStatus.VERIFIED_DELETED)
                cs.mark_refund_eligible(order_id, f"Review deleted, reply={reply}")
                deleted += 1
                print(f"  -> DELETED: eligible for refund")
            elif status == "present":
                cs.mark_verified(order_id, CaseStatus.VERIFIED_PRESENT)
                print(f"  -> PRESENT: review still there, escalate")
            else:
                cs.mark_verified(order_id, CaseStatus.ESCALATED)
                errors += 1
                print(f"  -> ERROR/UNKNOWN: {result}")
        except Exception as e:
            print(f"  -> EXCEPTION: {e}")
            cs.update(order_id, notes=f"Verification error: {e}")
            errors += 1

    cs.save()
    return {"deleted": deleted, "present": present, "errors": errors, "total": len(pending)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Verify review deletion for cases with buyer replies")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    print("=== Verifying review deletion ===")
    result = process_pending_verifications(limit=args.limit)
    print(f"\nResult: deleted={result['deleted']} present={result['present']} errors={result['errors']}")
