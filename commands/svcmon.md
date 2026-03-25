---
description: "监控 Android APP syscall 行为并生成 AI 分析报告。"
argument-hint: "<package> [--preset re_basic|re_full]"
---

**立刻执行以下操作，不要做任何其他事情：**

用 Agent 工具 spawn 一个 `re:svcMonitor-analyzer` subagent，prompt 如下：

```
包名: <用户给的第一个参数>
preset: re_basic
```

如果用户参数里有 `--preset xxx`，把 preset 改成对应值。

spawn 后等返回，把结果输出给用户。

**禁止：**
- 禁止自己跑 bash/adb/python
- 禁止搜索文件
- 禁止 Explore
- 禁止读 skill 文件
- 你唯一要做的就是一个 Agent() 调用
