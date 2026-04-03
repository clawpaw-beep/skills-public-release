from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3] / "twilio-review-mvp"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models import ReviewCase, MessageLog
from app.services.message_status_sync import MessageStatusSyncService
from app.services.twilio_service import TwilioService


def main() -> None:
    parser = argparse.ArgumentParser(description="Live Twilio smoke test: send one real message to a verified test number and sync status")
    parser.add_argument("--to", required=True, help="Verified destination phone number in E.164 format")
    parser.add_argument("--wait-seconds", type=int, default=10)
    args = parser.parse_args()

    body = "Live Twilio smoke test from review-after-sales-closure. Please ignore."

    with SessionLocal() as db:
        case = db.query(ReviewCase).filter(ReviewCase.phone_number == args.to).order_by(ReviewCase.id.desc()).first()
        if not case:
            case = ReviewCase(
                external_id=f"LIVE-SMOKE-{int(time.time())}",
                customer_name="Live Smoke Test",
                phone_number=args.to,
                review_text="live smoke test",
                rating="1",
                source="live_twilio_check",
                order_id=f"LIVE-{int(time.time())}",
                case_status="classified",
                issue_category="unknown",
            )
            db.add(case)
            db.commit()
            db.refresh(case)

        case.stop_contact = False
        case.last_outbound_sent_at = None
        db.commit()

        result = TwilioService().send_bulk_messages(
            db=db,
            body_template=body,
            limit=1,
            lookback_hours=1,
            only_statuses=[case.case_status],
            auto_template=False,
        )
        print("SEND_RESULT:", result)

        sid = None
        for item in result.get("details", []):
            if item.get("phone") == args.to and item.get("message_sid"):
                sid = item["message_sid"]
                break
        if not sid:
            raise RuntimeError(f"No message SID returned: {result}")

        time.sleep(args.wait_seconds)
        sync = MessageStatusSyncService().sync_recent(db=db, limit=20, only_pending=False)
        print("SYNC_RESULT:", sync)

        row = db.query(MessageLog).filter(MessageLog.message_sid == sid).first()
        if row:
            print("FINAL_LOG:", {
                "message_sid": row.message_sid,
                "status": row.status,
                "error_code": row.error_code,
                "error_message": row.error_message,
                "to_number": row.to_number,
            })


if __name__ == "__main__":
    main()
