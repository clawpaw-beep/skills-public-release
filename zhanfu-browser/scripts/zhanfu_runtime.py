#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import random
import socket
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from DrissionPage import Chromium

API_URL = "http://127.0.0.1:45008"

# ---------------------------------------------------------------------------
# CDP Port Discovery (新版本动态端口)
# ---------------------------------------------------------------------------

def find_cdp(timeout: float = 15.0) -> tuple[int | None, list[dict[str, Any]]]:
    """
    扫描 12620-12640 范围，发现第一个有 targets 的 CDP 端口。
    OpenBrowser 后需等待 5-10 秒再调用此函数。

    Args:
        timeout: 最大扫描时间（秒）

    Returns:
        (port, targets) — 找到则返回端口号和 targets 列表；未找到则返回 (None, [])
    """
    start = time.time()
    while time.time() - start < timeout:
        for port in range(12620, 12660):
            try:
                url = f"http://127.0.0.1:{port}/json"
                r = urllib.request.urlopen(url, timeout=2)
                targets = json.loads(r.read().decode("utf-8"))
                if targets:
                    return port, targets
            except Exception:
                pass
        time.sleep(2)
    return None, []


def find_cdp_or_raise(timeout: float = 15.0) -> tuple[int, list[dict[str, Any]]]:
    """find_cdp 的强验证版；未找到则抛出异常。"""
    port, targets = find_cdp(timeout=timeout)
    if port is None:
        raise RuntimeError(
            f"CDP port not found after {timeout}s. "
            "Ensure OpenBrowser was called and wait 5-10s before retry."
        )
    return port, targets


@dataclass
class WebDriverReady:
    port: int
    kernel_number: str | None
    ws_endpoint: str
    version_payload: dict[str, Any]


@dataclass
class WebDriverAttempt:
    attempt: int
    phase: str
    ok: bool
    port: int | None = None
    ws_endpoint: str | None = None
    error: str = ""
    waited_seconds: float = 0.0
    version_checks: int = 0
    reused_existing: bool = False
    reopened_browser: bool = False
    open_response_ret: int | None = None
    close_response_ret: int | None = None
    version_payload: dict[str, Any] | None = None


@dataclass
class WebDriverEnsureResult:
    ready: WebDriverReady | None
    error: str
    attempts: list[WebDriverAttempt]
    used_reopen: bool = False
    reused_existing: bool = False


@dataclass
class TabSnapshot:
    index: int
    url: str
    title: str
    page_kind: str
    score: int
    body_excerpt: str


SELLER_HOST_HINTS = [
    "seller.us.tiktokshopglobalselling.com",
    "seller.tiktokshopglobalselling.com",
    "seller-us.tiktok.com",
    "affiliate.tiktokshopglobalselling.com",
]
DEFAULT_SELLER_HOME_URLS = [
    "https://seller.us.tiktokshopglobalselling.com/homepage?shop_region=US",
    "https://seller.tiktokshopglobalselling.com/homepage",
    "https://seller-us.tiktok.com/homepage",
]
LOGIN_HINTS = ["login", "登录", "sign in", "sign-in", "log in"]
VERIFY_HINTS = ["验证", "captcha", "安全验证", "verify", "verification", "security check"]
ZHANFU_EXTENSION_HINTS = ["站斧浏览器", "打开店铺", "设备安全检测", "环境安全检测", "线路优化检测", "当前环境检测安全"]
SHELL_ONLY_HINTS = ["seller center", "powered by ai", "customer messages", "in progress", "ask anything"]
BUSINESS_DATA_HINTS = ["经营数据", "GMV", "订单数", "页面浏览数", "平均访客数", "数据分析"]


def post(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: int = 5) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_json(url: str, timeout: int = 5) -> dict[str, Any]:
    return json.loads(fetch_text(url, timeout=timeout))


def get_browser_list() -> list[dict[str, Any]]:
    response = post(
        {
            "action": "GetBrowserList",
            "module": "WebDriverModule",
            "args": '{"page":1,"limit":200}',
        }
    )
    data = (((response or {}).get("returnObj") or {}).get("data") or {}).get("mall_list") or []
    return data


def open_browser(browser_id: int | str) -> dict[str, Any]:
    return post(
        {
            "action": "OpenBrowser",
            "module": "WebDriverModule",
            "browserId": str(browser_id),
        }
    )


def close_browser(browser_id: int | str) -> dict[str, Any]:
    return post(
        {
            "action": "CloseBrowser",
            "module": "WebDriverModule",
            "args": "",
            "browserId": str(browser_id),
        }
    )


def get_browser_webdriver(browser_id: int | str) -> dict[str, Any]:
    return post(
        {
            "action": "GetBrowserWebDriver",
            "module": "WebDriverModule",
            "args": "",
            "browserId": str(browser_id),
        }
    )


def is_proxy_auth_error(text: str) -> bool:
    lower = (text or "").lower()
    return "407" in lower or "proxy authentication required" in lower


def is_connection_error(text: str) -> bool:
    lower = (text or "").lower()
    return "10061" in lower or "connection refused" in lower or "cannot connect" in lower


def is_port_open(port: int, timeout: float = 1.5) -> bool:
    if not port:
        return False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(("127.0.0.1", int(port)))
        return True
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def fetch_version_endpoint(port: int) -> tuple[dict[str, Any] | None, str]:
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        return fetch_json(url, timeout=8), ""
    except Exception as exc:
        return None, str(exc)


def _version_payload_has_real_ws(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    ws = str(payload.get("webSocketDebuggerUrl") or "").strip()
    if not ws.startswith("ws://"):
        return ""
    browser = str(payload.get("Browser") or "")
    if not browser:
        return ""
    return ws


def wait_for_real_webdriver_detailed(
    browser_id: int | str,
    timeout_seconds: int = 90,
    poll_seconds: int = 2,
    require_stable_checks: int = 2,
) -> tuple[WebDriverReady | None, str, WebDriverAttempt]:
    started = time.time()
    deadline = started + timeout_seconds
    last_error = ""
    version_checks = 0
    stable_hits = 0
    last_port = 0
    last_kernel = None
    last_payload: dict[str, Any] | None = None
    last_ws = ""

    while time.time() < deadline:
        try:
            response = get_browser_webdriver(browser_id)
            info = response.get("returnObj") or {}
            port = int(info.get("WebDriverPort") or 0)
            kernel = info.get("KernalNumber")
            last_port = port
            last_kernel = kernel
            if port:
                if not is_port_open(port):
                    stable_hits = 0
                    last_error = f"webdriver port {port} not accepting tcp yet"
                else:
                    version_data, version_error = fetch_version_endpoint(port)
                    version_checks += 1
                    if version_data:
                        ws = _version_payload_has_real_ws(version_data)
                        if ws:
                            last_payload = version_data
                            last_ws = ws
                            stable_hits += 1
                            if stable_hits >= max(1, require_stable_checks):
                                attempt = WebDriverAttempt(
                                    attempt=1,
                                    phase="wait_for_real_webdriver",
                                    ok=True,
                                    port=port,
                                    ws_endpoint=ws,
                                    waited_seconds=round(time.time() - started, 2),
                                    version_checks=version_checks,
                                    version_payload=version_data,
                                )
                                return WebDriverReady(port=port, kernel_number=kernel, ws_endpoint=ws, version_payload=version_data), "", attempt
                        else:
                            stable_hits = 0
                            last_error = "webdriver version endpoint missing real webSocketDebuggerUrl"
                    else:
                        stable_hits = 0
                        last_error = version_error
                        if is_proxy_auth_error(version_error):
                            attempt = WebDriverAttempt(
                                attempt=1,
                                phase="wait_for_real_webdriver",
                                ok=False,
                                port=port,
                                error=version_error,
                                waited_seconds=round(time.time() - started, 2),
                                version_checks=version_checks,
                            )
                            return None, version_error, attempt
        except Exception as exc:
            stable_hits = 0
            last_error = str(exc)
        time.sleep(poll_seconds)

    attempt = WebDriverAttempt(
        attempt=1,
        phase="wait_for_real_webdriver",
        ok=False,
        port=last_port or None,
        ws_endpoint=last_ws or None,
        error=last_error or "webdriver startup timeout",
        waited_seconds=round(time.time() - started, 2),
        version_checks=version_checks,
        version_payload=last_payload,
    )
    return None, last_error or "webdriver startup timeout", attempt


def wait_for_real_webdriver(browser_id: int | str, timeout_seconds: int = 90, poll_seconds: int = 2) -> tuple[WebDriverReady | None, str]:
    ready, error, _attempt = wait_for_real_webdriver_detailed(
        browser_id,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    return ready, error


def ensure_real_webdriver_detailed(
    browser_id: int | str,
    startup_wait: int = 90,
    reopen_once: bool = True,
    reuse_existing_first: bool = True,
    cooldown_seconds: float = 3.0,
    backoff_seconds: float = 4.0,
    stable_checks: int = 2,
) -> WebDriverEnsureResult:
    attempts: list[WebDriverAttempt] = []
    last_error = ""

    if reuse_existing_first:
        ready, error, detail = wait_for_real_webdriver_detailed(
            browser_id,
            timeout_seconds=min(max(20, startup_wait // 2), startup_wait),
            poll_seconds=2,
            require_stable_checks=stable_checks,
        )
        detail.attempt = len(attempts) + 1
        detail.phase = "reuse_existing"
        detail.reused_existing = True
        attempts.append(detail)
        if ready:
            return WebDriverEnsureResult(ready=ready, error="", attempts=attempts, reused_existing=True)
        last_error = error

    open_ret = None
    try:
        open_response = open_browser(browser_id)
        open_ret = int(open_response.get("ret")) if open_response.get("ret") is not None else None
    except Exception as exc:
        open_response = {"ret": None, "error": str(exc)}
        last_error = str(exc)

    ready, error, detail = wait_for_real_webdriver_detailed(
        browser_id,
        timeout_seconds=startup_wait,
        poll_seconds=2,
        require_stable_checks=stable_checks,
    )
    detail.attempt = len(attempts) + 1
    detail.phase = "open_then_wait"
    detail.open_response_ret = open_ret
    attempts.append(detail)
    if ready:
        return WebDriverEnsureResult(ready=ready, error="", attempts=attempts, reused_existing=False)
    last_error = error or last_error

    if reopen_once:
        close_ret = None
        try:
            close_response = close_browser(browser_id)
            close_ret = int(close_response.get("ret")) if close_response.get("ret") is not None else None
        except Exception as exc:
            close_ret = None
            last_error = last_error or f"close before reopen failed: {exc}"
        time.sleep(max(0.0, cooldown_seconds))
        time.sleep(random.uniform(0.2, 0.8))
        second_open_ret = None
        try:
            second_open_response = open_browser(browser_id)
            second_open_ret = int(second_open_response.get("ret")) if second_open_response.get("ret") is not None else None
        except Exception as exc:
            last_error = f"reopen failed: {exc}"
        time.sleep(max(0.0, backoff_seconds))
        ready, error, detail = wait_for_real_webdriver_detailed(
            browser_id,
            timeout_seconds=max(45, startup_wait),
            poll_seconds=2,
            require_stable_checks=stable_checks,
        )
        detail.attempt = len(attempts) + 1
        detail.phase = "reopen_then_wait"
        detail.reopened_browser = True
        detail.open_response_ret = second_open_ret
        detail.close_response_ret = close_ret
        attempts.append(detail)
        if ready:
            return WebDriverEnsureResult(ready=ready, error="", attempts=attempts, used_reopen=True)
        last_error = error or last_error

    return WebDriverEnsureResult(ready=None, error=last_error or "webdriver unavailable", attempts=attempts)


def ensure_real_webdriver(browser_id: int | str, startup_wait: int = 90, reopen_once: bool = True) -> tuple[WebDriverReady | None, str]:
    result = ensure_real_webdriver_detailed(browser_id, startup_wait=startup_wait, reopen_once=reopen_once)
    return result.ready, result.error


def ensure_result_to_dict(result: WebDriverEnsureResult) -> dict[str, Any]:
    return {
        "ready": asdict(result.ready) if result.ready else None,
        "error": result.error,
        "used_reopen": result.used_reopen,
        "reused_existing": result.reused_existing,
        "attempts": [asdict(item) for item in result.attempts],
    }


def connect_browser(port: int) -> Chromium:
    return Chromium(addr_or_opts=f"127.0.0.1:{port}")


def tab_body_text(tab) -> str:
    try:
        return tab.run_js("return document.body ? document.body.innerText : ''") or ""
    except Exception:
        return ""


def tab_title(tab) -> str:
    try:
        return tab.title or ""
    except Exception:
        return ""


def tab_url(tab) -> str:
    try:
        return tab.url or ""
    except Exception:
        return ""


def classify_page(url: str, title: str, body: str) -> str:
    lower_url = (url or "").lower()
    lower_title = (title or "").lower()
    lower_body = (body or "").lower()
    if any(hint.lower() in lower_title for hint in ZHANFU_EXTENSION_HINTS) or any(hint.lower() in lower_body for hint in ZHANFU_EXTENSION_HINTS):
        return "zhanfu_extension"
    if not lower_url or lower_url.startswith("chrome-extension://") or lower_url.startswith("chrome://"):
        return "extension_or_empty"
    if any(hint in lower_url for hint in ["login", "signin", "sign-in"]) or any(hint in lower_body for hint in LOGIN_HINTS):
        return "login"
    if any(hint in lower_body for hint in VERIFY_HINTS):
        return "verification"
    if any(hint.lower() in lower_body for hint in [item.lower() for item in BUSINESS_DATA_HINTS]):
        return "dashboard"
    if any(host in lower_url for host in SELLER_HOST_HINTS):
        if "seller-us.tiktok.com/homepage" in lower_url and not any(hint.lower() in lower_body for hint in [item.lower() for item in BUSINESS_DATA_HINTS]):
            return "seller_shell"
        if any(hint.lower() in lower_body for hint in [item.lower() for item in SHELL_ONLY_HINTS]):
            return "seller_shell"
        return "seller_page"
    return "other"


def score_tab(tab) -> int:
    url = tab_url(tab).lower()
    title = tab_title(tab)
    body = tab_body_text(tab)
    page_kind = classify_page(url, title, body)
    if page_kind in {"extension_or_empty", "zhanfu_extension"}:
        return -999 if page_kind == "extension_or_empty" else -200
    score = 0
    if any(host in url for host in SELLER_HOST_HINTS):
        score += 50
    if page_kind == "dashboard":
        score += 120
    elif page_kind == "seller_page":
        score += 50
    elif page_kind == "seller_shell":
        score += 20
    elif page_kind == "login":
        score -= 40
    elif page_kind == "verification":
        score -= 20
    if "redirect_url=" in url and page_kind == "login":
        score -= 10
    return score


def snapshot_tabs(browser: Chromium, excerpt_lines: int = 20) -> list[TabSnapshot]:
    snapshots: list[TabSnapshot] = []
    for idx, tab in enumerate(browser.get_tabs()):
        body = tab_body_text(tab)
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        url = tab_url(tab)
        title = tab_title(tab)
        page_kind = classify_page(url, title, body)
        snapshots.append(
            TabSnapshot(
                index=idx,
                url=url,
                title=title,
                page_kind=page_kind,
                score=score_tab(tab),
                body_excerpt="\n".join(lines[:excerpt_lines]),
            )
        )
    return snapshots


def snapshot_tabs_dict(browser: Chromium, excerpt_lines: int = 20) -> list[dict[str, Any]]:
    return [asdict(item) for item in snapshot_tabs(browser, excerpt_lines=excerpt_lines)]


def pick_best_tab(browser: Chromium):
    best_tab = None
    best_score = -999
    for tab in browser.get_tabs():
        current = score_tab(tab)
        if current > best_score:
            best_tab = tab
            best_score = current
    return best_tab, best_score


def open_store_from_extension_if_needed(browser: Chromium) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    clicked = False
    for idx, tab in enumerate(browser.get_tabs()):
        body = tab_body_text(tab)
        url = tab_url(tab)
        title = tab_title(tab)
        if classify_page(url, title, body) != "zhanfu_extension":
            continue
        try:
            ele = tab.ele("text:打开店铺", timeout=3)
            if ele:
                ele.click()
                time.sleep(3)
                clicked = True
                actions.append({"index": idx, "url": url, "title": title, "clicked": True})
            else:
                actions.append({"index": idx, "url": url, "title": title, "clicked": False, "error": "button not found"})
        except Exception as exc:
            actions.append({"index": idx, "url": url, "title": title, "clicked": False, "error": str(exc)})
    return {"clicked": clicked, "actions": actions}


def goto_seller_home_if_needed(browser: Chromium, wait_seconds: float = 12.0) -> dict[str, Any]:
    tab, score = pick_best_tab(browser)
    if tab is None:
        return {"ok": False, "error": "no tabs available", "target": DEFAULT_SELLER_HOME_URLS[0]}
    current_kind = classify_page(tab_url(tab), tab_title(tab), tab_body_text(tab))
    if current_kind == "dashboard":
        return {"ok": True, "skipped": True, "reason": "already on dashboard page", "url": tab_url(tab)}
    if current_kind == "seller_page" and score >= 90:
        return {"ok": True, "skipped": True, "reason": "already on seller business page", "url": tab_url(tab)}
    errors = []
    for url in DEFAULT_SELLER_HOME_URLS:
        try:
            tab.get(url)
            time.sleep(wait_seconds)
            body = tab_body_text(tab)
            return {
                "ok": True,
                "target": url,
                "url": tab_url(tab),
                "title": tab_title(tab),
                "page_kind": classify_page(tab_url(tab), tab_title(tab), body),
                "body_length": len(body),
            }
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    return {"ok": False, "target": DEFAULT_SELLER_HOME_URLS[0], "error": " | ".join(errors)}


def wait_for_business_tab(browser: Chromium, timeout_seconds: float = 45.0, poll_seconds: float = 5.0) -> dict[str, Any]:
    started = time.time()
    history: list[dict[str, Any]] = []
    while time.time() - started < timeout_seconds:
        best_tab, best_score = pick_best_tab(browser)
        body = tab_body_text(best_tab) if best_tab else ""
        page_kind = classify_page(tab_url(best_tab), tab_title(best_tab), body) if best_tab else "none"
        snap = {
            "elapsed": round(time.time() - started, 1),
            "score": best_score,
            "page_kind": page_kind,
            "url": tab_url(best_tab) if best_tab else "",
            "title": tab_title(best_tab) if best_tab else "",
            "body_length": len(body),
            "has_business_data": any(hint.lower() in body.lower() for hint in [item.lower() for item in BUSINESS_DATA_HINTS]),
        }
        history.append(snap)
        if snap["has_business_data"] or page_kind in {"dashboard", "seller_page"} and len(body) > 2500:
            return {"ok": True, "history": history, "final": snap}
        time.sleep(poll_seconds)
    return {"ok": False, "history": history, "final": history[-1] if history else {}}


def diagnose_store_entry(browser: Chromium, try_open_store: bool = True, try_goto_home: bool = True) -> dict[str, Any]:
    before = snapshot_tabs_dict(browser)
    open_store_result = {"clicked": False, "actions": []}
    if try_open_store:
        open_store_result = open_store_from_extension_if_needed(browser)
    if open_store_result.get("clicked"):
        time.sleep(8)
    navigation_result = {"ok": False, "skipped": True, "reason": "disabled"}
    if try_goto_home:
        navigation_result = goto_seller_home_if_needed(browser)
    business_wait = wait_for_business_tab(browser, timeout_seconds=60.0, poll_seconds=5.0)
    after = snapshot_tabs_dict(browser)
    best_tab, best_score = pick_best_tab(browser)
    return {
        "before_tabs": before,
        "open_store": open_store_result,
        "navigation": navigation_result,
        "business_wait": business_wait,
        "after_tabs": after,
        "best_tab": {
            "url": tab_url(best_tab) if best_tab else "",
            "title": tab_title(best_tab) if best_tab else "",
            "score": best_score,
            "page_kind": classify_page(tab_url(best_tab), tab_title(best_tab), tab_body_text(best_tab)) if best_tab else "none",
            "body_length": len(tab_body_text(best_tab)) if best_tab else 0,
        },
    }


# ---------------------------------------------------------------------------
# ZhanFu lifecycle management (robust startup)
# ---------------------------------------------------------------------------

import os as _os
import subprocess as _subprocess

# 新版本优先使用安装路径（英文），老版本便携作为备用
_ZHANFU_EXE_PRIMARY = r"C:\Program Files\ZhanFu\zhanfu.exe"
_ZHANFU_EXE_FALLBACK = _os.path.expandvars(
    r"%USERPROFILE%\\ZhanFu_5_2_88_portable\\站斧.exe"
)


def get_zhanfu_exe() -> str | None:
    """返回当前机器上可用的站斧可执行文件路径。"""
    if _os.path.exists(_ZHANFU_EXE_PRIMARY):
        return _ZHANFU_EXE_PRIMARY
    if _os.path.exists(_ZHANFU_EXE_FALLBACK):
        return _ZHANFU_EXE_FALLBACK
    return None


def kill_zhanfu() -> int:
    """Kill all ZhanFu processes. Returns number of processes killed."""
    try:
        result = _subprocess.run(
            ["taskkill", "/F", "/IM", "վ��.exe"],
            capture_output=True,
            timeout=10,
        )
        output = result.stdout.decode("utf-8", errors="replace")
        return output.count("SUCCESS")
    except Exception:
        return 0


def start_zhanfu(port: int = 45008, exe: str | None = None) -> bool:
    """Start ZhanFu in WebDriver mode. Returns True if started successfully."""
    if exe is None:
        exe = get_zhanfu_exe()
    if exe is None:
        return False
    args = [
        exe,
        "--multip",
        "--run_type=web_driver",
        "--ipc_type=http",
        f"--httpport={port}",
    ]
    try:
        _subprocess.Popen(args, shell=False)
        return True
    except Exception:
        return False


def is_api_ready() -> bool:
    """Check if ZhanFu HTTP API is responding (non-error response)."""
    try:
        stores = get_browser_list()
        return stores is not None
    except Exception:
        return False


def wait_for_api_ready(max_wait: float = 60, poll_interval: float = 2) -> tuple[bool, float]:
    """Wait for ZhanFu HTTP API to respond. Returns (success, elapsed_seconds)."""
    started = time.time()
    while time.time() - started < max_wait:
        if is_api_ready():
            return True, round(time.time() - started, 1)
        time.sleep(poll_interval)
    return False, round(time.time() - started, 1)


def ensure_zhanfu_ready(
    browser_id: int | str,
    startup_wait: float = 60,
    cdp_wait: float = 90,
    kill_first: bool = False,
) -> WebDriverEnsureResult:
    """Robust ZhanFu startup: ensures HTTP API is up, then opens browser and waits for CDP.

    Steps:
      1. Optionally kill existing ZhanFu processes
      2. Start ZhanFu in WebDriver mode
      3. Poll HTTP API until it responds
      4. Call ensure_real_webdriver_detailed to open browser and wait for CDP

    Args:
        browser_id: mall_id to open
        startup_wait: max seconds to wait for ZhanFu HTTP API to come up
        cdp_wait: max seconds to wait for CDP endpoint after opening browser
        kill_first: if True, kill ZhanFu before starting (clean slate)

    Returns:
        WebDriverEnsureResult — result.ready is None on failure
    """
    # Step 1: kill / start
    if kill_first:
        kill_zhanfu()
        time.sleep(2)

    if not is_api_ready():
        if not start_zhanfu():
            return WebDriverEnsureResult(
                ready=None,
                error="failed to start ZhanFu",
                attempts=[],
            )
        ok, elapsed = wait_for_api_ready(max_wait=startup_wait)
        if not ok:
            return WebDriverEnsureResult(
                ready=None,
                error=f"ZhanFu HTTP API not ready after {elapsed}s",
                attempts=[],
            )

    # Step 2: open browser + wait for CDP
    return ensure_real_webdriver_detailed(
        browser_id,
        startup_wait=cdp_wait,
        reopen_once=True,
        reuse_existing_first=True,
        cooldown_seconds=3.0,
        backoff_seconds=4.0,
        stable_checks=2,
    )


def ensure_store_connected(browser_id: int | str) -> WebDriverEnsureResult:
    """Alias for ensure_zhanfu_ready with sensible defaults for this machine."""
    return ensure_zhanfu_ready(browser_id, startup_wait=60, cdp_wait=90, kill_first=False)
