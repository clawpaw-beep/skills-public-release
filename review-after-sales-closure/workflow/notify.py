#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Feishu notifications for workflow events.

Usage:
  python notify.py --type daily_summary
  python notify.py --type refund_queue
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from state import CaseState


FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")


def send_card(content: dict) -> bool:
    """Send a Feishu interactive card via webhook."""
    if not FEISHU_WEBHOOK:
        print("FEISHU_WEBHOOK not set, skipping notification")
        return False
    import urllib.request
    payload = json.dumps(content, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Failed to send Feishu notification: {e}")
        return False


def notify_daily_summary(cs: CaseState = None) -> dict:
    """Send daily summary card."""
    if cs is None:
        cs = CaseState.load()
    s = cs.summary()

    # Build refund eligible list
    eligible = cs.get_eligible_for_refund()
    eligible_text = ""
    if eligible:
        rows = []
        for r in eligible[:10]:  # top 10
            rows.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{r['buyer_username']}** | order: `{r['order_id'][-8:]}` | verified: {r.get('verification_status','')}"
                }
            })
        eligible_text = "\n".join(f"- @{r['buyer_username']} | order: `{r['order_id'][-8:]}`" for r in eligible[:5])
    else:
        eligible_text = "No cases eligible for refund yet."

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "📋 售后闭环日报"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**总案件数:** {s['total']}\n"
                            f"**已发短信:** {s['sms_sent']}\n"
                            f"**买家回复:** {s['sms_replied']}\n"
                            f"**可退款:** {s['refund_eligible']}"
                        )
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**待退款名单 ({len(eligible)}件):**\n{eligible_text}"
                    }
                }
            ]
        }
    }

    ok = send_card(card)
    return {"ok": ok, "total": s["total"], "eligible": len(eligible)}


def notify_refund_queue() -> dict:
    """Send current refund-eligible queue."""
    cs = CaseState.load()
    eligible = cs.get_eligible_for_refund()

    rows = []
    for r in eligible:
        rows.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**@{r['buyer_username']}**\n"
                    f"Order: `{r['order_id']}`\n"
                    f"Product: `{r.get('product_id','')}`\n"
                    f"验证: {r.get('verification_status','')} | 备注: {r.get('notes','')}"
                )
            }
        })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"💰 待退款名单 ({len(eligible)}件)"},
                "template": "orange"
            },
            "elements": rows if rows else [{"tag": "div", "text": {"tag": "lark_md", "content": "暂无待退款"}}]
        }
    }

    ok = send_card(card)
    return {"ok": ok, "count": len(eligible)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["daily_summary", "refund_queue"], default="daily_summary")
    args = parser.parse_args()

    if args.type == "daily_summary":
        notify_daily_summary()
    elif args.type == "refund_queue":
        notify_refund_queue()
