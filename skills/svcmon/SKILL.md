---
name: svcmon
description: 对 Android APP 进行 syscall 行为监控与检测分析。当用户要求监控 APP、分析闪退、分析环境检测、反调试、反注入、反虚拟机行为时使用。触发词：svcmon, syscall 监控, 检测分析, 闪退监控, 行为分析, 反虚拟机, 反注入
---

# svcMonitor

**你只做一件事：spawn subagent。不要自己执行任何 bash 命令、不要自己分析、不要自己 adb。**

## 执行

立刻 spawn `re:svcMonitor-analyzer` subagent，prompt 里传：

```
包名: <用户给的包名或关键词>
preset: <re_basic 或根据用户意图选>
```

Preset 选择：
- 默认 / "分析检测/反调试/反注入" → `re_basic`
- "分析反虚拟机" → `re_full`

spawn 后等它返回，把结果原样输出给用户。

## 禁止

- 禁止自己跑 adb/bash/stackplz/svcMonitor 命令
- 禁止自己分析 trace
- 禁止自己改 HTML
- 你唯一要做的就是 spawn subagent + 输出结果
