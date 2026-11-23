#!/usr/bin/env python3
"""Test pool.py (điều phối nhiều task, mỗi task 1 worktree): python3 tests/test_pool.py"""
import os
import sqlite3
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


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout


def run(*args, cwd=None):
    r = subprocess.run([sys.executable, POOL, *args], capture_output=True, text=True, cwd=cwd or d, env=ENV)
    return r.returncode, r.stdout + r.stderr


def clean():
    """Thư mục chính không còn thay đổi (trừ config: đổi MAX_PARALLEL là sửa file này)."""
    return [l for l in sh(d, "git", "diff", "--name-only", "HEAD").splitlines() if l != ".claude/agent-team.config"] == []


def cfg(extra=""):
    with open(os.path.join(d, ".claude", "agent-team.config"), "w") as f:
        f.write('BE_PATHS="app"\nE2E_PORT_BASE=4100\n' + extra)


d = os.path.realpath(tempfile.mkdtemp())
sh(d, "git", "init", "-q", "-b", "master")
sh(d, "git", "config", "user.email", "t@t"), sh(d, "git", "config", "user.name", "t")
os.makedirs(os.path.join(d, ".claude")), os.makedirs(os.path.join(d, "app"))
open(os.path.join(d, ".gitignore"), "w").write(".agent-team/\n")
cfg("MAX_PARALLEL=2\n")
open(os.path.join(d, "app", "a.txt"), "w").write("base\n")
sh(d, "git", "add", "."), sh(d, "git", "commit", "-qm", "init")

code, out = run("fill")
check("fill khi còn ở master: không có task thì chỉ báo 0", code == 0 and "Đang chạy 0/2" in out)
sh(d, "git", "switch", "-qc", "agent/20261124-app")

check("thêm task khi module chưa chia (đang debate) bị từ chối", run("add", "M-1/T-1", "--task-id", "x", "--title", "x")[0] == 1)
run("module", "M-1", "--kind", "NẶNG", "--state", "DESIGN")
code, out = run("module", "M-2", "--state", "DESIGN")
check("mỗi lúc chỉ 1 module thiết kế", code == 1 and "M-1 đang thiết kế" in out)
run("module", "M-1", "--state", "SPLIT")
check("nhãn sai bị từ chối", run("add", "T-1", "--task-id", "x", "--title", "x")[0] == 1)
check("task-id có / bị từ chối", run("add", "M-1/T-1", "--task-id", "a/b", "--title", "x")[0] == 1)
run("add", "M-1/T-1", "--task-id", "20261124-m1-t1", "--title", "Auth API")
run("add", "M-1/T-2", "--task-id", "20261124-m1-t2", "--title", "Màn đăng nhập")
run("add", "M-1/T-3", "--task-id", "20261124-m1-t3", "--title", "Menu quyền", "--deps", "M-1/T-1")

code, out = run("fill")
check("fill: MAX_PARALLEL=2 → mở 2 task READY, T-3 chờ T-1", out.count("▶ ") == 2 and "M-1/T-3" not in out)
w1, w2 = os.path.join(d, ".worktrees", "20261124-m1-t1"), os.path.join(d, ".worktrees", "20261124-m1-t2")
check("worktree tạo từ branch phiên + branch agent/<task-id>", os.path.isdir(w1) and sh(w1, "git", "rev-parse", "--abbrev-ref", "HEAD").strip() == "agent/20261124-m1-t1")
check("mỗi worktree 1 cổng E2E riêng", open(os.path.join(w1, ".agent-team", "e2e_port")).read().strip() == "4100"
      and open(os.path.join(w2, ".agent-team", "e2e_port")).read().strip() == "4101")
check(".worktrees vào .git/info/exclude, không sửa .gitignore", "/.worktrees/" in open(os.path.join(d, ".git", "info", "exclude")).read()
      and ".worktrees" not in open(os.path.join(d, ".gitignore")).read())
check("thư mục chính vẫn sạch", sh(d, "git", "status", "--porcelain") == "")

cfg("MAX_PARALLEL=1\n")
code, out = run("fill")
check("giảm MAX_PARALLEL: không giết task đang chạy, không mở thêm", "Đang chạy 2/1" in out and "▶ " not in out)
cfg("MAX_PARALLEL=3\n")
code, out = run("fill")
check("tăng MAX_PARALLEL: vẫn không mở T-3 vì chờ T-1", "▶ " not in out and "READY 0" in out)

# T-1 code xong (Lead commit trong worktree), merge OK
open(os.path.join(w1, "app", "auth.txt"), "w").write("auth\n")
sh(w1, "git", "add", "."), sh(w1, "git", "commit", "-qm", "[backend-dev] 20261124-m1-t1: auth")
check("merge-begin khi chưa MERGE_WAIT bị từ chối", run("merge-begin", "M-1/T-1")[0] == 1)
run("set", "M-1/T-1", "MERGE_WAIT")
code, out = run("merge-begin", "M-1/T-1")
check("merge-begin: merge --no-commit, chờ integration test", code == 0 and "merge-end" in out and os.path.isfile(os.path.join(d, "app", "auth.txt")))
code, out = run("fill")
check("đang MERGING thì không fill", "Đang merge" in out)
code, out = run("merge-end", "M-1/T-1", "pass")
log = sh(d, "git", "log", "--oneline", "-1")
check("merge-end pass: commit merge 1 dòng [lead], xoá worktree", "[lead] 20261124-m1-t1: merge M-1/T-1" in log and not os.path.isdir(w1))
check("branch task giữ lại (không xoá branch)", "agent/20261124-m1-t1" in sh(d, "git", "branch"))
code, out = run("fill")
check("T-1 merged → T-3 READY → được mở", "▶ M-1/T-3" in out)
w3 = os.path.join(d, ".worktrees", "20261124-m1-t3")
check("worktree T-3 có code của T-1 (tạo từ branch phiên sau merge)", os.path.isfile(os.path.join(w3, "app", "auth.txt")))

# T-2 conflict với thư mục chính
open(os.path.join(w2, "app", "a.txt"), "w").write("t2\n")
sh(w2, "git", "commit", "-qam", "[frontend-dev] 20261124-m1-t2: a")
open(os.path.join(w3, "app", "a.txt"), "w").write("t3\n")
sh(w3, "git", "commit", "-qam", "[backend-dev] 20261124-m1-t3: a")
run("set", "M-1/T-3", "MERGE_WAIT"), run("merge-begin", "M-1/T-3"), run("merge-end", "M-1/T-3", "pass")
run("set", "M-1/T-2", "MERGE_WAIT")
code, out = run("merge-begin", "M-1/T-2")
check("conflict: --abort, task về FIX, báo file conflict", code == 2 and "CONFLICT" in out and "app/a.txt" in out)
check("sau conflict thư mục chính sạch", clean())

# IT fail
sh(w2, "git", "checkout", "-q", "HEAD~1", "--", "app/a.txt")
sh(w2, "git", "commit", "-qm", "[frontend-dev] 20261124-m1-t2: bỏ sửa a")
run("set", "M-1/T-2", "MERGE_WAIT"), run("merge-begin", "M-1/T-2")
code, out = run("merge-end", "M-1/T-2", "fail", "--note", "E2E login 375")
check("IT fail: --abort, FIX kèm lý do", "FAIL" in out and clean())
run("set", "M-1/T-2", "MERGE_WAIT"), run("merge-begin", "M-1/T-2")
code, out = run("merge-end", "M-1/T-2", "pass")
check("task cuối của module merged → module DONE + tag", "✅ M-1 xong" in out and "20261124-app-m1-done" in sh(d, "git", "tag"))

code, out = run("status")
check("status: Module ✅ 1/1, task ✅ Merged", "Module ✅ 1/1" in out and out.count("✅ Merged") == 3)
code, out = run("wait", "--interval", "1", "--max", "2")
check("wait: hết việc trong pool", code == 0 and "HẾT VIỆC" in out)

# wait: agent DONE trong worktree
run("module", "M-2", "--state", "SPLIT")
run("add", "M-2/T-1", "--task-id", "20261124-m2-t1", "--title", "Nhật ký")
run("fill")
wb = os.path.join(d, ".worktrees", "20261124-m2-t1", ".agent-team", "board.db")
c = sqlite3.connect(wb)
c.execute("CREATE TABLE agent_runs (task TEXT, role TEXT, run TEXT, started_at INTEGER, last_seen INTEGER, last_tool TEXT, "
          "busy_since INTEGER, tool_timeout INTEGER, state TEXT, step TEXT, eta_min INTEGER, result TEXT, ended_at INTEGER)")
c.execute("INSERT INTO agent_runs VALUES('20261124-m2-t1','backend-dev','S3',1,strftime('%s','now'),NULL,NULL,NULL,'DONE',NULL,NULL,'ok',strftime('%s','now'))")
c.commit(); c.close()
code, out = run("wait", "--interval", "1", "--max", "3")
check("wait: agent DONE trong worktree → CÓ VIỆC", code == 0 and "M-2/T-1: backend-dev DONE" in out)
c = sqlite3.connect(wb)
c.execute("UPDATE agent_runs SET state='RUNNING', last_seen=last_seen-1200, ended_at=NULL")
c.commit(); c.close()
code, out = run("wait", "--interval", "1", "--max", "3")
check("wait: agent im quá HANG_MINUTES → exit 3", code == 3 and "⚠ backend-dev" in out)
code, out = run("resume")
check("resume: liệt kê task đang chạy + worktree", "M-2/T-1: RUNNING" in out and ".worktrees/20261124-m2-t1" in out)

PROG = os.path.join(os.path.dirname(POOL), "progress.py")
out = subprocess.run([sys.executable, PROG], input="{}", capture_output=True, text=True, cwd=d).stdout
check("status line: bảng điều phối (Module ✅, task ▶, đã merge gộp 1 dòng)", "Module ✅ 1/2" in out and "chạy 1/3" in out
      and "│ M-2/T-1 │" in out and "3 task đã merge" in out)

cfg("")
check("config không có MAX_PARALLEL → mặc định 8", "/8" in run("fill")[1])

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
