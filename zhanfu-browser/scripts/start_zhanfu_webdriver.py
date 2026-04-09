#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start ZhanFu in WebDriver mode."""

import subprocess
import os
import sys
import glob
import time

# Find ZhanFu executable
patterns = [
    r'C:\Program Files\ZhanFu\*.exe',
    r'C:\Users\9400\ZhanFu_5_2_88_portable\*.exe',
]

exe_path = None
for pattern in patterns:
    files = glob.glob(pattern)
    for f in files:
        basename = os.path.basename(f)
        # Filter out uninstaller and other non-main executables
        if 'Uninstall' not in basename and not basename.startswith('uninstaller'):
            exe_path = f
            break
    if exe_path:
        break

if not exe_path:
    print("ERROR: Could not find ZhanFu executable")
    sys.exit(1)

print(f"Found executable: {exe_path}")

# Start ZhanFu in WebDriver mode
args = [
    exe_path,
    '--multip',
    '--run_type=web_driver',
    '--ipc_type=http',
    '--httpport=45008'
]

print(f"Starting with args: {args}")

proc = subprocess.Popen(
    args,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
)

print(f"Started process with PID: {proc.pid}")

# Wait and check if it's still running
time.sleep(3)

if proc.poll() is None:
    print("Process is running")
else:
    stdout, stderr = proc.communicate()
    print(f"Process exited with code: {proc.returncode}")
    print(f"stdout: {stdout}")
    print(f"stderr: {stderr}")
