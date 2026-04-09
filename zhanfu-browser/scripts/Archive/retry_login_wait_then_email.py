#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from zhanfu_runtime import ensure_real_webdriver_detailed, get_browser_list
from collector_sales import (
    click_open_store_if_zhanfu_page,
    detect_page_kind,
    pick_any_non_extension_page,
    pick_best_page,
    safe_page_body,
    safe_page_title,
    snapshot_browser_pages,
    try_navigate_to_seller_home,
    wait_for_non_extension_page,
)


EMAIL_SWITCH_HINTS = [
    "使用邮箱登录",
    "邮箱登录",
    "Email",
    "email",
    "Use email",
    "Continue with email",
]
LOGIN_HINTS = ["login", "sign in", "sign-in", "log in", "登录"]
VERIFY_HINTS = ["captcha", "verify", "verification", "security check", "robot", "验证"]


def pick_store_page(browser):
    page = None
    best_score = -999
    deadline = time.time() + 60
    while time.time() < deadline:
        candidate, current_score = pick_best_page(browser)
        if candidate is not None:
            page = candidate
            best_score = current_score
            if current_score >= 80:
                break
        time.sleep(2)

    click_result = None
    if page is None:
        page, best_score = pick_any_non_extension_page(browser)

    if page is None:
        click_result = click_open_store_if_zhanfu_page(browser)
        page, best_score = wait_for_non_extension_page(browser, timeout_seconds=45)

    return page, best_score, click_result


def try_click_email_switch(page):
    logs = []
    for hint in EMAIL_SWITCH_HINTS:
        try:
            el = page.get_by_text(hint, exact=False).first
            if el.is_visible(timeout=1500):
                el.click(timeout=5000)
                page.wait_for_timeout(3000)
                logs.append({"hint": hint, "clicked": True})
                return True, logs
        except Exception as exc:
            logs.append({"hint": hint, "clicked": False, "error": str(exc)})
    return False, logs


def inspect_fields(page):
    script = r"""
() => {
  const inputs = Array.from(document.querySelectorAll('input'));
  return inputs.map((el, i) => ({
    index: i,
    type: (el.getAttribute('type') || '').toLowerCase(),
    name: el.getAttribute('name') || '',
    autocomplete: el.getAttribute('autocomplete') || '',
    placeholder: el.getAttribute('placeholder') || '',
    value: el.value || '',
    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
  }));
}
"""
    try:
        fields = page.evaluate(script)
    except Exception:
        fields = []
    visible = [f for f in fields if f.get('visible')]
    nonempty = [f for f in visible if str(f.get('value') or '').strip()]
    has_password = any((f.get('type') == 'password') and str(f.get('value') or '').strip() for f in visible)
    has_account = any(str(f.get('value') or '').strip() for f in visible if f.get('type') in {'text', 'email'} or 'mail' in (f.get('name') or '').lower() or 'user' in (f.get('name') or '').lower())
    return {
        'fields': visible,
        'nonempty_count': len(nonempty),
        'has_password_value': has_password,
        'has_account_value': has_account,
        'ready_to_submit': bool(has_password and has_account),
    }


def try_submit(page):
    logs = []
    candidates = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button',
        '[role="button"]',
    ]
    for selector in candidates:
        try:
            els = page.locator(selector)
            count = min(els.count(), 20)
            for i in range(count):
                el = els.nth(i)
                try:
                    text = (el.inner_text(timeout=1000) or '').strip()
                except Exception:
                    text = ''
                lower = text.lower()
                if text and any(k in lower for k in ['log in', 'login', 'sign in', 'continue', '登录']):
                    if el.is_visible(timeout=1000):
                        el.click(timeout=5000)
                        page.wait_for_timeout(8000)
                        logs.append({'selector': selector, 'text': text, 'clicked': True})
                        return True, logs
        except Exception as exc:
            logs.append({'selector': selector, 'clicked': False, 'error': str(exc)})
    return False, logs


def run_one(store_id: int, output_dir: Path, wait_seconds: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure = ensure_real_webdriver_detailed(
        store_id,
        startup_wait=90,
        reopen_once=True,
        reuse_existing_first=False,
        cooldown_seconds=4,
        backoff_seconds=4,
        stable_checks=2,
    )
    result = {
        'store_id': store_id,
        'ensure_real_webdriver': {
            'error': ensure.error,
            'used_reopen': ensure.used_reopen,
            'reused_existing': ensure.reused_existing,
        },
    }
    if not ensure.ready:
        result['status'] = 'webdriver_unavailable'
        return result

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(ensure.ready.ws_endpoint)
        page, best_score, click_result = pick_store_page(browser)
        if page is None:
            result['status'] = 'no_page'
            result['initial_pages'] = snapshot_browser_pages(browser)
            return result

        try:
            page.wait_for_load_state('domcontentloaded', timeout=15000)
        except Exception:
            pass

        pre_nav_url = page.url
        pre_nav_title = safe_page_title(page)
        pre_nav_body = safe_page_body(page, timeout=5000)
        pre_nav_kind = detect_page_kind(pre_nav_url, pre_nav_title, pre_nav_body)
        nav_result = None
        if best_score < 80 or pre_nav_kind not in {'dashboard', 'verification', 'login'}:
            nav_result = try_navigate_to_seller_home(page)
            try:
                page.wait_for_load_state('domcontentloaded', timeout=15000)
            except Exception:
                pass

        before_wait = inspect_fields(page)
        page.wait_for_timeout(wait_seconds * 1000)
        after_wait = inspect_fields(page)

        email_clicked, email_logs = (False, [])
        if not after_wait.get('ready_to_submit'):
            email_clicked, email_logs = try_click_email_switch(page)
            if email_clicked:
                page.wait_for_timeout(5000)
                after_wait = inspect_fields(page)

        submitted = False
        submit_logs = []
        if after_wait.get('ready_to_submit'):
            submitted, submit_logs = try_submit(page)

        page.wait_for_timeout(8000)
        body = safe_page_body(page, timeout=15000)
        title = safe_page_title(page)
        kind = detect_page_kind(page.url, title, body)
        lower_body = body.lower()

        shot_path = output_dir / f'store_{store_id}_after_retry.png'
        screenshot_error = ''
        try:
            page.screenshot(path=str(shot_path), full_page=True)
        except Exception as exc:
            screenshot_error = str(exc)

        result.update({
            'status': 'ok',
            'page_url': page.url,
            'page_title': title,
            'page_kind': kind,
            'login_hint_present': any(h in lower_body for h in LOGIN_HINTS),
            'verify_hint_present': any(h in lower_body for h in VERIFY_HINTS),
            'pre_navigation': {
                'url': pre_nav_url,
                'title': pre_nav_title,
                'page_kind': pre_nav_kind,
            },
            'navigation_attempt': nav_result,
            'open_store_click': click_result,
            'before_wait_fields': before_wait,
            'after_wait_fields': after_wait,
            'email_switch_clicked': email_clicked,
            'email_switch_logs': email_logs,
            'submitted': submitted,
            'submit_logs': submit_logs,
            'body_excerpt': '\n'.join([line.strip() for line in body.splitlines() if line.strip()][:50]),
            'screenshot_path': str(shot_path) if shot_path.exists() else '',
            'screenshot_error': screenshot_error,
            'final_pages': snapshot_browser_pages(browser),
        })
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description='Wait on login pages, try email login if autofill appears')
    parser.add_argument('--stores', nargs='+', type=int, required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--wait-seconds', type=int, default=25)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    browser_list = get_browser_list()
    meta_map = {int(item.get('mall_id', 0)): item for item in browser_list if item.get('mall_id')}

    results = []
    for store_id in args.stores:
        item = run_one(store_id, output_dir / f'store_{store_id}', args.wait_seconds)
        meta = meta_map.get(int(store_id), {})
        item['store_name'] = meta.get('mall_name', '')
        item['platform_name'] = meta.get('platform_name', '')
        results.append(item)
        print(json.dumps({
            'store_id': store_id,
            'status': item.get('status'),
            'page_kind': item.get('page_kind', ''),
            'ready_to_submit': (item.get('after_wait_fields') or {}).get('ready_to_submit', False),
            'submitted': item.get('submitted', False),
        }, ensure_ascii=False))

    summary_path = output_dir / 'summary.json'
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'ok', 'summary': str(summary_path), 'count': len(results)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
