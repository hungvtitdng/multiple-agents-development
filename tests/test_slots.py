#!/usr/bin/env python3
"""Test chia slot (v0.29.1): debate chiếm 1 slot, tối đa MAX_DEBATE, task READY không giới hạn / module, theo thứ tự bảng Module.
python3 tests/test_slots.py"""
import os
import re
import subprocess
import sys
import tempfile

POOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "pool.py")
ENV = {k: v for k, v in os.environ.items() if k != "AGENT_TEAM_BOARD_DB"}
fail = total = 0


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


def sh(*cmd):
    return subprocess.run(cmd, cwd=d, capture_output=True, text=True, check=True).stdout


def run(*args):
    r = subprocess.run([sys.executable, POOL, *args], capture_output=True, text=True, cwd=d, env=ENV)
    return r.returncode, r.stdout + r.stderr


def w(rel, text):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


d = os.path.realpath(tempfile.mkdtemp())
sh("git", "init", "-q", "-b", "master"), sh("git", "config", "user.email", "t@t"), sh("git", "config", "user.name", "t")
w(".claude/agent-team.config", "MAX_PARALLEL=8\nMAX_DEBATE=4\n")
w(".gitignore", ".agent-team/\n")
rows = "\n".join(f"| M-{i} | Mod {i} | R-{i} | M-0 | VỪA | | | | TODO |" for i in range(1, 7))
w("docs/product/APP.md", f"""# App
| M | Module | Gồm R | Phụ thuộc | Loại | Tag | Task-id | Người chạy | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| M-0 | Khung | R-0 | | VỪA | | | | DONE |
{rows}
| M-7 | Báo cáo | R-7 | M-1 | VỪA | | | | TODO |
| M-8 | Xuất file | R-8 | M-1 | NHẸ | | | | TODO |

## Lý do phụ thuộc
- M-7 → M-1 (code): dùng bảng của M-1
- M-8 → M-1 (contract): chỉ gọi service M-1
""")
sh("git", "add", "."), sh("git", "commit", "-qm", "init"), sh("git", "switch", "-qc", "agent/app")

code, out = run("fill")
check("fill: 4 module đầu bắt đầu debate (mỗi debate 1 slot), MAX_DEBATE=4", out.count("💬 ") == 4 and all(f"💬 M-{i}:" in out for i in range(1, 5)))
code, out = run("status")
check("status: debate 4/4, chờ debate M-5, M-6 (M-7, M-8 chưa đủ điều kiện vì M-1 chưa chia task)",
      "debate 4/4" in out and "Chờ debate: M-5, M-6 (" in out and "⏳ Chờ slot debate" in out and "⏳ Chờ phụ thuộc" in out)

for k in range(1, 7):
    run("add", f"M-1/T-{k}", "--task-id", f"m1-t{k}", "--title", f"Task {k}")
code, out = run("fill")
check("task thêm lúc module còn debate: chưa READY, không mở worktree", "▶ " not in out)
run("module", "M-1", "--state", "SPLIT")
code, out = run("fill")
started = re.findall(r"▶ (M-\d+/T-\d+)", out)
check("M-1 chia task: slot debate thành slot task, M-1 lấy 5 slot (8 − 3 debate còn lại), không giới hạn / module",
      len(started) == 5 and all(s.startswith("M-1/") for s in started))
code, out = run("status")
check("M-1 đã chia task → M-7, M-8 đủ điều kiện debate, nhưng hết slot: vào hàng chờ debate",
      "chạy 8/8" in out and "Chờ debate: M-5, M-6, M-7, M-8" in out)

run("module", "M-2", "--state", "SPLIT")
run("module", "M-3", "--state", "SPLIT")
code, out = run("fill")
check("2 debate xong, chưa có task → 2 slot trống: M-1/T-6 trước (theo thứ tự bảng), rồi debate M-5",
      "▶ M-1/T-6" in out and "💬 M-5:" in out and "💬 M-6:" not in out)

run("module", "M-7", "--state", "DESIGN")
run("add", "M-7/T-1", "--task-id", "m7-t1", "--title", "Báo cáo"), run("module", "M-7", "--state", "SPLIT")
run("module", "M-8", "--state", "DESIGN")
run("add", "M-8/T-1", "--task-id", "m8-t1", "--title", "Xuất file"), run("module", "M-8", "--state", "SPLIT")
code, out = run("status")
check("phụ thuộc module: M-7 (code) chờ M-1 DONE · M-8 (contract) chưa có file contract cũng chờ",
      re.search(r"M-7\s*│ T-1.*⏳ Chờ M-1 ", out) is not None and re.search(r"M-8\s*│ T-1.*⏳ Chờ M-1 \(contract\)", out) is not None)
w("docs/product/contracts/M-1.md", "service M-1\n")
code, out = run("status")
check("có contract M-1 → M-8/T-1 READY, M-7/T-1 vẫn chờ code M-1", re.search(r"M-8\s*│ T-1.*🟢 READY", out) is not None
      and re.search(r"M-7\s*│ T-1.*⏳ Chờ M-1", out) is not None)

lines = [l for l in out.splitlines() if l.startswith("│")]
check("bảng: cột Module · Task · Debate · Code · Test · Review · Merge · Trạng thái, không có dòng tổng",
      "│ Module │ Task" in out and re.search(r"│ Debate\s*│ Code\s*│ Test\s*│ Review\s*│ Merge\s*│ Trạng thái", out) is not None and "tổng" not in out.lower())
check("task đang code: ✅ Debate, ▶ mm:ss Code, ⏳ Test/Review/Merge, chưa có agent", re.search(r"T-1 Task 1\s*│ ✅\s*│ ▶ \d\d:\d\d\s*│ ⏳\s*│ ⏳\s*│ ⏳\s*│ ▶ Code · chưa có agent", out) is not None)
check("module đang debate có thời gian chạy", re.search(r"💬 Debate \d\d:\d\d", out) is not None)
check("tên module chỉ ở dòng đầu của nhóm", sum(1 for l in lines if re.match(r"│ M-1\s", l)) == 1)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
