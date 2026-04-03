from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path

TEMP_DIR = Path(tempfile.mkdtemp(prefix="review_self_test_env_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEMP_DIR / 'self_test.db').as_posix()}"

PROJECT_ROOT = Path(r"C:\Users\9400\.openclaw\workspace\twilio-review-mvp")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.init_db import init_db
from app.models import ReviewCase
from app.services.campaign_service import CampaignService
from app.services.case_flow_service import CaseFlowService
from app.services.importer import import_csv
from app.services.review_classifier import classify_review_reason, pick_template_for_category


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    print("[1/6] init db")
    init_db()

    print("[2/6] build temp csv")
    csv_path = TEMP_DIR / "sample_reviews.csv"
    rows = [
        {
            "external_id": "CASE-001",
            "customer_name": "Alice",
            "phone_number": "+15550000001",
            "review_text": "Late delivery and shipping delay",
            "rating": "1",
            "order_id": "ORDER-001",
            "shop_id": "2376919",
            "shop_name": "FMCG",
            "review_username": "alice_review",
            "buyer_username": "alice_buyer",
        },
        {
            "external_id": "CASE-002",
            "customer_name": "Bob",
            "phone_number": "+15550000002",
            "review_text": "Product arrived broken and poor quality",
            "rating": "1",
            "order_id": "ORDER-002",
            "shop_id": "2376919",
            "shop_name": "FMCG",
            "review_username": "bob_review",
            "buyer_username": "bob_buyer",
        },
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("[3/6] import csv")
    with SessionLocal() as db:
        result = import_csv(db, str(csv_path), source="self_test")
        print(result)
        assert_true(result["imported"] == 2, "expected 2 imported rows")

    print("[4/6] validate classification + queue")
    with SessionLocal() as db:
        cases = db.query(ReviewCase).filter(ReviewCase.external_id.in_(["CASE-001", "CASE-002"])).all()
        assert_true(len(cases) == 2, "expected 2 cases in db")
        categories = {case.external_id: case.issue_category for case in cases}
        assert_true(categories.get("CASE-001") == "logistics", "CASE-001 should classify as logistics")
        assert_true(categories.get("CASE-002") == "quality", "CASE-002 should classify as quality")

        queue = CampaignService().build_send_queue(db=db, limit=10, lookback_hours=168)
        print(queue)
        assert_true(queue["queue_size"] >= 2, "expected queue size >= 2")

    print("[5/6] validate templates")
    assert_true("delivery" in pick_template_for_category("logistics").lower(), "logistics template mismatch")
    assert_true("product" in pick_template_for_category("quality").lower(), "quality template mismatch")
    assert_true(classify_review_reason("not as described", "1") == "not_as_described", "classification rule mismatch")

    print("[6/6] validate case flow")
    with SessionLocal() as db:
        case = db.query(ReviewCase).filter(ReviewCase.external_id == "CASE-001").first()
        assert_true(case is not None, "case missing")
        flow = CaseFlowService()
        flow.mark_sms_sent(case)
        flow.apply_inbound_reply(case, "refund_request", body="refund please")
        db.commit()
        db.refresh(case)
        assert_true(case.case_status == "pending_refund", "case should move to pending_refund")
        assert_true(case.refund_status == "pending_review", "refund status should be pending_review")
        flow.mark_refund_processed(case, amount="5.00", note="self-test refund")
        flow.mark_resolved(case, note="self-test resolved")
        flow.mark_review_followup_invited(case, note="self-test follow-up")
        db.commit()
        db.refresh(case)
        assert_true(case.refund_status == "processed", "refund status should be processed")
        assert_true(case.case_status == "resolved", "case should be resolved")
        assert_true(case.review_followup_status == "invited_after_resolution", "review follow-up should be invited")

    print("SELF_TEST_OK")


if __name__ == "__main__":
    main()
