---
description: "从设备 pull APK 并解压所有 arm64 SO 到 session 目录。支持模糊包名。"
argument-hint: "<package_name>"
---

依次执行：

1. 确定脚本路径：
```bash
SCRIPTS=$(python -c "from pathlib import Path; import glob; dirs=glob.glob(str(Path.home()/'.claude/plugins/cache/reverse-plugin/re/*/tools/scripts/')); print(dirs[0] if dirs else 'E:/_github/reverse-plugin/tools/scripts')")
```

2. 检查环境：
```bash
python "$SCRIPTS/check_env.py"
```
DEVICE=disconnected → 告诉用户连接设备，停止。
STATUS=NOT_INITIALIZED → 告诉用户跑 `/re:init`，停止。

3. Pull APK + 解压 SO：
```bash
python "$SCRIPTS/extractso_export.py" pull "<用户给的包名>"
```

4. 把结果输出给用户。关注：
- RESOLVED= 行表示做了模糊匹配，告诉用户实际包名
- SO= 行列出所有解压出的 SO
- STATUS=EXISTS 表示已经 pull 过了
- STATUS=OK 表示新 pull 成功

输出格式：
```
包名: <实际包名>
SO 目录: <路径>
SO 文件:
  - <name> (<size>)
  ...

下一步:
  /re:extractSo <包名> <so_name>  IDA 导出
  /re:svcmon <包名>               动态监控
```
