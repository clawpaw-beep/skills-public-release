#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from zhanfu_runtime import ensure_real_webdriver_detailed

VERIFY_TEXT = "请完成下列验证后继续:"
SLIDER_TEXT = "按住左边按钮拖动完成上方拼图"
VERIFY_HINTS = [VERIFY_TEXT, SLIDER_TEXT, "验证", "captcha", "verify", "security check", "robot"]


def find_seller_page(browser):
    for context in browser.contexts:
        for page in context.pages:
            url = (page.url or "").lower()
            if "seller." in url and "tiktokshopglobalselling.com" in url:
                return page
    return None


def has_verification(page: Page) -> bool:
    try:
        body = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return False
    lower = body.lower()
    return any(hint.lower() in lower for hint in VERIFY_HINTS)


def find_slider_handle(page: Page):
    candidates = [
        page.locator('[role="slider"]').first,
        page.locator('div[aria-label*="slider"]').first,
        page.locator('div[class*="slider"]').filter(has_text="").first,
        page.locator('span[class*="slider"]').first,
    ]
    for locator in candidates:
        try:
            if locator.count() and locator.first.is_visible(timeout=1000):
                box = locator.first.bounding_box()
                if box and box.get("width", 0) > 20 and box.get("height", 0) > 20:
                    return locator.first, box
        except Exception:
            pass

    js = """
    () => {
      const nodes = Array.from(document.querySelectorAll('div,span,button'));
      const filtered = nodes.map(el => {
        const r = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const text = (el.innerText || '').trim();
        return {
          el,
          x: r.x,
          y: r.y,
          width: r.width,
          height: r.height,
          area: r.width * r.height,
          bg: style.backgroundImage || '',
          br: style.borderRadius || '',
          cursor: style.cursor || '',
          text,
        };
      }).filter(x => x.width >= 30 && x.width <= 120 && x.height >= 30 && x.height <= 120);
      const pick = filtered.find(x => x.cursor.includes('grab') || x.cursor.includes('pointer')) ||
                   filtered.find(x => x.bg.includes('gradient')) ||
                   filtered.find(x => x.br.includes('50%')) ||
                   filtered[0];
      if (!pick) return null;
      return { x: pick.x, y: pick.y, width: pick.width, height: pick.height };
    }
    """
    box = page.evaluate(js)
    if box:
        return None, box
    return None, None


def estimate_drag_distance(page: Page, handle_box: dict) -> float:
    viewport = page.viewport_size or {"width": 1400, "height": 900}
    probe = page.evaluate(
        """
        () => {
          const nodes = Array.from(document.querySelectorAll('canvas,img,div'));
          const picks = [];
          for (const el of nodes) {
            const r = el.getBoundingClientRect();
            if (r.width < 180 || r.width > 500 || r.height < 80 || r.height > 260) continue;
            const style = getComputedStyle(el);
            const bg = style.backgroundImage || '';
            const text = (el.innerText || '').trim();
            picks.push({x:r.x,y:r.y,width:r.width,height:r.height,bg,tag:el.tagName.toLowerCase(),text});
          }
          picks.sort((a,b)=>(a.y-b.y)||((b.width*b.height)-(a.width*a.height)));
          return picks.slice(0,20);
        }
        """
    )
    if probe:
        same_band = [x for x in probe if abs((x.get("y", 0) + x.get("height", 0) / 2) - (handle_box["y"] + handle_box["height"] / 2)) < 120]
        if same_band:
            widest = max(same_band, key=lambda x: x.get("width", 0))
            return max(80.0, min(float(widest.get("width", 0)) - handle_box["width"] * 0.8, 360.0))
    return max(120.0, min(viewport["width"] * 0.18, 320.0))


def human_drag(page: Page, start_x: float, start_y: float, distance: float) -> None:
    steps = random.randint(22, 34)
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    travelled = 0.0
    for i in range(1, steps + 1):
        progress = i / steps
        ease = 1 - math.pow(1 - progress, 3)
        target = distance * ease
        delta = target - travelled
        travelled = target
        jitter_y = random.uniform(-1.5, 1.5)
        x = start_x + travelled + random.uniform(-0.8, 0.8)
        y = start_y + jitter_y
        page.mouse.move(x, y, steps=random.randint(1, 3))
        time.sleep(random.uniform(0.008, 0.03))
        if 0.35 < progress < 0.75 and random.random() < 0.18:
            micro_back = random.uniform(1.0, 3.5)
            page.mouse.move(x - micro_back, y + random.uniform(-1, 1), steps=1)
            time.sleep(random.uniform(0.01, 0.03))
            page.mouse.move(x, y, steps=1)
    time.sleep(random.uniform(0.05, 0.18))
    page.mouse.up()


def attempt_verify(page: Page, screenshot_dir: Path, max_tries: int = 4) -> dict:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    attempts = []
    for attempt in range(1, max_tries + 1):
        before_path = screenshot_dir / f"attempt_{attempt}_before.png"
        after_path = screenshot_dir / f"attempt_{attempt}_after.png"
        page.screenshot(path=str(before_path), full_page=True)
        handle_locator, handle_box = find_slider_handle(page)
        if not handle_box:
            attempts.append({
                "attempt": attempt,
                "ok": False,
                "error": "slider handle not found",
                "before": str(before_path),
            })
            time.sleep(1)
            continue
        start_x = handle_box["x"] + handle_box["width"] / 2
        start_y = handle_box["y"] + handle_box["height"] / 2
        distance = estimate_drag_distance(page, handle_box) + random.uniform(-8, 12)
        human_drag(page, start_x, start_y, distance)
        time.sleep(2.5)
        page.screenshot(path=str(after_path), full_page=True)
        solved = not has_verification(page)
        attempts.append({
            "attempt": attempt,
            "ok": solved,
            "before": str(before_path),
            "after": str(after_path),
            "handle_box": handle_box,
            "distance": round(distance, 2),
            "page_url": page.url,
        })
        if solved:
            return {"ok": True, "attempts": attempts}
        time.sleep(1.5 + attempt)
    return {"ok": False, "attempts": attempts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimental auto slider verification for TikTok seller pages")
    parser.add_argument("--store-id", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-tries", type=int, default=4)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ensure = ensure_real_webdriver_detailed(args.store_id, startup_wait=90, reopen_once=True, reuse_existing_first=True)
    if not ensure.ready:
        payload = {
            "status": "webdriver_unavailable",
            "store_id": args.store_id,
            "error": ensure.error,
        }
        (output_dir / "auto_slider_verify.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(2)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(ensure.ready.ws_endpoint)
        page = find_seller_page(browser)
        if page is None:
            payload = {
                "status": "no_seller_page",
                "store_id": args.store_id,
                "ws_endpoint": ensure.ready.ws_endpoint,
            }
            (output_dir / "auto_slider_verify.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(payload, ensure_ascii=False))
            raise SystemExit(3)
        page.bring_to_front()
        page.wait_for_timeout(1500)
        payload = {
            "store_id": args.store_id,
            "ws_endpoint": ensure.ready.ws_endpoint,
            "page_url": page.url,
            "verification_present_before": has_verification(page),
        }
        if payload["verification_present_before"]:
            result = attempt_verify(page, output_dir / "screenshots", max_tries=args.max_tries)
            payload.update({
                "status": "ok" if result.get("ok") else "verification_still_present",
                "verification_present_after": has_verification(page),
                "attempts": result.get("attempts", []),
            })
        else:
            payload.update({
                "status": "no_verification_visible",
                "verification_present_after": False,
                "attempts": [],
            })

        payload["body_excerpt"] = page.locator("body").inner_text(timeout=5000)[:4000]
        result_path = output_dir / "auto_slider_verify.json"
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
