#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

API_URL = "http://127.0.0.1:45008"


@dataclass
class WebDriverReady:
    port: int
    kernel_number: str | None
    ws_endpoint: str
    version_payload: dict[str, Any]


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


def fetch_version_endpoint(port: int) -> tuple[dict[str, Any] | None, str]:
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        return fetch_json(url, timeout=8), ""
    except Exception as exc:
        return None, str(exc)


def wait_for_real_webdriver(browser_id: int | str, timeout_seconds: int = 90, poll_seconds: int = 2) -> tuple[WebDriverReady | None, str]:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            response = get_browser_webdriver(browser_id)
            info = response.get("returnObj") or {}
            port = int(info.get("WebDriverPort") or 0)
            kernel = info.get("KernalNumber")
            if port:
                version_data, version_error = fetch_version_endpoint(port)
                if version_data:
                    ws = version_data.get("webSocketDebuggerUrl", "")
                    if ws:
                        return WebDriverReady(port=port, kernel_number=kernel, ws_endpoint=ws, version_payload=version_data), ""
                last_error = version_error
                if is_proxy_auth_error(version_error):
                    return None, version_error
        except Exception as exc:
            last_error = str(exc)
        time.sleep(poll_seconds)
    return None, last_error or "webdriver startup timeout"


def ensure_real_webdriver(browser_id: int | str, startup_wait: int = 90, reopen_once: bool = True) -> tuple[WebDriverReady | None, str]:
    ready, error = wait_for_real_webdriver(browser_id, timeout_seconds=startup_wait)
    if ready:
        return ready, ""

    if reopen_once:
        try:
            close_browser(browser_id)
            time.sleep(3)
        except Exception:
            pass
        try:
            open_browser(browser_id)
        except Exception as exc:
            return None, f"reopen failed: {exc}"
        return wait_for_real_webdriver(browser_id, timeout_seconds=startup_wait)

    return None, error
