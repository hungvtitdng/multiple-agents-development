#!/usr/bin/env python3
"""Test pool.py (điều phối nhiều task, mỗi task 1 worktree): python3 tests/test_pool.py"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

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
        f.write('BE_PATHS="app"\nE2E_PORT_BASE=4100\nPROGRESS_LINES=table\n' + extra)


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

check("thêm task khi module chưa debate bị từ chối", run("add", "M-1/T-1", "--task-id", "x", "--title", "x")[0] == 1)
run("module", "M-1", "--kind", "NẶNG", "--state", "DESIGN")
cfg("MAX_PARALLEL=2\nMAX_DEBATE=1\n")
code, out = run("module", "M-2", "--state", "DESIGN")
check("MAX_DEBATE=1: debate module thứ 2 bị từ chối", code == 1 and "= MAX_DEBATE" in out)
cfg("MAX_PARALLEL=2\n")
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
check("tăng MAX_PARALLEL: vẫn không mở T-3 vì chờ T-1", "▶ " not in out and "Đang chạy 2/3" in out)

# T-1 code xong (Lead commit trong worktree), merge OK
open(os.path.join(w1, "app", "auth.txt"), "w").write("auth\n")
sh(w1, "git", "add", "."), sh(w1, "git", "commit", "-qm", "[backend-dev] 20261124-m1-t1: auth")
check("merge-begin khi chưa MERGE_WAIT bị từ chối", run("merge-begin", "M-1/T-1")[0] == 1)
run("set", "M-1/T-1", "MERGE_WAIT")
code, out = run("merge-begin", "M-1/T-1")
check("merge-begin: merge --no-commit, chờ integration test", code == 0 and "merge-end" in out and os.path.isfile(os.path.join(d, "app", "auth.txt")))
code, out = run("fill")
check("đang MERGING thì không fill", "Đang merge" in out)
check("status: task đang merge có thời gian chạy (từ .git/MERGE_HEAD)", re.search(r"🧪 Integration test \d\d:\d\d", run("status")[1]) is not None)
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
run("set", "M-1/T-3", "MERGE_WAIT")
cfg("MAX_PARALLEL=3\nTEST_MODE=mvp\n")
check("TEST_MODE=mvp: IT chỉ TEST_CMD, E2E để M-E2E", "TEST_MODE=mvp: E2E để M-E2E" in run("merge-begin", "M-1/T-3")[1])
cfg("MAX_PARALLEL=3\n")
run("merge-end", "M-1/T-3", "pass")
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
check("status 1 module: không cột Module, tiêu đề M-1 · 3/3 task xong, module xong gộp 1 dòng", "M-1" in out.splitlines()[0] and "3/3 task xong" in out and "│ Module" not in out and "✅ Xong" in out)
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
check("status: agent im lâu hiện ⚠ <role> im Np ở dòng task", re.search(r"▶ Code · ⚠ backend-dev im 2\dp", run("status")[1]) is not None)
code, out = run("resume")
check("resume: liệt kê task đang chạy + worktree", "M-2/T-1: RUNNING" in out and ".worktrees/20261124-m2-t1" in out)

PROG = os.path.join(os.path.dirname(POOL), "progress.py")
out = subprocess.run([sys.executable, PROG], input="{}", capture_output=True, text=True, cwd=d).stdout
check("status line: task đang làm bên trái (M-2/T-1 ▶), M-1 xong sang bảng ✅ Done bên phải cùng dòng",
      "Module ✅ 1/2" in out and "chạy 1/3" in out and "✅ Done" in out
      and re.search(r"│ M-2\s*│ T-1 Nhật ký.*▶.*│ M-1\s*│", out) is not None and "│ M-1    │ (3 task)" not in out)

cfg("")
check("config không có MAX_PARALLEL → mặc định 8", "/8" in run("fill")[1])

# ---- v0.28.0: config riêng mỗi dev + worktree nhận script không commit ----
LOC = os.path.join(d, ".claude", "agent-team.local.config")
cfg("MAX_PARALLEL=3\n")
open(LOC, "w").write("MAX_PARALLEL=6\nE2E_PORT_BASE=\n")
check("local config ghi đè MAX_PARALLEL (6), để trống thì không ghi đè", "/6" in run("fill")[1])
open(LOC, "w").write("MAX_PARALLEL=\n")
check("local MAX_PARALLEL trống → dùng config chung (3)", "/3" in run("fill")[1])
os.makedirs(os.path.join(d, ".claude", "agent-team"), exist_ok=True)
open(os.path.join(d, ".claude", "agent-team", "board.py"), "w").write("# bản chép của plugin, không commit\n")
open(os.path.join(d, ".claude", "settings.json"), "w").write('{"permissions": {"allow": ["Bash(.claude/agent-team/agent-db-clone.sh:*)"]}}\n')
run("module", "M-3", "--state", "SPLIT")
run("add", "M-3/T-1", "--task-id", "20261124-hv-m3-t1", "--title", "Báo cáo")
run("fill")
w31 = os.path.join(d, ".worktrees", "20261124-hv-m3-t1")
check("worktree mới có script + local config chép từ thư mục chính (vì không commit)",
      os.path.isfile(os.path.join(w31, ".claude", "agent-team", "board.py")) and os.path.isfile(os.path.join(w31, ".claude", "agent-team.local.config")))
check("worktree mới có .claude/settings.json (quyền agent-db-clone) chép từ thư mục chính",
      "agent-db-clone.sh" in open(os.path.join(w31, ".claude", "settings.json")).read())
os.remove(LOC)

import importlib.util as _iu
_sp = _iu.spec_from_file_location("poolmod", POOL); _pm = _iu.module_from_spec(_sp); _sp.loader.exec_module(_pm)
_wt = os.path.join(d, ".worktrees", "x-t1"); _wt2 = _wt + "0"
os.makedirs(_wt, exist_ok=True); os.makedirs(_wt2, exist_ok=True)
_sl = lambda p: subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", p + "/a"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
_p1, _p2 = _sl(_wt), _sl(_wt2)
time.sleep(0.3)
_out = _pm.cleanup_task(d, {"task_id": "x-t1", "worktree": ".worktrees/x-t1"})
time.sleep(0.3)
check("merge xong: kill process trong worktree, không đụng worktree tên gần giống", _p1.poll() is not None and _p2.poll() is None and "process" in _out)
_p2.kill()
# ---- v0.40.0: drain (rebuild container khi thêm gói hệ thống) ----
code, out = run("drain")
check("drain: bật, liệt kê task đang dùng container", code == 0 and "⏸ drain" in out and "Đang dùng container" in out)
code, out = run("merge-begin", "M-9/T-9")
check("drain: merge-begin bị chặn (IT dùng container)", code != 0 and "đang drain" in out)
code, out = run("wait", "--interval", "1", "--max", "2")
check("drain: wait báo DRAIN XONG khi không task nào đang test", "DRAIN XONG" in out or "CÓ AGENT TREO" in out)
code, out = run("drain", "--off")
check("drain --off: tắt", code == 0 and not os.path.isfile(os.path.join(d, ".agent-team", "drain")))

# ---- v0.40.0: task lẻ (pool.py side) — worktree + cổng riêng, STATUS.md có mục riêng ----
cfg("")
code, out = run("side", "FIX-12")
sp = os.path.join(d, ".worktrees", "FIX-12")
port = open(os.path.join(sp, ".agent-team", "e2e_port")).read().strip()
used = {open(f).read().strip() for f in __import__("glob").glob(os.path.join(d, ".worktrees", "*", ".agent-team", "e2e_port")) if not f.startswith(sp)}
check("side: tạo worktree + branch agent/FIX-12 + cổng không trùng task khác", code == 0 and os.path.isdir(sp) and port not in used
      and "agent/FIX-12" in out and os.path.isfile(os.path.join(sp, ".agent-team", "side")))
os.makedirs(os.path.join(sp, "docs", "agent-tasks", "FIX-12"), exist_ok=True)
open(os.path.join(sp, "docs", "agent-tasks", "FIX-12", "TASK.md"), "w").write("# FIX-12\n- Loại: NHỎ\n")
open(os.path.join(sp, ".agent-team", "stage"), "w").write("S3\n")
line = subprocess.run([sys.executable, PROG], input=json.dumps({"workspace": {"current_dir": sp}}), capture_output=True, text=True, cwd=sp).stdout
md = open(os.path.join(d, ".agent-team", "STATUS.md"), encoding="utf-8").read()
check("side: status line của task lẻ hiện task của nó; STATUS.md thư mục chính có mục ### FIX-12",
      "FIX-12" in line and "## Task lẻ" in md and "### FIX-12" in md)
code, out = run("side", "FIX-12", "--done")
check("side --done: còn file chưa commit (TASK.md) → không xoá", code != 0 and os.path.isdir(sp) and "chưa commit" in out)
sh(sp, "git", "add", "docs"), sh(sp, "git", "commit", "-qm", "fix")
code, out = run("side", "FIX-12", "--done")
check("side --done: đã commit → xoá worktree (file riêng .agent-team bỏ qua)", not os.path.isdir(sp) and "xoá worktree" in out)

# ---- v0.44.0: reconcile — user merge tay branch task vào branch phiên ----
cfg("MAX_PARALLEL=8\n")
run("add", "M-2/T-20", "--task-id", "20261126-m2-t20", "--title", "Merge tay")
run("add", "M-2/T-21", "--task-id", "20261126-m2-t21", "--title", "Chưa làm gì")
code, out = run("fill")
w20, w21 = os.path.join(d, ".worktrees", "20261126-m2-t20"), os.path.join(d, ".worktrees", "20261126-m2-t21")
open(os.path.join(w20, "app", "r20.txt"), "w").write("x\n")
sh(w20, "git", "add", "app/r20.txt"), sh(w20, "git", "commit", "-qm", "[backend-dev] 20261126-m2-t20: r20")
sh(d, "git", "merge", "-q", "--no-edit", "agent/20261126-m2-t20")
code, out = run("reconcile")
check("reconcile: task đã merge tay → DONE + xoá worktree", code == 0 and "M-2/T-20" in out and not os.path.isdir(w20))
check("reconcile: task chưa có commit nào không bị đánh DONE", os.path.isdir(w21) and "M-2/T-21" not in out)

# ---- v0.45.0: commit — agent xong, 1 lệnh add + commit file vùng của role ----
cfg('MAX_PARALLEL=8\nFE_PATHS="web"\nTEST_PATHS="tests"\n')
os.makedirs(os.path.join(w21, "web")), os.makedirs(os.path.join(w21, "docs"))
for f in ("app/c.txt", "web/c.tsx", "docs/kb.md", ".env", "app/c.test.ts"):
    open(os.path.join(w21, f), "w").write("x\n")
code, out = run("commit", "M-2/T-21", "agent-team:backend-dev", "them c")
names = sh(w21, "git", "show", "--name-only", "--format=%s", "HEAD").split()
check("commit: backend-dev → chỉ file vùng be + file ngoài mọi vùng, message `[role] task-id: mô tả`",
      code == 0 and "[backend-dev] 20261126-m2-t21: them c" in sh(w21, "git", "log", "-1", "--format=%s") and "app/c.txt" in names and "docs/kb.md" in names
      and "web/c.tsx" not in names and "app/c.test.ts" not in names)
check("commit: báo file vùng role khác còn lại, bỏ qua .env", "vùng role khác" in out and "BỎ QUA" in out and ".env" not in names)
code, out = run("commit", "M-2/T-21", "test-executor", "test c", "--set", "merge_wait")
check("commit --set: test-executor commit file test + đổi trạng thái 1 lần gọi",
      code == 0 and "app/c.test.ts" in sh(w21, "git", "show", "--name-only", "--format=", "HEAD") and "MERGE_WAIT" in out)
code, out = run("commit", "M-2/T-21", "backend-dev", "khong co gi")
check("commit: không có file của role → báo, không lỗi", code == 0 and "không có file" in out)
sh(d, "git", "switch", "-q", "master")
open(os.path.join(d, "app", "m.txt"), "w").write("x\n")
code, out = run("commit", "20261126-le", "backend-dev", "x")
check("commit: từ chối trên master", code == 1 and "master" in out)
sh(d, "git", "switch", "-q", "agent/20261124-app")
code, out = run("commit", "20261126-le", "backend-dev", "task le")
check("commit: task lẻ (task-id) commit ở thư mục chính, không cuốn theo .claude/",
      code == 0 and sh(d, "git", "show", "--name-only", "--format=%s", "HEAD").split("\n")[:3] == ["[backend-dev] 20261126-le: task le", "", "app/m.txt"])

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
