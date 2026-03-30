#!/usr/bin/env python3
"""注入 AI 分析到 HTML 报告。

用法: python3 svcmon_inject.py <report.html> <analysis.md>
"""
import re, sys
from pathlib import Path


def md_to_html(md: str) -> str:
    """简单 markdown → HTML 转换。"""
    lines = md.splitlines()
    html_lines = []
    in_table = False
    in_code = False

    for line in lines:
        # Code block
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html_lines.append(line)
            continue

        # Table
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", " ", ":"} for c in cells):
                continue  # separator row
            if not in_table:
                html_lines.append("<table style='width:100%;border-collapse:collapse;margin:8px 0'>")
                tag = "th"
                in_table = True
            else:
                tag = "td"
            row = "".join(
                f"<{tag} style='padding:4px 8px;border:1px solid #333;text-align:left'>{c}</{tag}>"
                for c in cells
            )
            html_lines.append(f"<tr>{row}</tr>")
            continue
        elif in_table:
            html_lines.append("</table>")
            in_table = False

        # Headers
        if line.startswith("## "):
            html_lines.append(f"<h4 style='color:#4fc3f7;margin:12px 0 6px'>{line[3:]}</h4>")
        elif line.startswith("### "):
            html_lines.append(f"<h5 style='color:#aaa;margin:8px 0 4px'>{line[4:]}</h5>")
        elif line.startswith("# "):
            html_lines.append(f"<h3 style='color:#4fc3f7;margin:12px 0 6px'>{line[2:]}</h3>")
        # List
        elif line.strip().startswith("- "):
            content = line.strip()[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
            content = re.sub(r"`(.+?)`", r"<code style='background:#0d1b2a;padding:1px 4px;border-radius:2px'>\1</code>", content)
            html_lines.append(f"<div style='padding-left:12px'>• {content}</div>")
        # Numbered list
        elif re.match(r"^\d+\.\s", line.strip()):
            content = re.sub(r"^\d+\.\s", "", line.strip())
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
            content = re.sub(r"`(.+?)`", r"<code style='background:#0d1b2a;padding:1px 4px;border-radius:2px'>\1</code>", content)
            html_lines.append(f"<div style='padding-left:12px'>{content}</div>")
        # Normal text
        elif line.strip():
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            content = re.sub(r"`(.+?)`", r"<code style='background:#0d1b2a;padding:1px 4px;border-radius:2px'>\1</code>", content)
            html_lines.append(f"<div>{content}</div>")
        else:
            html_lines.append("<br>")

    if in_table:
        html_lines.append("</table>")
    if in_code:
        html_lines.append("</code></pre>")

    return "\n".join(html_lines)


def main():
    if len(sys.argv) < 3:
        print("用法: python3 svcmon_inject.py <report.html> <analysis.md>")
        sys.exit(1)

    report_path = Path(sys.argv[1])
    analysis_path = Path(sys.argv[2])

    if not report_path.is_file():
        print(f"ERROR=report.html 不存在: {report_path}")
        sys.exit(1)
    if not analysis_path.is_file():
        print(f"ERROR=analysis.md 不存在: {analysis_path}")
        sys.exit(1)

    html = report_path.read_text(encoding="utf-8")
    md = analysis_path.read_text(encoding="utf-8")

    analysis_html = md_to_html(md)

    injection = (
        '<div id="ai-analysis" style="background:#16213e;border:1px solid #333;'
        'border-radius:4px;padding:12px;margin-bottom:12px">\n'
        '<h3 style="color:#0f0;margin:0 0 8px">AI 分析报告</h3>\n'
        f'<div style="color:#ccc;line-height:1.6;font-size:13px">\n{analysis_html}\n</div>\n'
        '</div>'
    )

    placeholder = '<div id="ai-analysis"></div>'
    if placeholder in html:
        html = html.replace(placeholder, injection)
        report_path.write_text(html, encoding="utf-8")
        print(f"INJECTED={report_path}")
        print("STATUS=OK")
    else:
        print("ERROR=placeholder <div id=\"ai-analysis\"></div> 不存在")
        print("STATUS=FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
