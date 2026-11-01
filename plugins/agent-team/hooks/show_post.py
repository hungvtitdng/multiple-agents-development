#!/usr/bin/env python3
"""agent-team show_post - PostToolUse hook. Hiện bài post trên board vào chat (systemMessage)."""
import json
import os
import re
import sys

MAX_LINES = 15
MAX_COLS = 160
POST_RE = re.compile(r"^(S\d)-(R\d+)-(.+)-\d+\.md$")


def main():
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path") or ""
    full = path if os.path.isabs(path) else os.path.join(data.get("cwd") or os.getcwd(), path)
    m = POST_RE.match(os.path.basename(full))
    if data.get("tool_name") != "Write" or not m or "/board/" not in full.replace("\\", "/"):
        return
    try:
        lines = [l.rstrip() for l in open(full, encoding="utf-8") if l.strip() and not l.lstrip().startswith("<!--")]
    except OSError:
        return
    body = [("│ " + l[:MAX_COLS] + ("…" if len(l) > MAX_COLS else "")) for l in lines[:MAX_LINES]]
    if len(lines) > MAX_LINES:
        body.append(f"│ … còn {len(lines) - MAX_LINES} dòng")
    stage, rnd, role = m.groups()
    msg = "\n".join([f"┌─ [{role} · {stage}-{rnd}]", *body, f"└─ {path}"])
    print(json.dumps({"systemMessage": msg}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # lỗi hiển thị không được làm hỏng luồng làm việc
        sys.stderr.write(f"[agent-team show_post] warning: {e}\n")
    sys.exit(0)
