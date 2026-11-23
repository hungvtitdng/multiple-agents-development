#!/usr/bin/env python3
"""Test progress.py: python3 tests/test_progress.py"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "scripts", "progress.py")
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, ".claude"))
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\nPROGRESS_LINES=1\n")
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
check("S2 chưa có bước: không còn %, chỉ giai đoạn", code == 0 and out.startswith("[T-7] S2 DEBATE") and "%" not in out)
check("S2 liệt kê tối đa 3 mục thiếu", "thiếu: Loại, Phương án chốt, Security duyệt solution …" in out)

write_task(**{"Loại": "VỪA", "Phương án chốt": "B", "Security duyệt solution": "APPROVED", "Workflow": "YES"})
check("S2 điền 4/5: chỉ còn thiếu UI mockup", "thiếu: UI mockup" in run()[1])

write_task(**{"Loại": "NHỎ (sửa text)"})
check("NHỎ dùng cổng ngắn", "thiếu: Tiêu chí nghiệm thu" in run()[1] and "Phương án" not in run()[1])

stage("S4")
write_task(**{"Lint/format": "PASS", "Kết quả test": "PASS"})
check("S4 điền 2/4: không còn thanh %", "▓" not in run()[1] and "thiếu: Gap còn mở, E2E" in run()[1])

stage("S6")
write_task(**{"Code review": "APPROVED", "Security review": "APPROVED", "Cập nhật KB": "YES", "Bài học": "KHÔNG CÓ"})
check("S6 đủ: không còn thiếu", "thiếu" not in run()[1])

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

# ---- v0.20.0: danh sách bước ----
def runl():
    r = subprocess.run([sys.executable, SCRIPT, "--list"], capture_output=True, text=True, cwd=os.path.join(d, "docs"))
    return r.stdout.strip()


stage("S3")
check("--list chưa có bước: nhắc Lead lập", "Chưa có danh sách bước" in runl())
db = sqlite3.connect(os.path.join(d, ".agent-team", "board.db"))
db.executescript("""
CREATE TABLE plan_steps (task TEXT, n INTEGER, title TEXT, role TEXT, state TEXT, started_at INTEGER, ended_at INTEGER);
INSERT INTO plan_steps VALUES('T-7',1,'Scaffold starter','backend-dev','done',1,2),
 ('T-7',2,'Đăng ký, 2FA','backend-dev','doing',2,NULL),
 ('T-7',3,'Khung R-54','backend-dev','todo',NULL,NULL),
 ('T-7',4,'Test + lint','test-executor','todo',NULL,NULL);
""")
db.commit()
out = run()[1]
check("status line: bước 2/4 + còn", "bước 2/4: Đăng ký, 2FA" in out and "còn: Khung R-54, Test + lint" in out and "thiếu" not in out)
out = runl()
check("--list: bảng khung #/Bước/Role/Trạng thái", "│ # │ Bước" in out and "│ Trạng thái" in out and "┌" in out and "└" in out
      and "│ Scaffold starter │ backend-dev   │ ✅ Xong" in out and "▶ Đang làm" in out and "│ Test + lint      │ test-executor │ ⏳ Chờ" in out)
db.execute("UPDATE plan_steps SET state='done' WHERE n=2"); db.commit()
check("chưa bước nào đang chạy: bước tiếp 3/4", "bước tiếp 3/4: Khung R-54" in run()[1])
db.execute("UPDATE plan_steps SET state='done'"); db.commit()
check("xong hết: xong 4/4 bước", "xong 4/4 bước" in run()[1])
db.close()

# App: module x/N
os.makedirs(os.path.join(d, "docs", "product", "design"))
APP = os.path.join(d, "docs", "product", "APP.md")
open(APP, "w").write("# App\n- Intake: YES\n- Challenger: TODO\n| M | Module | Gồm R | Phụ thuộc | Loại | Branch gốc | Task-id | Trạng thái |\n|---|---|---|---|---|---|---|---|\n"
                     "| M-0 | Khung | | | VỪA | | | DONE |\n| M-1 | Auth | | M-0 | | | | TODO |\n| M-E2E | E2E | | | | | | TODO |\n")
out = runl()
check("--list có tầng App: 1/3 module xong + module đang làm", out.splitlines()[0].endswith("· 1/3 module xong") and "M-1" in out and "▶ Đang làm" in [l for l in out.splitlines() if "M-1" in l][0])

# Phase A (APP, S2): 10 bước theo cổng + file
write_task(**{"Loại": "APP"})
stage("S2")
open(os.path.join(d, "docs", "product", "problem.md"), "w").write("- G-1: Giảm thời gian duyệt | Thước đo: 2 ngày\n")
open(os.path.join(d, "docs", "product", "requirements.md"), "w").write("| R | Yêu cầu |\n|---|---|\n| R-1 | Đăng nhập |\n")
open(os.path.join(d, "docs", "product", "flows.md"), "w").write("## F-1: Đăng nhập\n")
out = run()[1]
check("Phase A: 3 bước đầu xong → bước 4/10 Mockup", "S2 Phase A" in out and "bước 4/10: Mockup" in out)
open(os.path.join(d, "docs", "product", "design", "mockup-login.html"), "w").write("x")
out = runl()
check("Phase A --list: 10 bước > 8 dòng → gộp 1–4 ✅, ▶ Săn gap", "App · Phase A · 5/10 xong" in out and "1–4" in out and "Săn gap (Challenger)" in out
      and "▶ Đang làm" in out and "Chia module" in out)
open(os.path.join(d, "docs", "product", "flows.md"), "w").write("## F-1: TODO\n")
check("flows.md còn TODO: bước 3 chưa xong", "bước 3/10" in run()[1])

# ---- v0.21.0: ∥ trong --list ----
os.remove(APP)
write_task(**{"Loại": "VỪA"})
stage("S3")
db = sqlite3.connect(os.path.join(d, ".agent-team", "board.db"))
db.execute("DROP TABLE plan_steps")
db.executescript("""
CREATE TABLE plan_steps (task TEXT, n INTEGER, title TEXT, role TEXT, state TEXT, started_at INTEGER, ended_at INTEGER, grp INTEGER);
INSERT INTO plan_steps VALUES('T-7',1,'API','backend-dev','doing',1,NULL,1), ('T-7',2,'Màn hình','frontend-dev','doing',1,NULL,1),
 ('T-7',3,'Test','test-executor','todo',NULL,NULL,2);
""")
db.commit(); db.close()
out = runl()
check("--list: 2 bước song song có ∥", out.count("∥") == 2)
check("status line: bước 1+2/3 chạy cùng lúc", "bước 1+2/3: API; Màn hình" in run()[1])

# ---- v0.22.0: status line dạng bảng (mặc định) ----
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\n")
out = run()[1]
check("PROGRESS_LINES mặc định = bảng nhiều dòng", out.count("\n") >= 3 and "Trạng thái" in out and "⏳ Chờ" in out)
check("bước đang làm có thời gian chạy mm:ss", re.search(r"▶ Đang làm \d+:\d\d", out) is not None)
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\nPROGRESS_LINES=1\n")
check("PROGRESS_LINES=1: 1 dòng như cũ", "\n" not in run()[1])
db = sqlite3.connect(os.path.join(d, ".agent-team", "board.db"))
db.execute("DELETE FROM plan_steps")
db.executemany("INSERT INTO plan_steps VALUES('T-7',?,?,?,?,1,NULL,?)",
               [(i, f"Bước {i}", "backend-dev", "done" if i <= 5 else "doing" if i == 6 else "todo", i) for i in range(1, 13)])
db.commit(); db.close()
out = runl()
check("12 bước: gộp ✅ đầu + ⏳ cuối, ≤ 8 dòng bước", "1–5" in out and "✅ Xong" in out and len([l for l in out.splitlines() if l.startswith(" ") and "Bước" in l]) <= 9)

# ---- v0.23.1: S1-S2 vẫn có bảng; `- Module: N/A (...)` không coi là thư mục module ----
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\n")
open(APP, "w").write("# Cà phê\n| M | Module | Gồm R | Phụ thuộc | Loại | Branch gốc | Task-id | Trạng thái |\n|---|---|---|---|---|---|---|---|\n"
                     "| M-0 | Khung | | | VỪA | | x | DONE |\n| M-1 | Auth | | M-0 | | | | TODO |\n")
write_task(**{"Loại": "VỪA (module M-1)"})
open(os.path.join(task_dir, "TASK.md"), "a").write("- Module: N/A (task con của module mới: docs/product/modules/<tên>; hook chờ)\n")
stage("S2")
db = sqlite3.connect(os.path.join(d, ".agent-team", "board.db")); db.execute("DELETE FROM plan_steps"); db.commit(); db.close()
out = run()[1]
check("Module: N/A → vẫn hiện tầng App", out.startswith("App Cà phê · 1/2 module xong") and "M-1" in out)
check("S2 chưa có bước: bảng giai đoạn S1 ✅ S2 ▶ S3 ⏳", "│ S1 Scout │ S2 Debate │ S3 Code │" in out and "│ ✅       │ ▶         │ ⏳      │" in out and "Chưa có danh sách bước" not in out)

# ---- v0.24.0: khung bảng thẳng hàng (độ rộng hiển thị) ----
lines = [l for l in out.splitlines() if l[:1] in "┌│├└"]
import unicodedata as _ud
_w = lambda t: sum(0 if _ud.combining(c) else 2 if _ud.east_asian_width(c) in ("W", "F") else 1 for c in t)
groups, cur = [], []
for l in out.splitlines():
    if l[:1] in "┌│├└":
        cur.append(l)
    elif cur:
        groups.append(cur); cur = []
if cur:
    groups.append(cur)
check("mọi dòng trong 1 bảng cùng độ rộng hiển thị (có ✅ ⏳ tiếng Việt)", groups and all(len({_w(l) for l in g}) == 1 for g in groups))
open(APP, "a").write("| M-2 | Báo cáo | | M-1 | | | | BLOCKED (chờ owner Q-3) |\n")
check("module BLOCKED hiện ⛔ Chặn", "⛔ Chặn" in run()[1])

print(f"\n{total - fail}/{total} PASS")
sys.exit(1 if fail else 0)
