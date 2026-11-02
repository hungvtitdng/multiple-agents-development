#!/usr/bin/env python3
"""Test kb-check.py: python3 tests/test_kb_check.py"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "scripts", "kb-check.py")
TPL = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "templates", "kb")
fail = total = 0


def run(root):
    r = subprocess.run([sys.executable, SCRIPT, "--json", root], capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else [])


def check(desc, got, exp):
    global fail, total
    total += 1
    fail += got != exp
    print(f"{'PASS' if got == exp else 'FAIL'}  {desc}  (expect {exp}, got {got})")


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


proj = tempfile.mkdtemp()
write(proj, ".claude/agent-team.config", 'BE_PATHS="app"\n')
code, rows = run(proj)
check("không có docs -> thiếu", code, 1)

# copy nguyên khung template: header có chữ `verified-at: <commit>` nhưng chưa phải KB thật
for dp, _, fs in os.walk(TPL):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), TPL)
        write(proj, os.path.join("docs", rel), open(os.path.join(dp, f), encoding="utf-8").read())
code, rows = run(proj)
check("khung template chưa điền -> thiếu", code, 1)
check("khung template: mọi file bắt buộc đều THIẾU", sum(not r["ok"] for r in rows) >= 11, True)

FILLED = "verified-at: abc1234\n| BR-1 | x | y | z | Assumption | app/a.rb:10 |\n| BR-2 | x | y | z | Assumption | app/b.rb:20 |\n| BR-3 | x | y | z | Assumption | app/c.rb:30 |\n"
for rel in ("project-overview", "architecture", "tech-stack", "domain-model", "business-rules", "roles-and-permissions",
            "glossary", "api/endpoints", "database/schema", "testing/test-strategy", "engineering/coding-standards"):
    write(proj, f"docs/{rel}.md", "# t\n" + FILLED)
code, rows = run(proj)
check("điền đủ nhưng chưa có module -> thiếu", code, 1)
write(proj, "docs/modules/trip/README.md", "# trip\nverified-at: abc1234\n")
code, rows = run(proj)
check("điền đủ + 1 module -> đạt", code, 0)

write(proj, "docs/business-rules.md", "# t\nverified-at: abc1234\n| BR-1 | x | y | z | A | app/a.rb:10 |\n")
code, rows = run(proj)
check("business-rules chỉ 1/3 nguồn -> thiếu", code, 1)
write(proj, "docs/business-rules.md", "# t\n" + FILLED)
write(proj, "docs/modules/order/README.md", "# order\n")
code, rows = run(proj)
check("module thiếu verified-at -> thiếu", code, 1)
os.remove(os.path.join(proj, "docs/modules/order/README.md"))
write(proj, "docs/glossary.md", "# t\nverified-at: <commit>\n")
code, rows = run(proj)
check("verified-at còn placeholder <commit> -> thiếu", code, 1)

nocfg = tempfile.mkdtemp()
r = subprocess.run([sys.executable, SCRIPT, nocfg], capture_output=True, text=True)
check("không có config -> exit 2", r.returncode, 2)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
