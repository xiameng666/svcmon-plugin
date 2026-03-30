#!/usr/bin/env python3
"""extractso_export.py — pull APK + 解压 SO + IDA 全量导出。

用法:
  python extractso_export.py pull <package>                # 从设备 pull APK 并解压 arm64 SO
  python extractso_export.py ida <package> <so_name>       # 对指定 SO 做 IDA 导出

需要: ~/.reverse-plugin/config.json 中有 work_dir（pull）和 ida_path（ida）
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent


def load_config():
    cfg_path = Path.home() / ".reverse-plugin" / "config.json"
    if not cfg_path.is_file():
        print("ERROR=未初始化，请先运行 /re:init")
        sys.exit(1)
    return json.loads(cfg_path.read_text())


def adb_run(cmd, timeout=30):
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def resolve_package(keyword):
    """模糊匹配包名。返回完整包名或 None。"""
    # 先尝试精确匹配
    rc, out, _ = adb_run(["adb", "shell", f"pm list packages {keyword}"], timeout=10)
    if rc == 0:
        exact = [l.strip()[8:] for l in out.splitlines() if l.strip() == f"package:{keyword}"]
        if exact:
            return keyword

    # 模糊匹配
    rc, out, _ = adb_run(["adb", "shell", "pm list packages"], timeout=15)
    if rc != 0:
        return None
    matches = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            pkg = line[8:]
            if keyword.lower() in pkg.lower():
                matches.append(pkg)
    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]
    # 多个匹配，输出列表让 agent 选择
    print(f"MATCH_COUNT={len(matches)}")
    for i, m in enumerate(matches):
        print(f"MATCH={i}:{m}")
    return matches[0]  # 默认选第一个


def cmd_pull(args):
    """从设备 pull APK 并解压 arm64 SO 到 sessions/<pkg>/so/"""
    cfg = load_config()
    work_dir = Path(cfg["work_dir"])

    # Resolve package name (fuzzy match)
    package = resolve_package(args.package)
    if not package:
        print(f"ERROR=找不到匹配的包: {args.package}")
        sys.exit(1)
    if package != args.package:
        print(f"RESOLVED={package}")
    print(f"PACKAGE={package}")

    so_dir = work_dir / "sessions" / package / "so"

    # Check if already pulled
    if so_dir.exists():
        so_files = list(so_dir.glob("*.so"))
        if so_files:
            print(f"SO_DIR={so_dir}")
            print(f"SO_COUNT={len(so_files)}")
            for f in sorted(so_files):
                print(f"SO={f.name} ({f.stat().st_size // 1024}KB)")
            print("STATUS=EXISTS")
            return

    so_dir.mkdir(parents=True, exist_ok=True)

    # Find APK paths on device
    print(f"PHASE=finding APK for {package}...")
    rc, out, err = adb_run(["adb", "shell", f"su -c 'pm path {package}'"])
    if rc != 0:
        print(f"ERROR=pm path 失败: {err}")
        sys.exit(1)

    apk_paths = [l.strip()[8:] for l in out.splitlines() if l.strip().startswith("package:")]
    if not apk_paths:
        print(f"ERROR=pm path 返回为空")
        sys.exit(1)

    # Find arm64 split APK (preferred) or base APK
    target_apk = None
    for p in apk_paths:
        if "split_config.arm64" in p:
            target_apk = p
            break
    if not target_apk:
        for p in apk_paths:
            if "base.apk" in p:
                target_apk = p
                break
    if not target_apk:
        target_apk = apk_paths[0]

    apk_name = target_apk.rsplit("/", 1)[-1]
    local_apk = so_dir / apk_name
    print(f"APK_DEVICE={target_apk}")
    print(f"APK_LOCAL={local_apk}")

    # Pull APK
    print("PHASE=pulling APK...")
    rc, out, err = adb_run(["adb", "pull", target_apk, str(local_apk)], timeout=60)
    if rc != 0:
        print(f"ERROR=pull APK 失败: {err}")
        sys.exit(1)
    print(f"APK_SIZE={local_apk.stat().st_size // 1024}KB")

    # Extract arm64 SOs from APK (it's a zip)
    print("PHASE=extracting arm64 SOs...")
    extracted = []
    try:
        with zipfile.ZipFile(str(local_apk), "r") as zf:
            for entry in zf.namelist():
                # Match lib/arm64-v8a/*.so
                if entry.startswith("lib/arm64-v8a/") and entry.endswith(".so"):
                    so_name = entry.rsplit("/", 1)[-1]
                    target = so_dir / so_name
                    with zf.open(entry) as src, open(target, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(so_name)
                    print(f"SO={so_name} ({target.stat().st_size // 1024}KB)")
    except zipfile.BadZipFile:
        print(f"ERROR=APK 不是有效的 zip 文件")
        sys.exit(1)

    if not extracted:
        print("WARN=APK 中没有找到 arm64 SO，尝试 base.apk...")
        # Try base.apk if split didn't have SOs
        for p in apk_paths:
            if "base.apk" in p and p != target_apk:
                base_local = so_dir / "base.apk"
                rc, _, _ = adb_run(["adb", "pull", p, str(base_local)], timeout=60)
                if rc == 0:
                    try:
                        with zipfile.ZipFile(str(base_local), "r") as zf:
                            for entry in zf.namelist():
                                if entry.startswith("lib/arm64-v8a/") and entry.endswith(".so"):
                                    so_name = entry.rsplit("/", 1)[-1]
                                    target = so_dir / so_name
                                    with zf.open(entry) as src, open(target, "wb") as dst:
                                        dst.write(src.read())
                                    extracted.append(so_name)
                                    print(f"SO={so_name} ({target.stat().st_size // 1024}KB)")
                    except zipfile.BadZipFile:
                        pass
                break

    print(f"SO_DIR={so_dir}")
    print(f"SO_COUNT={len(extracted)}")
    print("STATUS=OK")


def find_package_dir(sessions_dir, keyword):
    """在 sessions 目录中模糊查找包名目录。"""
    exact = sessions_dir / keyword / "so"
    if exact.exists():
        return keyword, exact
    # Fuzzy match on directory names
    for d in sessions_dir.iterdir():
        if d.is_dir() and keyword.lower() in d.name.lower():
            so = d / "so"
            if so.exists():
                return d.name, so
    return None, None


def cmd_ida(args):
    """对指定 SO 做 IDA 全量导出"""
    cfg = load_config()
    work_dir = Path(cfg["work_dir"])
    sessions_dir = work_dir / "sessions"

    # Find package directory (fuzzy match on local dirs)
    package, so_dir = find_package_dir(sessions_dir, args.package)
    if not package:
        print(f"ERROR=找不到包目录: {args.package}")
        print(f"HINT=请先运行: /re:extractSo {args.package}")
        sys.exit(1)
    if package != args.package:
        print(f"RESOLVED={package}")
    print(f"PACKAGE={package}")

    # Check IDA
    ida_path = cfg.get("ida_path", "")
    if not ida_path:
        print("ERROR=未配置 IDA 路径，请运行 /re:init 配置")
        sys.exit(1)

    ida_dir = Path(ida_path)
    idat_exe = None
    for name in ["idat64.exe", "idat64", "idat.exe", "idat"]:
        candidate = ida_dir / name
        if candidate.exists():
            idat_exe = str(candidate)
            break
    if not idat_exe:
        print(f"ERROR=在 {ida_dir} 中找不到 idat64/idat")
        sys.exit(1)

    # Check IDA scripts
    router_src = SCRIPTS_DIR / "ida_run.py"
    export_script = SCRIPTS_DIR / "ida_full_export.py"
    if not router_src.exists() or not export_script.exists():
        print("ERROR=缺少 IDA 脚本 (ida_run.py / ida_full_export.py)")
        sys.exit(1)

    # Find SOs to export
    if not so_dir.exists():
        print(f"ERROR=SO 目录不存在: {so_dir}")
        print("HINT=请先运行: python extractso_export.py pull <package>")
        sys.exit(1)

    all_sos = sorted(so_dir.glob("*.so"))
    if not all_sos:
        print(f"ERROR=SO 目录为空: {so_dir}")
        sys.exit(1)

    # Find matching SO
    matches = [s for s in all_sos if args.so_name in s.stem]
    if not matches:
        print(f"ERROR=找不到匹配的 SO: {args.so_name}")
        print(f"可用 SO: {', '.join(s.name for s in all_sos)}")
        sys.exit(1)
    targets = matches

    print(f"IDA={idat_exe}")
    print(f"TARGETS={len(targets)}")

    for so_path in targets:
        so_stem = so_path.stem
        export_dir = work_dir / "sessions" / package / f"static_{so_stem}"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Check if already exported
        summary_file = export_dir / "summary.json"
        if summary_file.exists():
            summary = json.loads(summary_file.read_text())
            disasm_count = len(list((export_dir / "disasm").glob("*.asm"))) if (export_dir / "disasm").exists() else 0
            print(f"SKIP={so_stem} (已导出, {disasm_count} 函数, {summary.get('elapsed_seconds', '?')}s)")
            continue

        print(f"EXPORT={so_stem}...")
        print(f"OUTPUT_DIR={export_dir}")

        # Copy router to temp
        tmp_router = Path(tempfile.gettempdir()) / "ida_bridge_run.py"
        shutil.copy2(router_src, tmp_router)

        cmd = f'"{idat_exe}" -A -S"{tmp_router}" "{so_path}"'
        env = os.environ.copy()
        env["IDA_BRIDGE_SCRIPT"] = "full_export"
        env["IDA_BRIDGE_ARGS"] = json.dumps([str(export_dir)])
        env["IDA_BRIDGE_SCRIPT_DIR"] = str(SCRIPTS_DIR)

        start = time.time()
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=600, cwd=str(so_path.parent), env=env
            )
            elapsed = time.time() - start
            print(f"ELAPSED={elapsed:.1f}s")

            if result.returncode != 0 and not summary_file.exists():
                print(f"WARN={so_stem} 导出失败 (exit={result.returncode})")
                continue

        except subprocess.TimeoutExpired:
            print(f"WARN={so_stem} 导出超时 (>600s)")
            continue

        # Count results
        disasm_count = len(list((export_dir / "disasm").glob("*.asm"))) if (export_dir / "disasm").exists() else 0
        decomp_count = len(list((export_dir / "decompiled").glob("*.c"))) if (export_dir / "decompiled").exists() else 0
        print(f"DONE={so_stem} (函数: {disasm_count}, 反编译: {decomp_count})")

    print("STATUS=OK")


def main():
    parser = argparse.ArgumentParser(description="extractSo — pull APK + extract SO + IDA export")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pull = sub.add_parser("pull", help="从设备 pull APK 并解压 arm64 SO")
    p_pull.add_argument("package", help="包名")

    p_ida = sub.add_parser("ida", help="对 SO 做 IDA 全量导出")
    p_ida.add_argument("package", help="包名")
    p_ida.add_argument("so_name", help="SO 名称（模糊匹配）")

    args = parser.parse_args()
    if args.command == "pull":
        cmd_pull(args)
    elif args.command == "ida":
        cmd_ida(args)


if __name__ == "__main__":
    main()
