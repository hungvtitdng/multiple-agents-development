#!/usr/bin/env python3
"""Test nền dữ liệu M-DB (v0.30): thiếu migration → chỉ M-0 / M-DB chạy; task đổi / xoá bảng chung bị chặn merge.
python3 tests/test_schema.py"""
import os
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


def run(*args):
    r = subprocess.run([sys.executable, POOL, *args], capture_output=True, text=True, cwd=d, env=ENV)
    return r.returncode, r.stdout + r.stderr


def w(rel, text, base=None):
    p = os.path.join(base or d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


d = os.path.realpath(tempfile.mkdtemp())
sh(d, "git", "init", "-q", "-b", "master"), sh(d, "git", "config", "user.email", "t@t"), sh(d, "git", "config", "user.name", "t")
w(".claude/agent-team.config", 'MIGRATION_PATHS="database/migrations"\n')
w(".gitignore", ".agent-team/\n")
w("docs/database/schema.md", """# Database schema
## Nguyên tắc chung
- id UUID
## Bảng
| Bảng | Cột chính |
|---|---|
| `users` | id, name |
| `idps` | id, user_id, status |
| `cache`, `cache_locks` | bảng chuẩn |
## Trạng thái
| `khong_phai_bang` | x |
""")
w("database/migrations/0001_create_users_table.php", "<?php Schema::create('users', function ($t) {}); Schema::create('cache', fn($t) => 1);\n")
w("docs/product/APP.md", """# App
| M | Module | Gồm R | Phụ thuộc | Loại | Tag | Task-id | Người chạy | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| M-0 | Khung | R-0 | | VỪA | | | | DONE |
| M-DB | Nền dữ liệu | mọi bảng | M-0 | NHẸ | | | | TODO |
| M-2 | IDP | R-2 | M-DB | VỪA | | | | TODO |
| M-3 | Báo cáo | R-3 | M-DB | VỪA | | | | TODO |
""")
sh(d, "git", "add", "."), sh(d, "git", "commit", "-qm", "init"), sh(d, "git", "switch", "-qc", "agent/app")

code, out = run("schema")
check("schema: 4 bảng (gồm `cache`, `cache_locks` cùng 1 dòng), bảng ở mục khác không tính; thiếu idps, cache_locks → exit 1",
      code == 1 and "Schema 4 bảng" in out and "idps" in out and "cache_locks" in out and "khong_phai_bang" not in out)
code, out = run("fill")
check("fill khi thiếu migration: ⛔ báo bảng thiếu, chỉ bắt đầu debate M-DB, M-2 / M-3 chờ",
      "⛔ Nền dữ liệu chưa đủ" in out and "💬 M-DB:" in out and "💬 M-2" not in out and "💬 M-3" not in out)

w("database/migrations/0002_create_idps_table.php", "<?php Schema::create('idps', fn($t) => 1); Schema::create('cache_locks', fn($t) => 1);\n")
sh(d, "git", "add", "."), sh(d, "git", "commit", "-qm", "[backend-dev] mdb: tables")
check("đủ migration → schema ✅ exit 0", run("schema")[0] == 0)
run("module", "M-DB", "--state", "SPLIT")
code, out = run("fill")
check("đủ migration nhưng M-DB chưa DONE → M-2, M-3 chờ", "💬 M-2" not in out and "💬 M-3" not in out)

# task M-2 đổi / xoá bảng chung → chặn merge
run("module", "M-2", "--state", "DESIGN")
run("add", "M-2/T-1", "--task-id", "m2-t1", "--title", "IDP"), run("module", "M-2", "--state", "SPLIT")
run("add", "M-DB/T-1", "--task-id", "mdb-t1", "--title", "seed")
c = __import__("sqlite3").connect(os.path.join(d, ".agent-team", "board.db"))
c.execute("UPDATE pool_modules SET state='DONE' WHERE module='M-DB'"); c.execute("UPDATE pool SET state='DONE' WHERE label='M-DB/T-1'"); c.commit(); c.close()
code, out = run("fill")
wt = os.path.join(d, ".worktrees", "m2-t1")
check("M-DB DONE → task M-2 mở worktree", os.path.isdir(wt))
w("database/migrations/0003_alter_idps.php", "<?php Schema::table('idps', function ($t) { $t->dropColumn('status'); });\n", wt)
sh(wt, "git", "add", "."), sh(wt, "git", "commit", "-qm", "[backend-dev] m2-t1: drop")
run("set", "M-2/T-1", "MERGE_WAIT")
code, out = run("merge-begin", "M-2/T-1")
check("task xoá cột bảng chung (idps) → chặn merge, bảo GAP + --allow-schema-change", code == 1 and "đổi / xoá bảng chung" in out and "idps" in out)
code, out = run("merge-begin", "M-2/T-1", "--allow-schema-change")
check("Lead đã duyệt GAP → --allow-schema-change merge được", code == 0 and "merge-end" in out)
run("merge-end", "M-2/T-1", "fail", "--note", "thử")

run("add", "M-3/T-1", "--task-id", "m3-t1", "--title", "Báo cáo"), run("module", "M-3", "--state", "SPLIT")
run("fill")
wt3 = os.path.join(d, ".worktrees", "m3-t1")
w("database/migrations/0004_add_note_to_idps.php", "<?php Schema::table('idps', function ($t) { $t->string('note')->nullable(); });\n", wt3)
w("database/migrations/0005_create_reports_table.php", "<?php Schema::create('reports', fn($t) => 1);\n", wt3)
sh(wt3, "git", "add", "."), sh(wt3, "git", "commit", "-qm", "[backend-dev] m3-t1: thêm")
run("set", "M-3/T-1", "MERGE_WAIT")
code, out = run("merge-begin", "M-3/T-1")
check("thêm cột vào bảng chung + bảng riêng mới: không chặn", code == 0 and "merge-end" in out)
run("merge-end", "M-3/T-1", "pass")

app = open(os.path.join(d, "docs/product/APP.md")).read()
w("docs/product/APP.md", app + "| M-SKEL | Khung file | | M-DB | NHẸ | | | | TODO |\n| M-4 | Tài khoản | R-4 | M-DB | VỪA | | | | TODO |\n")
sh(d, "git", "add", "."), sh(d, "git", "commit", "-qm", "skel")
code, out = run("fill")
check("M-SKEL chưa DONE → không mở debate module khác (M-4 chờ), báo ⛔", "💬 M-4" not in out and "⛔ M-SKEL chưa DONE" in out)
run("module", "M-SKEL", "--state", "DONE")
code, out = run("fill")
check("M-SKEL DONE → M-4 được debate", "💬 M-4" in out and "⛔ M-SKEL" not in out)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
