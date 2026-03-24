# /svcmon Command

Monitor Android APP syscall behavior and generate AI analysis report.

## Usage

```bash
/svcmon <package_or_keyword> [--preset re_basic|re_full|file|proc|mem|net|security|all] [--duration 15s]
```

## Arguments

- `<package_or_keyword>` — Package name or keyword. Supports fuzzy match: `silicon` → `silicon.android.app`
- `--preset` — Syscall preset (default: re_basic). re_basic for detection analysis, re_full for full reverse
- `--duration` — Wait time after app launch (default: 15s)

## What This Command Does

Three steps: Collect → Analyze → Inject.

### Step 1: Collect (run svcmon CLI)

```bash
svcmon run <package_or_keyword> --preset <preset> --duration <duration> --no-open
```

If `svcmon` command not found, install it first:
```bash
cd <path-to-svcmon-plugin>/tools && pip install -e .
svcmon setup
```

Capture the output: trace.log path and report.html path.

If 0 events: check stackplz installation (`svcmon setup`), try `--preset re_basic`.

### Step 2: AI Analysis (spawn subagent)

Spawn a `svcmon-analyzer` subagent with this prompt:

```
Read <trace.log path>. This is a stackplz trace of <package>.

Analyze and output Markdown:

## Detection Chain
Timeline of detection actions after app launch.

## Thread Roles
Each thread's role: detection / destruction / self-kill / normal.

## Detection Methods
For each method found, give count, thread, and call source:
- FD enumeration (readlinkat /proc/self/fd/*)
- Maps scanning (openat /proc/self/maps)
- Thread name scanning (openat /proc/self/task/*/comm)
- Memory probing (openat /proc/self/mem, smaps)
- Mount checking (openat /proc/self/mountinfo)
- Cmdline checking (openat /proc/self/cmdline)
- Anti-debug (ptrace, prctl PR_SET_DUMPABLE)
- FD brute-close (massive sequential close())
- Self-kill (kill/tgkill SIGKILL)
- Network port scanning (openat /proc/net/tcp)
- Suspicious file probing (frida/magisk/su paths)
- Anti-VM (system property reads, /dev/goldfish_pipe, /proc/cpuinfo, build.prop)

## Key Call Sites
SO name + offset from backtraces that initiated detection.

## Bypass Suggestions
Specific bypass direction for each detection method found.

Be concise. Don't fabricate detection methods that don't exist in the trace.
```

### Step 3: Inject Analysis into Report

After subagent returns markdown, use Edit tool to replace `<div id="ai-analysis"></div>` in report.html with:

```html
<div id="ai-analysis" style="background:#16213e;border:1px solid #333;border-radius:4px;padding:12px;margin-bottom:12px">
<h3 style="color:#0f0;margin:0 0 8px">AI Analysis</h3>
<div style="color:#ccc;line-height:1.6">
[convert markdown to HTML: ## → <h4>, ** → <b>, - → <li>, ``` → <code>, newline → <br>]
</div>
</div>
```

### Step 4: Output

```
Report: <path>/report.html
Trace:  <path>/trace.log

[Brief summary of key findings from subagent analysis]
```

Then open the report: `start "" <report.html>` (Windows) or `open <report.html>` (Mac).

## Preset Reference

| Preset | Use Case | Categories |
|--------|----------|-----------|
| re_basic | Detection analysis (recommended) | File + Process + Signal |
| re_full | Full reverse engineering | File + Process + Memory + Network + Signal + Security |
| file | File behavior only | File operations |
| proc | Process behavior only | Process + Signal |
| mem | Memory behavior only | Memory management |
| net | Network behavior only | Network communication |
| security | Security audit | seccomp/bpf/namespace |
| all | Everything (may OOM) | All syscalls |

## Prerequisites

- `svcmon` CLI installed: `cd <plugin>/tools && pip install -e . && svcmon setup`
- Device connected via ADB with root (APatch/Magisk/KernelSU)
- stackplz downloaded and pushed to device (handled by `svcmon setup`)
