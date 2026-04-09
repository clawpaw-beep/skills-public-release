#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the full after-sales closed-loop workflow.

Steps:
  1. Collect negative reviews from ZhanFu (if --collect)
  2. Send SMS to pending cases (if --send-sms)
  3. Verify review deletion for cases with replies (if --verify)
  4. Send Feishu notification (if --notify)

Usage:
  python run_workflow.py --collect --send-sms --verify --notify
  python run_workflow.py --collect          # just collect reviews
  python run_workflow.py --verify          # just verify pending
  python run_workflow.py --collect --send-sms --verify --notify --limit-sms 20
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from state import CaseState


def run_step(name: str, fn, **kwargs):
    print(f"\n{'='*50}")
    print(f"STEP: {name}")
    print(f"{'='*50}")
    try:
        result = fn(**kwargs)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}


def main(
    collect: bool = False,
    send_sms: bool = False,
    verify: bool = False,
    notify: bool = False,
    collect_store_id: str = "2376919",
    collect_min_stars: int = 4,
    sms_limit: int = None,
    verify_limit: int = None,
    dry_run: bool = False,
):
    results = {}

    if collect:
        from collect_negative_reviews import collect_negative_reviews, import_into_state
        run_step("COLLECT NEGATIVE REVIEWS", collect_negative_reviews,
                 store_id=collect_store_id, min_stars=collect_min_stars)

    if send_sms:
        from send_sms import process_pending_cases
        results["sms"] = run_step("SEND SMS", process_pending_cases,
                                   limit=sms_limit, dry_run=dry_run)

    if verify:
        from verify_review import process_pending_verifications
        results["verify"] = run_step("VERIFY REVIEWS", process_pending_verifications,
                                     limit=verify_limit)

    if notify:
        from notify import notify_daily_summary
        results["notify"] = run_step("SEND NOTIFICATION", notify_daily_summary)

    # Final summary
    cs = CaseState.load()
    summary = cs.summary()
    print(f"\n{'='*50}")
    print("FINAL SUMMARY")
    print(f"{'='*50}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="After-sales closed-loop workflow")
    parser.add_argument("--collect", action="store_true", help="Collect negative reviews from ZhanFu")
    parser.add_argument("--send-sms", action="store_true", help="Send SMS to pending cases")
    parser.add_argument("--verify", action="store_true", help="Verify review deletion")
    parser.add_argument("--notify", action="store_true", help="Send Feishu notification")
    parser.add_argument("--dry-run", action="store_true", help="SMS dry run (no real send)")
    parser.add_argument("--store-id", default="2376919")
    parser.add_argument("--min-stars", type=int, default=4)
    parser.add_argument("--limit-sms", type=int, default=None)
    parser.add_argument("--limit-verify", type=int, default=None)
    args = parser.parse_args()

    if not any([args.collect, args.send_sms, args.verify, args.notify]):
        parser.print_help()
        sys.exit(1)

    main(
        collect=args.collect,
        send_sms=args.send_sms,
        verify=args.verify,
        notify=args.notify,
        collect_store_id=args.store_id,
        collect_min_stars=args.min_stars,
        sms_limit=args.limit_sms,
        verify_limit=args.limit_verify,
        dry_run=args.dry_run,
    )
