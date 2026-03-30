---
description: "用 IDA 全量导出指定 SO 的反汇编、反编译、调用图到 session 目录。"
argument-hint: "<package_name> <so_name>"
---

**立刻执行以下操作，不要做任何其他事情：**

用 Agent 工具 spawn 一个 `so-extractor` subagent，prompt 如下：

```
PACKAGE: <用户给的第一个参数>
SO_NAME: <用户给的第二个参数>
```

如果用户只给了一个参数（没有 so_name），告诉用户：
```
用法: /re:extractSo <package> <so_name>
先用 /re:pullApk <package> 查看可用的 SO 文件
```

spawn 后等返回，把结果输出给用户。

**禁止：**
- 禁止自己跑 bash/python/ida
- 你唯一要做的就是一个 Agent() 调用
