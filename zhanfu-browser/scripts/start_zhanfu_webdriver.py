#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start ZhanFu in WebDriver mode, wait for API to be ready."""

import subprocess
import os
import sys
import glob
import time
import socket

HTTP_PORT = 45008
STARTUP_TIMEOUT = 30  # seconds to wait for port to open


def find_zhanfu_exe():
    """Find ZhanFu executable, checking known installation paths."""
    candidates = [
        r"C:\Program Files\ZhanFu\zhanfu.exe",
        r"C:\Program Files (x86)\ZhanFu\zhanfu.exe",
        r"C:\Users\9400\ZhanFu_5_2_88_portable\zhanfu.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    for pattern in [
        r"C:\Program Files\ZhanFu\*.exe",
        r"C:\Users\9400\ZhanFu*\zhanfu.exe",
    ]:
        files = glob.glob(pattern)
        for f in files:
            basename = os.path.basename(f)
            if "Uninstall" not in basename and not basename.startswith("uninstaller"):
                return f
    return None


def is_port_open(port, host="127.0.0.1"):
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        return True
    except OSError:
        return False


def wait_for_api(port, timeout=STARTUP_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(port):
            return True
        time.sleep(1)
    return False


def start_zhanfu_webdriver():
    """Start ZhanFu in WebDriver mode. Returns True if API is up."""
    exe = find_zhanfu_exe()
    if not exe:
        print(f"ERROR: Could not find ZhanFu executable", file=sys.stderr)
        return False
    print(f"Found executable: {exe}")

    if is_port_open(HTTP_PORT):
        print(f"Port {HTTP_PORT} already open — ZhanFu WebDriver API may already be running")
        return True

    print(f"Starting ZhanFu WebDriver mode on port {HTTP_PORT}...")
    args = [
        exe,
        "--multip",
        "--run_type=web_driver",
        "--ipc_type=http",
        f"--httpport={HTTP_PORT}",
    ]
    print(f"CMD: {' '.join(args)}")

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"Process started (PID={proc.pid}), waiting for API...")

    if wait_for_api(HTTP_PORT, timeout=STARTUP_TIMEOUT):
        print(f"SUCCESS: ZhanFu WebDriver API is up on port {HTTP_PORT}")
        return True

    # Capture any error output before terminating
    try:
        stdout, stderr = proc.communicate(timeout=5)
        err_output = (stdout + stderr).decode("utf-8", errors="replace")
    except Exception:
        err_output = "(could not read error output)"
    print(f"TIMEOUT: API did not respond on port {HTTP_PORT} after {STARTUP_TIMEOUT}s", file=sys.stderr)
    print(f"Process stderr/stdout: {err_output[:500]}", file=sys.stderr)
    proc.terminate()
    return False


if __name__ == "__main__":
    ok = start_zhanfu_webdriver()
    sys.exit(0 if ok else 1)
