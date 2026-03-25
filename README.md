# reverse-plugin

Claude Code plugin for Android reverse engineering.

## 安装

```bash
/plugin marketplace add xiameng666/reverse-plugin
/plugin install re
/reload-plugins
```

## 命令

### `/re:svcmon <包名>` — Syscall 行为监控

一键监控 APP 的 syscall 行为，自动生成带 AI 分析的 HTML 报告。

```bash
/re:svcmon silicon              # 模糊匹配包名
/re:svcmon com.example.app      # 完整包名
```

**功能：**
- 基于 [stackplz](https://github.com/SeeFlowerX/stackplz)（eBPF）采集 syscall + 栈回溯
- Zygote maps baseline + mmap 事件重建完整内存映射
- APK 内嵌 SO 偏移解析（split_config.arm64_v8a.apk → libxxx.so）
- addr2line 级别的精确符号化
- AI 语义分析：检测链路、线程分工、关键 SO 定位、绕过建议
- 自包含 HTML 报告（暗色主题、Tab 分类、按线程钻取）

**检测识别：**

| 类别 | 识别内容 |
|------|---------|
| 反调试 | ptrace、prctl PR_SET_DUMPABLE、/proc/self/status |
| 反注入 | maps 扫描、FD 遍历、线程名扫描、暴力 close fd、/proc/self/mem 完整性校验 |
| 反虚拟机 | 系统属性探测、/dev/goldfish_pipe、/proc/cpuinfo、build.prop |
| 挂载检测 | /proc/self/mountinfo（Magisk bind mount） |
| 网络检测 | /proc/net/tcp（frida-server 端口） |
| 文件探测 | faccessat/openat frida/magisk/su/xposed 路径 |

**Preset：**

| Preset | 场景 | Syscall 分类 |
|--------|------|-------------|
| `re_basic` | 检测分析（默认） | 文件操作 + 进程管理 + 信号处理 |
| `re_full` | 完整逆向 | 全部 6 大分类 |
| `file` | 文件行为 | 文件操作 |
| `proc` | 进程行为 | 进程管理 + 信号 |
| `mem` | 内存行为 | 内存管理 |
| `net` | 网络行为 | 网络通信 |
| `security` | 安全审计 | seccomp/bpf/namespace |
| `all` | 全量 | 所有 syscall |

**首次使用自动 setup：**
- 下载 stackplz 最新版
- 推送到设备 `/data/local/tmp/re/`
- 配置报告输出目录

---

## 计划中

### `/re:hook <包名>` — Frida Hook 编排

自动分析检测点 → 生成 hook 脚本 → 注入绕过 → 验证结果。

### `/re:patch <包名>` — 静态修补

基于 svcmon 分析结果，定位检测 SO → 生成 NOP patch → 重打包验证。

### `/re:trace <包名>` — uprobe 精准追踪

对 svcmon 定位的关键 SO 函数做 uprobe hook，抓取参数和返回值。

### `/re:diff <包名>` — 版本对比

对比两个版本的 APP 检测行为差异，追踪保护方案升级。

### `/re:report` — 综合报告

汇总 svcmon + hook + patch 的结果，生成完整逆向分析报告。

---

## 依赖

- Claude Code v2.1+
- Android 设备（root，ARM64，kernel 5.10+）
- ADB
- Python 3.8+ / pip / click

## 架构

```
/re:svcmon silicon
     ↓
主 Agent (skill)
  ├── AskUserQuestion（首次 setup）
  └── spawn subagent
         ↓
svcMonitor-analyzer (subagent)
  ├── pip install svcMonitor CLI
  ├── 下载 + push stackplz
  ├── svcMonitor run（采集）
  ├── 读 trace_resolved.log（分析）
  ├── 注入 AI 分析到 HTML
  └── 返回结果
```

## License

MIT
