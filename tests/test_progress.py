#!/usr/bin/env python3
"""Test progress.py: python3 tests/test_progress.py"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "scripts", "progress.py")
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, ".claude"))
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\n")
os.makedirs(os.path.join(d, ".agent-team"))
task_dir = os.path.join(d, "docs", "agent-tasks", "T-7")
os.makedirs(task_dir)
fail = total = 0


def write_task(**vals):
    keys = ["Loại", "Tiêu chí nghiệm thu", "Phương án chốt", "Security duyệt solution", "Workflow", "UI mockup",
            "Kết quả test", "Lint/format", "Gap còn mở", "E2E", "Code review", "Security review", "Cập nhật KB", "Bài học"]
    body = "".join(f"- {k}: {vals.get(k, 'TODO (x)')}\n" for k in keys)
    open(os.path.join(task_dir, "TASK.md"), "w").write("# T-7\n## Điều kiện\n" + body)


def stage(s):
    open(os.path.join(d, ".agent-team", "stage"), "w").write(s + "\n")


def run(stdin=None):
    data = json.dumps({"workspace": {"current_dir": os.path.join(d, "docs")}}) if stdin is None else stdin
    r = subprocess.run([sys.executable, SCRIPT], input=data, capture_output=True, text=True, cwd=d)
    return r.returncode, r.stdout.strip()


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


check("chưa có stage: không in gì", run() == (0, ""))

write_task()
stage("S2")
code, out = run()
check("S2 chưa điền gì: 15%", code == 0 and out.startswith("[T-7] S2 DEBATE ") and " 15%" in out)
check("S2 liệt kê tối đa 3 mục thiếu", "thiếu: Loại, Phương án chốt, Security duyệt solution …" in out)

write_task(**{"Loại": "VỪA", "Phương án chốt": "B", "Security duyệt solution": "APPROVED", "Workflow": "YES"})
check("S2 điền 4/5: 31%", " 31%" in run()[1] and "thiếu: UI mockup" in run()[1])

write_task(**{"Loại": "NHỎ (sửa text)"})
check("NHỎ dùng cổng ngắn: 25%", " 25%" in run()[1])

stage("S4")
write_task(**{"Lint/format": "PASS", "Kết quả test": "PASS"})
check("S4 điền 2/4: 70%", " 70%" in run()[1] and "▓▓▓▓▓▓▓░░░" in run()[1])

stage("S6")
write_task(**{"Code review": "APPROVED", "Security review": "APPROVED", "Cập nhật KB": "YES", "Bài học": "KHÔNG CÓ"})
check("S6 đủ: 100%, không còn thiếu", " 100%" in run()[1] and "thiếu" not in run()[1])

stage("S5")
db = sqlite3.connect(os.path.join(d, ".agent-team", "board.db"))
db.executescript("""
CREATE TABLE rounds (id INTEGER PRIMARY KEY, task TEXT, stage TEXT, round INTEGER, goal TEXT, roles TEXT,
  opened_at INTEGER, closed_at INTEGER);
CREATE TABLE messages (id INTEGER PRIMARY KEY, task TEXT, stage TEXT, round INTEGER, role TEXT, body TEXT);
CREATE TABLE whys (id INTEGER PRIMARY KEY, task TEXT, status TEXT);
INSERT INTO rounds(task, stage, round, roles, opened_at) VALUES('T-7','S5',1,'code-reviewer,security',1);
INSERT INTO messages(task, stage, round, role, body) VALUES('T-7','S5',1,'security','ok');
INSERT INTO whys(task, status) VALUES('T-7','open'), ('T-7','agreed');
""")
db.commit()
db.close()
out = run()[1]
check("board: role chưa post", "chờ: code-reviewer" in out and "security," not in out)
check("board: WHY mở", "WHY mở: 1" in out)

check("chạy tay không có stdin JSON vẫn chạy", run("")[1].startswith("[T-7] S5 REVIEW"))
check("stage lạ: không in gì", (stage("S9"), run())[1] == (0, ""))

print(f"\n{total - fail}/{total} PASS")
sys.exit(1 if fail else 0)
