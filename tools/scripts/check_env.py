#!/usr/bin/env python3
"""检查 svcMonitor 运行环境。输出 KEY=VALUE 格式。"""
import json, os, subprocess, sys
from pathlib import Path

def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return -1, ""

# Config
cfg_path = Path.home() / ".reverse-plugin" / "config.json"
if not cfg_path.is_file():
    print("STATUS=NOT_INITIALIZED")
    print("ERROR=请先运行 /re:init")
    sys.exit(1)

cfg = json.loads(cfg_path.read_text())
work_dir = cfg.get("work_dir", "")
if not work_dir:
    print("STATUS=NOT_INITIALIZED")
    print("ERROR=工作目录未设置，请先运行 /re:init")
    sys.exit(1)

work_dir = Path(work_dir)
stackplz_local = work_dir / ".config" / "stackplz"
sessions_dir = work_dir / "sessions"

print(f"WORK_DIR={work_dir}")
print(f"SESSIONS_DIR={sessions_dir}")
print(f"STACKPLZ_LOCAL={stackplz_local}")
print(f"STACKPLZ_LOCAL_EXISTS={stackplz_local.is_file()}")

# svcMonitor CLI
rc, out = run(["svcMonitor", "--help"])
print(f"CLI={'ok' if rc == 0 else 'missing'}")

# Device
env = os.environ.copy()
env["MSYS_NO_PATHCONV"] = "1"
rc, out = run(["adb", "devices", "-l"])
device = "disconnected"
model = ""
for line in out.splitlines():
    if "device product:" in line:
        device = "connected"
        for p in line.split():
            if p.startswith("model:"):
                model = p.split(":", 1)[1]
        break
print(f"DEVICE={device}")
if model:
    print(f"MODEL={model}")

# stackplz on device
rc, out = run(["adb", "shell", "su -c 'ls /data/local/tmp/re/stackplz'"])
print(f"STACKPLZ_DEVICE={'ok' if rc == 0 and 'stackplz' in out else 'missing'}")

print("STATUS=OK")
