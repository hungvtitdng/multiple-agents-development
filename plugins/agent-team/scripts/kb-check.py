#!/usr/bin/env python3
"""kb-check - file Knowledge Base nào còn là khung rỗng. Chỉ đọc.

Dùng: kb-check.py [--json] [thư mục project]
Exit 0 = đủ, 1 = còn thiếu. File KB hợp lệ cần: dòng `verified-at: <commit hash>` và đủ số nguồn `file.ext:dòng`.
"""
import glob
import json
import os
import re
import sys

# file KB bắt buộc sau khi dựng nháp từ code có sẵn: số nguồn `file:dòng` tối thiểu
REQUIRED = {
    "docs/project-overview.md": 0,
    "docs/architecture.md": 0,
    "docs/tech-stack.md": 0,
    "docs/domain-model.md": 1,
    "docs/business-rules.md": 3,
    "docs/roles-and-permissions.md": 1,
    "docs/glossary.md": 0,
    "docs/api/endpoints.md": 1,
    "docs/database/schema.md": 1,
    "docs/testing/test-strategy.md": 0,
    "docs/engineering/coding-standards.md": 1,
}
VERIFIED_RE = re.compile(r"verified-at:\s*`?[0-9a-f]{7,40}\b")
CITE_RE = re.compile(r"[\w./@-]+\.\w{1,5}:\d+")


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def check(root):
    rows = []
    for rel, min_cite in REQUIRED.items():
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            rows.append({"file": rel, "ok": False, "why": "chưa có file"})
            continue
        text = open(p, encoding="utf-8", errors="ignore").read()
        cites = len(CITE_RE.findall(text))
        why = []
        if not VERIFIED_RE.search(text):
            why.append("thiếu dòng `verified-at: <commit>` (còn là khung)")
        if cites < min_cite:
            why.append(f"mới {cites}/{min_cite} nguồn file:dòng")
        rows.append({"file": rel, "ok": not why, "why": "; ".join(why), "cites": cites})
    mods = sorted(glob.glob(os.path.join(root, "docs", "modules", "*", "README.md")))
    bad = [m for m in mods if not VERIFIED_RE.search(open(m, encoding="utf-8", errors="ignore").read())]
    if not mods:
        rows.append({"file": "docs/modules/<tên>/README.md", "ok": False, "why": "chưa có module nào"})
    for m in bad:
        rows.append({"file": os.path.relpath(m, root), "ok": False, "why": "thiếu dòng `verified-at: <commit>`"})
    if mods and not bad:
        rows.append({"file": f"docs/modules/ ({len(mods)} module)", "ok": True, "why": ""})
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = find_root(args[0] if args else os.getcwd())
    if not root:
        sys.stderr.write("kb-check: không thấy .claude/agent-team.config (chạy /agent-team:init trước)\n")
        sys.exit(2)
    rows = check(root)
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{'OK  ' if r['ok'] else 'THIEU'}  {r['file']}" + (f"  - {r['why']}" if r["why"] else ""))
        n = sum(not r["ok"] for r in rows)
        print(f"\n{len(rows) - n}/{len(rows)} đạt" + (f", còn {n} mục thiếu" if n else ""))
    sys.exit(1 if any(not r["ok"] for r in rows) else 0)


if __name__ == "__main__":
    main()
