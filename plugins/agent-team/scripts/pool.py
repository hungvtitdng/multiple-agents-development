#!/usr/bin/env python3
"""agent-team pool: Lead điều phối nhiều task chạy song song, mỗi task 1 git worktree, merge về branch của phiên.

Dữ liệu: bảng `pool`, `pool_modules` trong .agent-team/board.db của thư mục chính.
Config (.claude/agent-team.config, đọc lại mỗi lần chạy → đổi là tự scale):
  MAX_PARALLEL=8 (task + debate)  MAX_DEBATE=4  WORKTREE_DIR=.worktrees  E2E_PORT_BASE=4000  INTEGRATION_CMD="..."

Lead:
  module <M-n> [--kind NHẸ|VỪA|NẶNG] [--state DESIGN|SPLIT|DONE] [--title ..]
  add <M-n/T-k> --task-id <id> --title ".." [--deps "M-1/T-1,M-2/T-3"]   (chỉ khi module đã chia task)
  fill            mở worktree cho task READY tới đủ MAX_PARALLEL (in việc Lead làm tiếp)
  set <M-n/T-k> <RUNNING|GAP|FIX|BLOCKED|MERGE_WAIT> [--note ".."]
  commit <M-n/T-k | task-id> <role> "<mô tả>" [--set <STATE>]   agent xong: add file vùng của role + commit `[role] task-id: mô tả`, 1 dòng kết quả
  merge-begin <M-n/T-k>    merge --no-commit vào branch phiên; conflict → --abort, FIX
  merge-end <M-n/T-k> pass|fail [--note ".."]   pass: commit + xoá worktree + DONE; fail: --abort, FIX
  wait [--interval 30] [--max 540]   exit 0 có việc (kể cả develop có commit mới) · 3 agent treo · 4 hết giờ chờ
Nền dữ liệu:
  schema          bảng trong SCHEMA_DOC (mặc định docs/database/schema.md, mục `## Bảng`) đã có migration chưa
Team (Phase B / C):
  handoff         kiểm bàn giao cuối Phase B
  claimable       module nhận được ngay / chờ / đã có người nhận
  claim <M-n>     nhận module: branch task/YYYYMMDD-<DEV_ID>-m<n> từ origin/BASE_BRANCH, ghi Người chạy, push
  reconcile       task có branch đã nằm trong branch phiên (user merge tay) → DONE + dọn worktree
  sync            đồng bộ origin/BASE_BRANCH vào branch hiện tại (conflict → --abort, báo file)
  status | resume
"""
import argparse
import glob
import os
import re
import sqlite3
import subprocess
import sys
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS pool (
  label TEXT PRIMARY KEY, task_id TEXT NOT NULL UNIQUE, module TEXT NOT NULL, title TEXT NOT NULL, deps TEXT,
  state TEXT NOT NULL DEFAULT 'WAIT', worktree TEXT, branch TEXT, port INTEGER, note TEXT, ord INTEGER,
  started_at INTEGER, ended_at INTEGER);
CREATE TABLE IF NOT EXISTS pool_modules (
  module TEXT PRIMARY KEY, title TEXT, kind TEXT, state TEXT NOT NULL DEFAULT 'WAIT', tag TEXT, ord INTEGER);
"""
SLOT_STATES = ("RUNNING", "FIX", "GAP")  # chiếm chỗ (worktree đang làm)
STATES = ("WAIT", "RUNNING", "GAP", "FIX", "BLOCKED", "MERGE_WAIT", "MERGING", "DONE")
LABEL_RE = re.compile(r"^M-(\d+|E2E|DB|SKEL(?:-BE|-FE)?)/T-\d+$")


def die(msg, code=1):
    sys.stderr.write(f"pool: {msg}\n")
    sys.exit(code)


def find_root():
    d = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            die("không thấy .claude/agent-team.config (chạy ở thư mục chính của project)")
        d = os.path.dirname(d)


def cfg(root, key, default):
    """.claude/agent-team.local.config (riêng mỗi dev, gitignore) trước, rồi .claude/agent-team.config."""
    for name in ("agent-team.local.config", "agent-team.config"):
        try:
            for line in open(os.path.join(root, ".claude", name), encoding="utf-8", errors="ignore"):
                m = re.match(rf"^\s*{key}=(.*)$", line)
                if m:
                    v = m.group(1).split("#")[0].strip().strip("'\"")
                    if v:
                        return v
                    if name == "agent-team.config":
                        return default
        except OSError:
            pass
    return default


def connect(root):
    os.makedirs(os.path.join(root, ".agent-team"), exist_ok=True)
    db = sqlite3.connect(os.environ.get("AGENT_TEAM_BOARD_DB") or os.path.join(root, ".agent-team", "board.db"), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=15000")
    db.executescript(SCHEMA)
    if "design_at" not in {r[1] for r in db.execute("PRAGMA table_info(pool_modules)")}:  # board.db cũ
        db.execute("ALTER TABLE pool_modules ADD COLUMN design_at INTEGER")
        db.commit()
    return db


def git(root, *args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def row(db, label):
    r = db.execute("SELECT * FROM pool WHERE label=?", (label,)).fetchone()
    if not r:
        die(f"không có task {label} (pool.py status)")
    return r


def deps_of(r):
    return [x.strip() for x in (r["deps"] or "").split(",") if x.strip()]


def is_ready(db, r, root=None):
    """Task READY: WAIT, task phụ thuộc đã merge, module đã chia task (SPLIT), module phụ thuộc đủ (code: DONE · contract: có file)."""
    if r["state"] != "WAIT":
        return False
    done = {x["label"] for x in db.execute("SELECT label FROM pool WHERE state='DONE'")}
    if not all(d in done for d in deps_of(r)):
        return False
    if root is None:
        return True
    m = db.execute("SELECT state FROM pool_modules WHERE module=?", (r["module"],)).fetchone()
    if m and m["state"] not in ("SPLIT", "DONE"):
        return False
    return module_deps_ok(db, root, r["module"], "code")


def max_debate(root):
    try:
        return max(1, int(cfg(root, "MAX_DEBATE", "4")))
    except ValueError:
        return 4


def app_rows(root):
    text = show(root, "", APP_MD)
    return module_table(text), dep_reasons(text)


def mod_state(db, root, m, rows=None):
    """Trạng thái module: pool_modules, hoặc DONE theo APP.md."""
    r = db.execute("SELECT state FROM pool_modules WHERE module=?", (m,)).fetchone()
    if r and r["state"] == "DONE":
        return "DONE"
    for x in rows if rows is not None else app_rows(root)[0]:
        if x["M"] == m and x.get("Trạng thái", "").upper().startswith("DONE"):
            return "DONE"
    return r["state"] if r else "WAIT"


def module_deps_ok(db, root, m, need):
    """need=design: module phụ thuộc đã chia task (biết contract) hoặc có file contract · need=code: DONE hoặc (contract) có file. M-E2E: mọi module DONE."""
    rows, reasons = app_rows(root)
    me = next((x for x in rows if x["M"] == m), None)
    if not me:
        return True
    deps = [x["M"] for x in rows if x["M"] != m] if me["deps"] == ["*"] else me["deps"]
    for d in deps:
        st = mod_state(db, root, d, rows)
        if st == "DONE":
            continue
        if me["deps"] == ["*"]:
            return False
        has_contract = reasons.get((m, d)) == "contract" and os.path.isfile(os.path.join(root, contract_path(d)))
        if has_contract or (need == "design" and st == "SPLIT"):
            continue
        return False
    return True


def module_wait(db, root, m):
    """Vì sao task của module m chưa READY dù task phụ thuộc đã xong: ['nền dữ liệu'] / module phụ thuộc chưa xong."""
    if missing_tables(root) and m not in ("M-0", "M-DB"):
        return ["nền dữ liệu (M-DB)"]
    rows, reasons = app_rows(root)
    me = next((x for x in rows if x["M"] == m), None)
    if not me:
        return []
    deps = [x["M"] for x in rows if x["M"] != m] if me["deps"] == ["*"] else me["deps"]
    out = []
    for d in deps:
        if mod_state(db, root, d, rows) == "DONE":
            continue
        if reasons.get((m, d)) == "contract" and os.path.isfile(os.path.join(root, contract_path(d))) and me["deps"] != ["*"]:
            continue
        out.append(d + (" (contract)" if reasons.get((m, d)) == "contract" else ""))
    return out


def plan_fill(db, root):
    """Chia slot trống theo thứ tự bảng Module: task READY của module đã chia (không giới hạn / module),
    hoặc bắt đầu debate module kế (1 slot, tối đa MAX_DEBATE debate cùng lúc). Trả (task, module debate, debate chờ)."""
    limit, maxdeb = max_parallel(root), max_debate(root)
    tasks = db.execute(f"SELECT count(*) FROM pool WHERE state IN ({','.join('?' * len(SLOT_STATES))})", SLOT_STATES).fetchone()[0]
    debating = db.execute("SELECT count(*) FROM pool_modules WHERE state='DESIGN'").fetchone()[0]
    free = limit - tasks - debating
    rows, _ = app_rows(root)
    order = [x["M"] for x in rows] + [m["module"] for m in db.execute("SELECT module FROM pool_modules ORDER BY ord")
                                     if m["module"] not in {x["M"] for x in rows}]
    start_t, start_d, wait_d = [], [], []
    miss = missing_tables(root)  # thiếu migration → chỉ M-0 / M-DB chạy, module khác chờ nền dữ liệu
    mdb_open = any(x["M"] == "M-DB" for x in rows) and mod_state(db, root, "M-DB", rows) != "DONE"
    skel_open = any(x["M"].startswith("M-SKEL") and mod_state(db, root, x["M"], rows) != "DONE" for x in rows)
    for m in order:
        st = mod_state(db, root, m, rows)
        if (miss or mdb_open) and m not in ("M-0", "M-DB"):
            continue
        skel_wait = skel_open and m not in ("M-0", "M-DB") and not m.startswith("M-SKEL")
        if st in ("SPLIT", "DESIGN") and not skel_wait:
            for r in db.execute("SELECT * FROM pool WHERE module=? ORDER BY ord", (m,)):
                if free > 0 and is_ready(db, r, root):
                    start_t.append(r)
                    free -= 1
        elif st == "WAIT" and rows and m != "M-0" and module_deps_ok(db, root, m, "design"):
            if debating + len(start_d) >= maxdeb or free <= 0:
                wait_d.append(m)
            else:
                start_d.append(m)
                free -= 1
    return start_t, start_d, wait_d


def max_parallel(root):
    try:
        return max(1, int(cfg(root, "MAX_PARALLEL", "8")))
    except ValueError:
        return 8


def cmd_module(db, root, a):
    cur = db.execute("SELECT * FROM pool_modules WHERE module=?", (a.module,)).fetchone()
    if not cur:
        n = db.execute("SELECT count(*) FROM pool_modules").fetchone()[0]
        db.execute("INSERT INTO pool_modules(module, ord) VALUES(?,?)", (a.module, n + 1))
    for k in ("kind", "state", "title"):
        v = getattr(a, k)
        if v:
            db.execute(f"UPDATE pool_modules SET {k}=? WHERE module=?", (v.upper() if k == "state" else v, a.module))
            if k == "state" and v.upper() == "DESIGN":
                db.execute("UPDATE pool_modules SET design_at=COALESCE(design_at, ?) WHERE module=?", (int(time.time()), a.module))
    if a.state and a.state.upper() == "DESIGN":
        others = [x[0] for x in db.execute("SELECT module FROM pool_modules WHERE state='DESIGN' AND module!=?", (a.module,))]
        if len(others) >= max_debate(root):
            die(f"đang debate {len(others)} module ({', '.join(others)}) = MAX_DEBATE: chờ 1 module chia task xong (`--state SPLIT`)")
    db.commit()
    m = db.execute("SELECT * FROM pool_modules WHERE module=?", (a.module,)).fetchone()
    print(f"{m['module']} · {m['kind'] or '-'} · {m['state']}")


def cmd_add(db, root, a):
    if not LABEL_RE.match(a.label):
        die("nhãn task dạng M-<n>/T-<k> (vd M-1/T-2)")
    mod = a.label.split("/")[0]
    m = db.execute("SELECT state FROM pool_modules WHERE module=?", (mod,)).fetchone()
    if not m or m["state"] not in ("DESIGN", "SPLIT", "DONE"):
        die(f"{mod} chưa debate (`pool.py fill` hoặc `module {mod} --state DESIGN`): task chỉ thêm khi đang chia task, READY sau `--state SPLIT`")
    if not re.match(r"^[\w.-]+$", a.task_id):
        die("task-id chỉ gồm chữ, số, . _ - (dùng trong commit `[role] task-id: ...`)")
    for d in [x.strip() for x in (a.deps or "").split(",") if x.strip()]:
        if not LABEL_RE.match(d):
            die(f"phụ thuộc '{d}' phải dạng M-<n>/T-<k> (hoặc M-DB/T-<k>)")
    n = db.execute("SELECT count(*) FROM pool").fetchone()[0]
    db.execute("INSERT OR REPLACE INTO pool(label, task_id, module, title, deps, ord) VALUES(?,?,?,?,?,COALESCE((SELECT ord FROM pool WHERE label=?),?))",
               (a.label, a.task_id, mod, a.title, a.deps or "", a.label, n + 1))
    db.commit()
    print(f"Đã thêm {a.label} ({a.task_id})" + (f", chờ {a.deps}" if a.deps else ""))


def free_port(db, root):
    used = {r[0] for r in db.execute("SELECT port FROM pool WHERE port IS NOT NULL AND state != 'DONE'")}
    for f in glob.glob(os.path.join(root, cfg(root, "WORKTREE_DIR", ".worktrees"), "*", ".agent-team", "e2e_port")):
        try:
            used.add(int(open(f).read().strip()))
        except (OSError, ValueError):
            pass
    p = int(cfg(root, "E2E_PORT_BASE", "8801" if cfg(root, "CLONE_MODE", "") == "schema" else "4000"))
    while p in used:
        p += 1
    return p


def exclude_worktrees(root, wdir):
    """WORKTREE_DIR vào .git/info/exclude (không sửa .gitignore của dự án)."""
    code, gitdir = git(root, "rev-parse", "--git-common-dir")
    if code:
        return
    p = os.path.join(root, gitdir, "info", "exclude") if not os.path.isabs(gitdir) else os.path.join(gitdir, "info", "exclude")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cur = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    line = "/" + wdir.strip("/") + "/"
    if line not in cur.splitlines():
        with open(p, "a", encoding="utf-8") as f:
            f.write(("" if cur.endswith("\n") or not cur else "\n") + line + "\n")


LOCAL_FILES = [".claude/agent-team.local.config", ".claude/settings.json", ".claude/settings.local.json"]  # config riêng + quyền / statusLine (có thể chưa commit)
LOCAL_DIRS = [".claude/agent-team"]  # script plugin chép vào (không commit) → worktree không có, chép từ thư mục chính


def copy_local_files(root, path):
    """Worktree chỉ có file đã commit: chép script agent-team, config riêng, quyền Claude Code (settings) từ thư mục chính sang.
    File đã có trong worktree (đã commit) thì giữ nguyên, không ghi đè."""
    import shutil
    for rel in LOCAL_FILES:
        s, t = os.path.join(root, rel), os.path.join(path, rel)
        if os.path.isfile(s) and not os.path.isfile(t):
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copy2(s, t)
    for rel in LOCAL_DIRS:
        sd = os.path.join(root, rel)
        if not os.path.isdir(sd):
            continue
        for f in os.listdir(sd):
            s, t = os.path.join(sd, f), os.path.join(path, rel, f)
            if os.path.isfile(s) and f.endswith((".py", ".sh")) and not os.path.isfile(t):
                os.makedirs(os.path.dirname(t), exist_ok=True)
                shutil.copy2(s, t)


def cmd_fill(db, root, a):
    limit, wdir = max_parallel(root), cfg(root, "WORKTREE_DIR", ".worktrees")
    if db.execute("SELECT 1 FROM pool WHERE state='MERGING'").fetchone():
        print("Đang merge (MERGING): xong merge-end rồi fill (worktree mới phải tạo từ branch đã merge)")
        return
    start_t, start_d, wait_d = plan_fill(db, root)
    miss = missing_tables(root)
    skel = app_rows(root)[0]
    if any(x["M"].startswith("M-SKEL") and mod_state(db, root, x["M"], skel) != "DONE" for x in skel):
        print("⛔ M-SKEL (BE / FE) chưa DONE → module khác chỉ được debate, chưa mở task code (tránh conflict file khung), task đang chạy vẫn chạy tiếp")
    if miss:
        print(f"⛔ Nền dữ liệu chưa đủ: {len(miss)} bảng trong schema chưa có migration ({', '.join(miss[:8])}"
              f"{' …' if len(miss) > 8 else ''}) → chỉ chạy M-0 / M-DB, module khác chờ (pool.py schema)")
    busy = db.execute(f"SELECT count(*) FROM pool WHERE state IN ({','.join('?' * len(SLOT_STATES))})", SLOT_STATES).fetchone()[0]
    deb = [x[0] for x in db.execute("SELECT module FROM pool_modules WHERE state='DESIGN'")]
    print(f"Đang chạy {busy + len(deb)}/{limit} (task {busy} · debate {len(deb)}/{max_debate(root)})"
          + (f" · chờ debate: {', '.join(wait_d)}" if wait_d else ""))
    rows, _ = app_rows(root)
    for m in start_d:
        n = db.execute("SELECT count(*) FROM pool_modules").fetchone()[0]
        idx = next((i for i, x in enumerate(rows) if x["M"] == m), n)
        db.execute("INSERT OR IGNORE INTO pool_modules(module, ord) VALUES(?,?)", (m, idx + 1))
        db.execute("UPDATE pool_modules SET state='DESIGN', design_at=COALESCE(design_at, ?) WHERE module=?", (int(time.time()), m))
        db.commit()
        print(f"💬 {m}: bắt đầu debate (1 slot) → TASK.md thiết kế ở thư mục chính, debate theo Loại, chia task → pool.py add → module {m} --state SPLIT")
    if start_t and os.path.isfile(drain_file(root)):
        print(f"⏸ drain đang bật (rebuild container): chưa mở {len(start_t)} task READY → pool.py drain --off khi xong")
        return
    if not start_t:
        return
    code, branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if code or branch in ("HEAD", "main", "master", "develop"):
        die(f"thư mục chính phải đứng ở branch của phiên (task/<task-id app>), đang là '{branch}'")
    exclude_worktrees(root, wdir)
    for r in start_t:
        path = os.path.join(root, wdir, r["task_id"])
        br = f"task/{r['task_id']}"
        if not os.path.isdir(path):
            code, out = git(root, "worktree", "add", path, "-b", br, "HEAD")
            if code:
                code, out = git(root, "worktree", "add", path, br)  # branch đã có (chạy lại sau lỗi)
                if code:
                    print(f"✗ {r['label']}: không tạo được worktree: {out[:200]}")
                    continue
        port = r["port"] or free_port(db, root)
        os.makedirs(os.path.join(path, ".agent-team"), exist_ok=True)
        copy_local_files(root, path)
        open(os.path.join(path, ".agent-team", "e2e_port"), "w").write(f"{port}\n")
        db.execute("UPDATE pool SET state='RUNNING', worktree=?, branch=?, port=?, started_at=COALESCE(started_at, ?), note=NULL WHERE label=?",
                   (os.path.relpath(path, root), br, port, int(time.time()), r["label"]))
        db.commit()
        print(f"▶ {r['label']} {r['title']} · worktree {os.path.relpath(path, root)} · branch {br} · E2E_PORT {port}")
    print("Tiếp: mỗi task mới → TASK.md `- Loại: ĐÃ CHIA` trong worktree, `cd <worktree> && echo S3 > .agent-team/stage`, `board.py plan`, gọi agent (nền)")


def main_deps(root):
    if cfg(root, "CLONE_MODE", "") != "schema":
        return
    sh_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-db.sh")
    try:
        out = subprocess.run(["bash", sh_path, "main-deps", "main"], cwd=root, capture_output=True, text=True, timeout=900)
        if out.stdout.strip() or out.returncode:
            print((out.stdout + out.stderr).strip()[-800:])
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"⚠ cài lại vendor / node_modules của thư mục chính lỗi: {e}")


def drain_file(root):
    return os.path.join(root, ".agent-team", "drain")


def testing_tasks(db, root):
    out = []
    for r in db.execute("SELECT label, state, worktree FROM pool WHERE state IN ('RUNNING','FIX','MERGING') ORDER BY ord"):
        st = ""
        if r["worktree"]:
            try:
                st = open(os.path.join(root, r["worktree"], ".agent-team", "stage")).read().strip().upper()
            except OSError:
                pass
        if r["state"] == "MERGING" or st in ("S4", "S5"):
            out.append(f"{r['label']} ({'IT' if r['state'] == 'MERGING' else st})")
    return out


def cmd_drain(db, root, a):
    if a.off:
        if os.path.isfile(drain_file(root)):
            os.remove(drain_file(root))
        print("▶ hết drain: pool.py fill mở task mới lại")
        return
    os.makedirs(os.path.dirname(drain_file(root)), exist_ok=True)
    open(drain_file(root), "w").write(f"{int(time.time())}\n")
    testing = testing_tasks(db, root)
    print("⏸ drain: fill không mở task mới (task đang chạy vẫn chạy)")
    print("Đang dùng container (test / E2E / IT): " + (", ".join(testing) if testing else "không có → rebuild được ngay"))
    print("Xong rebuild: pool.py drain --off")


def cmd_side(db, root, a):
    wdir = cfg(root, "WORKTREE_DIR", ".worktrees")
    path = os.path.join(root, wdir, a.task_id)
    rel = os.path.relpath(path, root)
    if a.done:
        _, st = git(path, "status", "--porcelain", "--untracked-files=all")
        own = (".agent-team/", *LOCAL_FILES, *[x + "/" for x in LOCAL_DIRS])
        left = [x[3:] for x in st.splitlines() if x[3:] and not x[3:].startswith(own)]
        if left:
            die(f"{rel} còn {len(left)} file chưa commit ({', '.join(left[:5])}): commit / push trước rồi --done")
        cleanup_task(root, {"task_id": a.task_id, "worktree": rel})
        code, out = git(root, "worktree", "remove", "--force", path)
        print(f"✓ xoá worktree {rel} (branch task/{a.task_id} giữ lại)" if not code else f"✗ chưa xoá được {rel}: {out[:200]} (còn file chưa commit?)")
        return
    if os.path.isdir(path):
        die(f"{rel} đã có: cd {rel}")
    exclude_worktrees(root, wdir)
    code, out = git(root, "worktree", "add", path, "-b", f"task/{a.task_id}", a.base)
    if code:
        die(f"không tạo được worktree: {out[:200]}")
    os.makedirs(os.path.join(path, ".agent-team"), exist_ok=True)
    copy_local_files(root, path)
    port = free_port(db, root)
    open(os.path.join(path, ".agent-team", "e2e_port"), "w").write(f"{port}\n")
    open(os.path.join(path, ".agent-team", "side"), "w").write(root + "\n")
    print(f"▶ task lẻ {a.task_id} · worktree {rel} · branch task/{a.task_id} (từ {a.base}) · cổng {port}")
    print(f"Mở terminal mới: cd {path} && claude  → /agent-team:task …  · xong: pool.py side {a.task_id} --done")


def cmd_set(db, root, a):
    r = row(db, a.label)
    st = a.state.upper()
    if st not in STATES or st in ("MERGING", "DONE"):
        die("trạng thái: RUNNING | GAP | FIX | BLOCKED | MERGE_WAIT | WAIT (MERGING / DONE do merge-begin / merge-end)")
    db.execute("UPDATE pool SET state=?, note=? WHERE label=?", (st, a.note, a.label))
    db.commit()
    print(f"{r['label']}: {r['state']} → {st}" + (f" ({a.note})" if a.note else ""))


def cmd_merge_begin(db, root, a):
    if os.path.isfile(drain_file(root)):
        die("đang drain (rebuild container): merge sau khi pool.py drain --off")
    r = row(db, a.label)
    if r["state"] != "MERGE_WAIT":
        die(f"{a.label} đang {r['state']}: chỉ merge task MERGE_WAIT (code + test + review xong)")
    cur = db.execute("SELECT label FROM pool WHERE state='MERGING'").fetchone()
    if cur:
        die(f"{cur[0]} đang merge: merge lần lượt (merge-end trước)")
    changes = schema_changes(root, r["branch"]) if r["module"] != "M-DB" else []
    if changes and not getattr(a, "allow_schema_change", False):
        die("task đổi / xoá bảng chung (M-DB): " + "; ".join(changes[:5]) + ". Module chỉ được thêm cột / bảng mới. "
            "Cần đổi thật → GAP, Lead duyệt + báo module dùng bảng đó, rồi merge-begin --allow-schema-change")
    code, out = git(root, "diff", "--name-only", "HEAD")
    dirty = [l for l in out.splitlines() if l and l != ".claude/agent-team.config"]  # đổi MAX_PARALLEL không chặn merge
    if dirty:
        die("thư mục chính còn thay đổi chưa commit: " + ", ".join(dirty[:5]) + ". Commit trước khi merge")
    code, out = git(root, "merge", "--no-ff", "--no-commit", r["branch"])
    if code:
        _, files = git(root, "diff", "--name-only", "--diff-filter=U")
        git(root, "merge", "--abort")
        db.execute("UPDATE pool SET state='FIX', note=? WHERE label=?", (f"conflict: {files.replace(chr(10), ', ')[:200]}", a.label))
        db.commit()
        print(f"✗ CONFLICT {a.label}: {files or out[:200]}\nĐã --abort. Task về FIX: dev rebase branch task lên branch phiên rồi sửa trong worktree.")
        sys.exit(2)
    db.execute("UPDATE pool SET state='MERGING' WHERE label=?", (a.label,))
    db.commit()
    if r["module"].startswith("M-SKEL"):
        cmd_merge_end(db, root, argparse.Namespace(label=a.label, result="pass", note=None))
        return
    tag = "@" + r["module"].lower().replace("-", "")
    it = cfg(root, "INTEGRATION_CMD", "") or (
        "TEST_CMD + E2E toàn bộ (agent-db.sh e2e)" if r["module"] == "M-E2E"
        else "TEST_CMD (TEST_MODE=mvp: E2E để M-E2E)" if cfg(root, "TEST_MODE", "").lower() == "mvp"
        else f"TEST_CMD + E2E của module (agent-db.sh e2e <task> --grep {tag} + spec đã sửa); toàn bộ E2E chỉ ở M-E2E")
    print(f"Đã merge (chưa commit) {a.label}. Chạy integration test: {it}\nRồi: pool.py merge-end {a.label} pass|fail")


def maybe_module_done(db, root, mod):
    left = db.execute("SELECT count(*) FROM pool WHERE module=? AND state!='DONE'", (mod,)).fetchone()[0]
    m = db.execute("SELECT * FROM pool_modules WHERE module=?", (mod,)).fetchone()
    if left or not m or m["state"] != "SPLIT":
        return
    _, branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    tag = f"{branch.split('/', 1)[-1]}-{mod.lower().replace('-', '')}-done"
    code, out = git(root, "tag", tag)
    db.execute("UPDATE pool_modules SET state='DONE', tag=? WHERE module=?", (tag if not code else None, mod))
    db.commit()
    print(f"✅ {mod} xong" + (f" · tag {tag}" if not code else f" (không tạo được tag: {out[:120]})") + " · cập nhật Trạng thái DONE trong APP.md")


def cleanup_task(root, r):
    safe = re.sub(r"[^a-z0-9_.-]", "-", r["task_id"].lower())
    out = []
    wt0 = os.path.join(root, r["worktree"]) if r["worktree"] else ""
    if cfg(root, "CLONE_MODE", "") == "schema" and wt0 and os.path.isdir(wt0):
        sh_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-db.sh")
        try:
            if subprocess.run(["bash", sh_path, "down", r["task_id"]], cwd=wt0, capture_output=True, timeout=120).returncode == 0:
                out.append(f"DB + process cổng của {r['task_id']}")
        except (OSError, subprocess.TimeoutExpired):
            pass
    for name in (f"agent-clone-{safe}", f"agent-e2e-{safe}"):
        try:
            if subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=60).returncode == 0:
                out.append(name)
        except (OSError, subprocess.TimeoutExpired):
            break
    wt = os.path.join(root, r["worktree"]) if r["worktree"] else ""
    if wt:
        ps = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout.splitlines()
        hit = re.compile(re.escape(wt) + r"(/|\s|$)")
        pids = [l.split(None, 1)[0] for l in ps if len(l.split(None, 1)) == 2 and hit.search(l.split(None, 1)[1])]
        pids = [p for p in pids if int(p) not in (os.getpid(), os.getppid())]
        if pids:
            subprocess.run(["kill", *pids], capture_output=True)
            out.append(f"{len(pids)} process trong worktree")
    return ", ".join(out)


def cmd_merge_end(db, root, a):
    r = row(db, a.label)
    if r["state"] != "MERGING":
        die(f"{a.label} không ở MERGING")
    if a.result == "fail":
        git(root, "merge", "--abort")
        db.execute("UPDATE pool SET state='FIX', note=? WHERE label=?", (f"IT fail: {a.note or ''}"[:200], a.label))
        db.commit()
        print(f"✗ {a.label}: integration test FAIL → đã --abort, task về FIX (dev sửa trong worktree, merge lại)")
        return
    code, out = git(root, "commit", "-m", f"[lead] {r['task_id']}: merge {a.label} {r['title']}"[:120])
    if code:
        die(f"commit merge lỗi: {out[:300]}")
    killed = cleanup_task(root, r)
    if r["worktree"]:
        git(root, "worktree", "remove", "--force", os.path.join(root, r["worktree"]))
    main_deps(root)
    db.execute("UPDATE pool SET state='DONE', ended_at=?, note=NULL WHERE label=?", (int(time.time()), a.label))
    print(f"🧹 dọn {a.label}: {killed or 'không còn process / container'} · Lead: TaskStop mọi agent + shell nền của task này")
    db.commit()
    print(f"✅ {a.label} merged" + (" (khung, không IT)" if r["module"].startswith("M-SKEL") else " + IT pass") + f" (branch {r['branch']} giữ lại)")
    maybe_module_done(db, root, r["module"])


def cmd_reconcile(db, root, a):
    done = []
    for r in db.execute("SELECT * FROM pool WHERE state NOT IN ('DONE', 'WAIT', 'MERGING') AND branch IS NOT NULL").fetchall():
        if git(root, "merge-base", "--is-ancestor", r["branch"], "HEAD")[0]:
            continue
        if not git(root, "log", "-1", "--format=%h", f"--grep={r['task_id']}:", "HEAD")[1].strip():
            continue
        cleanup_task(root, r)
        if r["worktree"]:
            git(root, "worktree", "remove", "--force", os.path.join(root, r["worktree"]))
        db.execute("UPDATE pool SET state='DONE', ended_at=?, note='merge tay' WHERE label=?", (int(time.time()), r["label"]))
        db.commit()
        done.append(r["label"])
        maybe_module_done(db, root, r["module"])
    print("reconcile: " + (", ".join(done) + " đã nằm trong branch phiên → DONE" if done else "không task nào đã merge tay"))


OWNER_ZONE = {"backend-dev": "be", "frontend-dev": "fe", "test-executor": "test"}
TEST_FILE_RE = re.compile(r"(^|/)(__tests__|__mocks__)/|(_spec|_test)\.\w+$|\.(spec|test)\.\w+$|(^|/)test_[^/]+\.py$")
SECRET_FILE_RE = re.compile(r"(^|/)(\.env(\.(?!example$|sample$|template$|dist$)[^/]+)?|id_(rsa|ed25519|ecdsa|dsa)[^/]*|\.(npmrc|pgpass|netrc)|[^/]+\.(pem|key|dump|sql\.gz|bak))$")
PROTECTED = ("main", "master", "develop")


def zone_of(root, rel):
    paths = lambda k: [os.path.normpath(x.strip("/")) for x in cfg(root, k, "").split() if x.upper() != "TODO"]
    under = lambda k: any(rel == x or rel.startswith(x + "/") for x in paths(k))
    if under("TEST_PATHS") or TEST_FILE_RE.search(rel):
        return "test"
    return "be" if under("BE_PATHS") else "fe" if under("FE_PATHS") else None


def cmd_commit(db, root, a):
    role, msg = a.role.strip().lower().split(":")[-1], " ".join(a.msg.split())
    r = row(db, a.task) if LABEL_RE.match(a.task) else None
    if a.set and not r:
        die("--set chỉ dùng với task trong pool (M-n/T-k)")
    wdir = os.path.join(root, r["worktree"]) if r and r["worktree"] else root
    if git(wdir, "branch", "--show-current")[1] in PROTECTED:
        die("không commit trên main / master / develop")
    out = subprocess.run(["git", "-C", wdir, "status", "--porcelain", "--no-renames", "-uall"], capture_output=True, text=True).stdout
    mine, take, left, secret = OWNER_ZONE.get(role), [], [], []
    for line in out.splitlines():
        f = line[3:].strip('"')
        z = zone_of(root, f)
        (secret if SECRET_FILE_RE.search(f) else left if f.startswith(".claude/") or z not in (None, mine) else take).append(f)
    done = "không có file của role để commit"
    if take:
        git(wdir, "add", "--", *take)
        code, err = git(wdir, "commit", "-q", "-m", f"[{role}] {r['task_id'] if r else a.task}: {msg}", "--", *take)
        if code:
            die(f"commit lỗi: {err[-300:]}")
        done = f"{len(take)} file · {git(wdir, 'rev-parse', '--short', 'HEAD')[1]}"
    print(f"[{role}] {a.task}: {done}"
          + (f" · còn {len(left)} file vùng role khác / .claude chưa commit: {', '.join(left[:5])}" if left else "")
          + (f" · BỎ QUA file nhạy cảm: {', '.join(secret[:5])}" if secret else ""))
    if a.set:
        a.label, a.state, a.note = a.task, a.set, None
        cmd_set(db, root, a)


def wt_board(root, r):
    p = os.path.join(root, r["worktree"] or "", ".agent-team", "board.db")
    if not r["worktree"] or not os.path.isfile(p):
        return []
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT role, state, last_seen, busy_since, tool_timeout, last_tool, ended_at FROM agent_runs").fetchall()
        con.close()
        return rows
    except sqlite3.Error:
        return []


def wt_stage(root, r):
    try:
        return open(os.path.join(root, r["worktree"], ".agent-team", "stage"), encoding="utf-8").read().strip().upper()
    except (OSError, TypeError):
        return ""


def cmd_wait(db, root, a):
    """Lead chờ: trả về khi có agent DONE mới, có chỗ trống + task READY, có agent treo, hoặc hết --max giây."""
    hang = int(cfg(root, "HANG_MINUTES", "10")) * 60
    start = int(time.time())
    if has_remote(root):  # develop có commit mới (người khác merge) → đồng bộ trước khi merge task tiếp
        fetch(root)
        code, n = git(root, "rev-list", "--count", f"HEAD..{base_ref(root)}")
        if not code and n.strip() not in ("", "0"):
            print(f"CÓ VIỆC:\n{base_ref(root)} có {n.strip()} commit mới → pool.py sync (đọc lại file đổi)")
            sys.exit(0)
    while True:
        rows = db.execute("SELECT * FROM pool WHERE state IN ('RUNNING','FIX','GAP') ORDER BY ord").fetchall()
        done, stuck = [], []
        now = int(time.time())
        for r in rows:
            for x in wt_board(root, r):
                if x["state"] == "DONE" and (x["ended_at"] or 0) >= start - a.interval:
                    done.append(f"{r['label']}: {x['role']} DONE")
                elif x["state"] == "RUNNING":
                    limit = max(hang, (x["tool_timeout"] or 0) + 60) if x["busy_since"] else hang
                    if now - x["last_seen"] > limit:
                        stuck.append(f"{r['label']}: ⚠ {x['role']} im {(now - x['last_seen']) // 60}p · {x['last_tool'] or ''}")
        busy = len(rows)
        st_t, st_d, _ = plan_fill(db, root)
        draining = os.path.isfile(drain_file(root))
        ready = ([] if draining else [r["label"] for r in st_t]) + [f"💬 debate {m}" for m in st_d]
        free = len(ready)
        merge = [] if draining else [r["label"] for r in db.execute("SELECT label FROM pool WHERE state='MERGE_WAIT' ORDER BY ord")]
        if draining and not testing_tasks(db, root):
            print("DRAIN XONG: không task nào đang test / IT → rebuild container, rồi pool.py drain --off")
            sys.exit(0)
        if stuck:
            print("CÓ AGENT TREO: TaskStop agent đó rồi gọi lại kèm lý do\n" + "\n".join(stuck))
            sys.exit(3)
        if done or (free > 0 and ready) or (merge and not db.execute("SELECT 1 FROM pool WHERE state='MERGING'").fetchone()):
            out = done + ([f"Còn chỗ: {', '.join(ready)} → pool.py fill"] if free > 0 and ready else []) + \
                  ([f"Chờ merge: {', '.join(merge)} → pool.py merge-begin {merge[0]}"] if merge else [])
            print("CÓ VIỆC:\n" + "\n".join(out))
            sys.exit(0)
        if not rows and not ready and not merge and not db.execute("SELECT 1 FROM pool_modules WHERE state='DESIGN'").fetchone():
            print("HẾT VIỆC trong pool (thiết kế module tiếp theo hoặc báo cáo cuối)")
            sys.exit(0)
        if time.time() - start >= a.max:
            print(f"CHƯA CÓ GÌ MỚI ({busy} task đang chạy): gọi wait lần nữa")
            sys.exit(4)
        status_md(root)
        time.sleep(a.interval)


def status_md(root):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("progress", os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.py"))
        prog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prog)
        prog.write_md(root)
    except Exception:
        pass


MARK = {"WAIT": "⏳ Chờ", "RUNNING": "▶", "GAP": "⛔ GAP", "FIX": "🔧 Sửa", "BLOCKED": "⛔ Chặn",
        "MERGE_WAIT": "🔀 Chờ merge", "MERGING": "🔀 IT đang chạy", "DONE": "✅ Merged"}


def status_rows(db, root):
    out = []
    for r in db.execute("SELECT * FROM pool ORDER BY ord"):
        agents = ", ".join(x["role"] for x in wt_board(root, r) if x["state"] == "RUNNING") if r["state"] in ("RUNNING", "FIX", "GAP") else ""
        st = MARK.get(r["state"], r["state"])
        if r["state"] == "WAIT":
            st = "🟢 READY" if is_ready(db, r, root) else "⏳ Chờ " + ",".join(d.split("/")[-1] if d.split("/")[0] == r["module"] else d for d in deps_of(r))
        elif r["state"] in ("RUNNING", "FIX", "GAP"):
            stg = wt_stage(root, r)
            st += (f" {stg}" if stg else "") + (f" {(int(time.time()) - r['started_at']) // 60}p" if r["started_at"] else "")
        if r["note"] and r["state"] in ("FIX", "GAP", "BLOCKED"):
            st += f" · {r['note'][:30]}"
        out.append((r["label"], r["title"], agents, st, r["state"]))
    return out


def cmd_status(db, root, a):
    """Bảng giống status line (progress.py), không cắt dòng: module · task · Debate · Code · Test · Review · Merge · trạng thái."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("progress", os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.py"))
    prog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prog)
    print("\n".join(prog.pool_block(root, all_rows=True)) or "Pool trống")
    _, _, wait_d = plan_fill(db, root)
    if wait_d:
        print(f"Chờ debate: {', '.join(wait_d)} (đủ {max_debate(root)} debate / hết slot)")
    miss = missing_tables(root)
    if miss:
        print(f"⛔ Thiếu migration {len(miss)} bảng: {', '.join(miss[:8])} → M-DB trước")


def cmd_resume(db, root, a):
    rows = db.execute("SELECT * FROM pool WHERE state NOT IN ('DONE','WAIT') ORDER BY ord").fetchall()
    if not rows:
        print("Không có task dở trong pool: pool.py fill để chạy task READY")
        return
    for r in rows:
        if r["state"] == "MERGING":
            print(f"{r['label']}: đang merge dở → chạy lại integration test rồi merge-end pass|fail (hoặc `git merge --abort` + set MERGE_WAIT)")
        elif r["state"] in SLOT_STATES:
            ok = r["worktree"] and os.path.isdir(os.path.join(root, r["worktree"]))
            print(f"{r['label']}: {r['state']} · {r['worktree']} {'' if ok else '(MẤT worktree: git worktree add ' + r['worktree'] + ' ' + (r['branch'] or '') + ')'}"
                  f" → `cd {r['worktree']}` làm tiếp theo resume.md (agent DONE thì không gọi lại)")
        else:
            print(f"{r['label']}: {r['state']}" + (f" · {r['note']}" if r["note"] else ""))
    print("Sau đó: pool.py fill (đủ MAX_PARALLEL) → pool.py wait")


# ---------- team: nhận module, đồng bộ develop, kiểm bàn giao (v0.29) ----------
APP_MD = "docs/product/APP.md"
DEP_REASON_RE = re.compile(r"(M-(?:\d+|E2E|DB|SKEL(?:-BE|-FE)?))\s*(?:→|->)\s*(M-(?:\d+|DB|SKEL(?:-BE|-FE)?))\s*\((contract|code)\)\s*:\s*\S")
ENV_USE_RES = [  # chỉ key bắt buộc: có giá trị mặc định trong code (env('X', 'mặc định')) thì không tính
    re.compile(r"\benv\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\)"),                                # Laravel env('X')
    re.compile(r"\bENV(?:\[\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\]|\.fetch\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\))"),  # Rails
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]+)"),                                               # Node
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]+)"),                                          # Vite
    re.compile(r"os\.(?:getenv|environ\.get)\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\)|os\.environ\[\s*['\"]([A-Z][A-Z0-9_]+)['\"]"),  # Python
    re.compile(r"os\.Getenv\(\s*\"([A-Z][A-Z0-9_]+)\""),                                         # Go
]
ENV_BUILTIN = {"NODE_ENV", "PATH", "HOME", "CI", "PORT", "DEV", "PROD", "MODE", "SSR", "BASE_URL", "VIEWPORTS",
               "EVIDENCE_DIR", "TASK_ID", "APP_ENV", "APP_DEBUG"}


def base_ref(root):
    return f"origin/{cfg(root, 'BASE_BRANCH', 'develop')}"


def has_remote(root):
    code, out = git(root, "remote")
    return code == 0 and "origin" in out.split()


def fetch(root):
    if has_remote(root):
        git(root, "fetch", "-q", "origin")


def show(root, ref, path):
    """Nội dung file ở ref (vd origin/develop), '' nếu không có."""
    code, out = git(root, "show", f"{ref}:{path}") if ref else (1, "")
    if code:
        try:
            return open(os.path.join(root, path), encoding="utf-8").read() if not ref else ""
        except OSError:
            return ""
    return out


def exists_at(root, ref, path):
    if not ref:
        return os.path.exists(os.path.join(root, path))
    return git(root, "cat-file", "-e", f"{ref}:{path}")[0] == 0


def module_table(text):
    """[{M, Module, Gồm R, Phụ thuộc, Loại, Task-id, Người chạy, Trạng thái, deps:[...]}] theo tên cột."""
    head, rows = None, []
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if c and c[0] == "M" and "Module" in c:
            head = c
            continue
        if head and len(c) >= 2 and re.match(r"^M-(\d+|E2E|DB|SKEL(?:-BE|-FE)?)$", c[0]):
            r = dict(zip(head, c + [""] * (len(head) - len(c))))
            dep = r.get("Phụ thuộc", "")
            r["deps"] = ["*"] if re.search(r"tất cả|mọi module", dep, re.I) else re.findall(r"M-(?:\d+|DB|SKEL(?:-BE|-FE)?)\b", dep)
            rows.append(r)
        elif head and not line.strip().startswith("|"):
            head = None if rows else head
    return rows


def dep_reasons(text):
    return {(a, b): kind for a, b, kind in DEP_REASON_RE.findall(text)}


def contract_path(m):
    return f"docs/product/contracts/{m}.md"


def mod_branch_suffix(m):
    return "m" + m.split("-")[1].lower()


def taken_remote(root, m, me):
    """Branch module của người khác trên remote: task/YYYYMMDD-<dev>-m<n> (kết thúc đúng -m<n>)."""
    code, out = git(root, "branch", "-r", "--list", "origin/task/*", "origin/agent/*")
    suf = "-" + mod_branch_suffix(m)
    hits = [b.strip() for b in out.splitlines() if b.strip().endswith(suf)]
    return [b for b in hits if not (me and f"-{me}-" in b)]


def classify(root, ref, me):
    """(nhận được, chờ phụ thuộc, đã có người nhận, xong) theo APP.md ở ref."""
    text = show(root, ref, APP_MD)
    rows, reasons = module_table(text), dep_reasons(text)
    done = {r["M"] for r in rows if r.get("Trạng thái", "").upper().startswith("DONE")}
    ok, wait, taken = [], [], []
    for r in rows:
        m, st = r["M"], r.get("Trạng thái", "").upper()
        if m in done:
            continue
        who = r.get("Người chạy", "").strip()
        others = taken_remote(root, m, me) if ref else []
        if (who and who != me and (st.startswith("DESIGN") or st.startswith("DOING"))) or others:
            taken.append((m, who or ", ".join(o.split("/")[-1] for o in others)))
            continue
        deps = [x for x in rows if x["M"] != m] if r["deps"] == ["*"] else [x for x in rows if x["M"] in r["deps"]]
        miss = []
        for d in deps:
            if d["M"] in done:
                continue
            if reasons.get((m, d["M"])) == "contract" and exists_at(root, ref, contract_path(d["M"])):
                continue
            miss.append(d["M"])
        (wait if miss else ok).append((m, r.get("Module", ""), miss))
    return ok, wait, taken, sorted(done)


def cmd_claimable(db, root, a):
    fetch(root)
    ref = base_ref(root) if has_remote(root) else ""
    ok, wait, taken, done = classify(root, ref, cfg(root, "DEV_ID", ""))
    print(f"Theo {ref or 'thư mục hiện tại'} · xong {len(done)}")
    for m, title, _ in ok:
        print(f"  🟢 {m:<6} {title[:40]}  → pool.py claim {m}")
    for m, title, miss in wait:
        print(f"  ⏳ {m:<6} {title[:40]}  chờ {', '.join(miss)}")
    for m, who in taken:
        print(f"  👤 {m:<6} đang được nhận: {who}")


def set_row(text, m, **vals):
    """Sửa ô theo tên cột ở dòng module m (giữ nguyên dòng khác)."""
    out, head = [], None
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if c and c[0] == "M" and "Module" in c:
            head = c
        elif head and c and c[0] == m and line.strip().startswith("|"):
            c += [""] * (len(head) - len(c))
            for k, v in vals.items():
                if k in head:
                    c[head.index(k)] = v
            line = "| " + " | ".join(c) + " |"
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def cmd_claim(db, root, a):
    """Một người nhận 1 module (team, Phase C): branch từ develop mới nhất, ghi Người chạy, push ngay để người khác thấy."""
    me, m = cfg(root, "DEV_ID", ""), a.module
    busy = db.execute("SELECT count(*) FROM pool WHERE state NOT IN ('DONE')").fetchone()[0]
    if busy:
        die(f"máy này còn {busy} task chưa merge (pool.py status): xong module đang làm (PR) rồi mới nhận module khác")
    if not me:
        die("chưa có DEV_ID trong .claude/agent-team.local.config (tên viết tắt của bạn)")
    if not has_remote(root) or cfg(root, "PUSH", "1") == "0":
        die("nhận module theo team cần remote + PUSH=1 (người khác thấy branch đã nhận). Làm một mình: APP_BUILD=auto")
    code, out = git(root, "diff", "--name-only", "HEAD")
    dirty = [l for l in out.splitlines() if l and l != ".claude/agent-team.config"]
    if dirty:
        die("thư mục chính còn thay đổi chưa commit: " + ", ".join(dirty[:5]))
    fetch(root)
    ref = base_ref(root)
    ok, wait, taken, done = classify(root, ref, me)
    if m in done:
        die(f"{m} đã DONE trên {ref}")
    for t, who in taken:
        if t == m:
            die(f"{m} đã có người nhận: {who}")
    for t, _, miss in wait:
        if t == m:
            die(f"{m} chưa nhận được, chờ {', '.join(miss)} xong trên {ref}. Nhận được ngay: " + (", ".join(x[0] for x in ok) or "không có"))
    if m not in [x[0] for x in ok]:
        die(f"không thấy {m} trong bảng Module ở {ref}")
    tid = f"{time.strftime('%Y%m%d')}-{me}-{mod_branch_suffix(m)}"
    br = f"task/{tid}"
    code, out = git(root, "switch", "-c", br, ref)
    if code:
        die(f"không tạo được branch {br}: {out[:200]}")
    p = os.path.join(root, APP_MD)
    text = open(p, encoding="utf-8").read()
    open(p, "w", encoding="utf-8").write(set_row(text, m, **{"Người chạy": me, "Trạng thái": "DESIGN", "Task-id": tid}))
    git(root, "add", APP_MD)
    code, out = git(root, "commit", "-m", f"[lead] {tid}: nhận {m}")
    if code:
        die(f"commit lỗi: {out[:200]}")
    code, out = git(root, "push", "-u", "origin", br)
    if code:
        die(f"push lỗi (có thể người khác vừa nhận): {out[:200]}")
    db.execute("INSERT OR IGNORE INTO pool_modules(module, ord) VALUES(?, 0)", (m,))
    db.execute("UPDATE pool_modules SET state='DESIGN', design_at=COALESCE(design_at, ?) WHERE module=?", (int(time.time()), m))
    db.commit()
    print(f"✅ Đã nhận {m} · branch {br} (đã push) · task-id {tid}\n"
          f"Tiếp: thiết kế {m} theo Loại (app.md Phase C) → chia task → pool.py add → module {m} --state SPLIT → fill / wait\n"
          f"Xong: pool.py sync → integration test → PR vào {ref.split('/', 1)[1]} (người review merge), rồi dừng")


def cmd_sync(db, root, a):
    """Đồng bộ develop vào branch hiện tại: merge, báo file docs đã đổi để đọc lại; conflict → --abort, báo file."""
    if not has_remote(root):
        print("Không có remote: bỏ qua")
        return
    if db.execute("SELECT 1 FROM pool WHERE state='MERGING'").fetchone():
        die("đang merge task (MERGING): merge-end trước")
    code, out = git(root, "diff", "--name-only", "HEAD")
    if [l for l in out.splitlines() if l and l != ".claude/agent-team.config"]:
        die("thư mục chính còn thay đổi chưa commit")
    fetch(root)
    ref = base_ref(root)
    code, n = git(root, "rev-list", "--count", f"HEAD..{ref}")
    if code or n.strip() == "0":
        print(f"Đã mới nhất so với {ref}")
        return
    _, docs = git(root, "diff", "--name-only", f"HEAD...{ref}", "--", "docs/")
    _, code_files = git(root, "diff", "--name-only", f"HEAD...{ref}", "--", ".", ":!docs")
    _, br = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    code, out = git(root, "merge", "--no-ff", "-m", f"[lead] {br.split('/', 1)[-1]}: đồng bộ {ref}", ref)
    if code:
        _, files = git(root, "diff", "--name-only", "--diff-filter=U")
        git(root, "merge", "--abort")
        print(f"✗ CONFLICT khi đồng bộ {ref}: {files or out[:200]}\nĐã --abort. Không tự gộp code người khác: báo user file conflict.")
        sys.exit(2)
    print(f"✅ Đã đồng bộ {n.strip()} commit từ {ref}")
    if docs:
        print("Đọc lại (KB / tài liệu đổi): " + ", ".join(docs.splitlines()[:15]))
        if any(re.search(r"contracts/|APP\.md|business-rules|roles-and-permissions|domain-model|decisions/", f) for f in docs.splitlines()):
            print("⚠ Có contract / quy tắc / quyền / ADR đổi: kiểm module đang làm có dùng không → có thì GAP, dừng task liên quan")
    if code_files:
        print(f"{len(code_files.splitlines())} file code đổi → `graphify update .` (nếu dùng); task đang chạy merge lại sẽ chạy IT trên code mới")


def env_keys_used(root):
    paths = " ".join(cfg(root, k, "") for k in ("BE_PATHS", "FE_PATHS")).split() or ["."]
    used = set()
    for base in paths:
        top = os.path.join(root, base)
        walk = [(os.path.dirname(top), [], [os.path.basename(top)])] if os.path.isfile(top) else os.walk(top)
        for d, dirs, files in walk:
            dirs[:] = [x for x in dirs if x not in ("node_modules", "vendor", ".git", "storage", "tmp", "dist", "build", "public")]
            for f in files:
                if not f.endswith((".php", ".rb", ".js", ".ts", ".tsx", ".jsx", ".vue", ".py", ".go", ".yml", ".yaml")):
                    continue
                try:
                    t = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                for r in ENV_USE_RES:
                    for m in r.findall(t):
                        used.update([m] if isinstance(m, str) else [x for x in m if x])
    return used - ENV_BUILTIN


def cmd_handoff(db, root, a):
    """Kiểm bàn giao cuối Phase B: đủ thì team mới nhận module (Phase C)."""
    text = show(root, "", APP_MD)
    rows, reasons, res = module_table(text), dep_reasons(text), []

    def item(ok, name, detail=""):
        res.append(ok)
        print(f"{'✅' if ok else '❌'} {name}" + (f": {detail}" if detail else ""))

    gc = os.path.join(root, ".claude", "agent-team", "gap-check.py")
    if os.path.isfile(gc):
        r = subprocess.run([sys.executable, gc], cwd=root, capture_output=True, text=True)
        item(r.returncode == 0, "gap-check (tài liệu app đủ, SPEC mới)", "" if r.returncode == 0 else r.stdout.strip().splitlines()[-1][:120] if r.stdout.strip() else "lỗi")
    else:
        item(False, "gap-check", "thiếu .claude/agent-team/gap-check.py")
    bad = [r["M"] for r in rows if not r.get("Loại") or not r.get("Gồm R")]
    item(bool(rows) and not bad, "bảng Module có Loại + Gồm R", ", ".join(bad))
    nore = [f"{r['M']}→{d}" for r in rows for d in r["deps"] if d != "*" and (r["M"], d) not in reasons]
    item(not nore, "mỗi phụ thuộc có lý do (mục `## Lý do phụ thuộc`: `- M-5 → M-1 (contract|code): ...`)", ", ".join(nore[:8]))
    heavy = [r["M"] for r in rows if (r.get("Loại", "").split() or [""])[0].upper() in ("NẶNG", "LỚN")]
    noc = [m for m in heavy if not os.path.isfile(os.path.join(root, contract_path(m)))]
    item(not noc, "contract module NẶNG (docs/product/contracts/M-n.md)", ", ".join(noc))
    tabs = schema_tables(root)
    if tabs:
        miss = missing_tables(root)
        item(not miss, f"nền dữ liệu: mọi bảng trong schema ({len(tabs)}) có migration (M-DB)", ("thiếu: " + ", ".join(miss[:10])) if miss else "")
        mdb = next((r for r in rows if r["M"] == "M-DB"), None)
        item(bool(mdb) and mdb.get("Trạng thái", "").upper().startswith("DONE"), "M-DB DONE trong bảng Module")
    else:
        item(False, f"schema: không thấy mục `## Bảng` trong {cfg(root, 'SCHEMA_DOC', SCHEMA_DOC_DEFAULT)} (danh sách bảng để kiểm M-DB)")
    m0 = next((r for r in rows if r["M"] == "M-0"), None)
    m0_ok = bool(m0) and m0.get("Trạng thái", "").upper().startswith("DONE")
    if m0_ok and m0.get("Task-id"):
        tt = show(root, "", f"docs/agent-tasks/{m0['Task-id']}/TASK.md")
        for k in ("Kết quả test", "E2E"):
            m = re.search(rf"(?m)^[\s>*-]*{k}\s*:\s*(\S+)", tt)
            if not m or m.group(1).upper().strip("`*") != "PASS":
                m0_ok = False
    item(m0_ok, "M-0 DONE, test + E2E PASS (TASK.md của M-0)")
    ex = show(root, "", ".env.example")
    have = set(re.findall(r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=", ex))
    miss = sorted(env_keys_used(root) - have)
    item(bool(ex) and not miss, ".env.example đủ key code đang dùng", ("thiếu: " + ", ".join(miss[:10])) if miss else ("không có .env.example" if not ex else ""))
    item(bool(cfg(root, "SEED_CMD", "")), "SEED_CMD (DB mới + dữ liệu mẫu cho test / E2E, máy nào cũng chạy được)", "chưa ghi trong config")
    readme = show(root, "", "README.md")
    item(bool(re.search(r"(?mi)^#+\s*Chạy dự án lần đầu", readme)), "README có mục \"Chạy dự án lần đầu\" (cài, .env, docker, seed, test)")
    ok, wait, taken, done = classify(root, "", cfg(root, "DEV_ID", ""))
    print(f"Nhận được ngay sau bàn giao: {', '.join(x[0] for x in ok) or 'không có (xem lại phụ thuộc)'}")
    if wait:
        print("Chờ: " + "; ".join(f"{m} ← {', '.join(x)}" for m, _, x in wait[:8]))
    if not all(res):
        sys.exit(1)
    print("BÀN GIAO ĐỦ: commit, push, PR vào nhánh gốc; báo team danh sách module nhận được")


# ---------- nền dữ liệu M-DB: mọi bảng trong schema có migration trước Phase C (v0.30) ----------
SCHEMA_DOC_DEFAULT = "docs/database/schema.md"
MIGRATION_DIRS_DEFAULT = ["database/migrations", "db/migrate", "migrations", "prisma/migrations", "src/migrations", "alembic/versions"]
CREATE_RES = [
    re.compile(r"Schema::create\(\s*['\"]([A-Za-z0-9_]+)['\"]"),            # Laravel
    re.compile(r"create_table\s*\(?\s*[:'\"]([A-Za-z0-9_]+)"),                # Rails
    re.compile(r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([A-Za-z0-9_]+)"),  # SQL
    re.compile(r"createTable\(\s*['\"]([A-Za-z0-9_]+)['\"]"),                 # Knex / TypeORM / Sequelize
    re.compile(r"op\.create_table\(\s*['\"]([A-Za-z0-9_]+)['\"]"),            # Alembic
]
TABLE_REF_RES = [  # bảng mà migration đụng tới
    re.compile(r"Schema::(?:table|drop|dropIfExists|rename)\(\s*['\"]([A-Za-z0-9_]+)['\"]"),
    re.compile(r"(?:change_table|drop_table|rename_table|remove_column|rename_column|change_column|remove_columns)\s*\(?\s*[:'\"]([A-Za-z0-9_]+)"),
    re.compile(r"(?i)(?:ALTER|DROP)\s+TABLE\s+(?:IF\s+EXISTS\s+)?[`\"]?([A-Za-z0-9_]+)"),
    re.compile(r"(?:alterTable|dropTable|renameTable)\(\s*['\"]([A-Za-z0-9_]+)['\"]"),
    re.compile(r"op\.(?:alter_column|drop_table|drop_column)\(\s*['\"]([A-Za-z0-9_]+)['\"]"),
]
DESTRUCTIVE_RE = re.compile(  # đổi / xoá (thêm cột mới thì được)
    r"dropColumn|renameColumn|->change\(\)|Schema::(?:drop|dropIfExists|rename)\b|dropForeign|dropIndex|dropUnique"
    r"|\b(?:remove_column|remove_columns|rename_column|change_column|drop_table|rename_table)\b"
    r"|(?i:DROP\s+TABLE|ALTER\s+TABLE\s+\S+\s+(?:DROP|RENAME|MODIFY|ALTER\s+COLUMN|CHANGE))"
    r"|\b(?:dropTable|renameTable|dropColumn|renameColumn)\(|op\.(?:drop_table|drop_column|alter_column)\(")


def schema_tables(root):
    """Tên bảng trong mục `## Bảng` của SCHEMA_DOC (cột đầu, tên trong backtick). [] nếu không có file / mục."""
    text = show(root, "", cfg(root, "SCHEMA_DOC", SCHEMA_DOC_DEFAULT))
    m = re.search(r"(?ms)^##\s+Bảng\s*$(.*?)(?=^##\s)", text + "\n## _")
    out = []
    for line in (m.group(1) if m else "").splitlines():
        c = line.strip().strip("|").split("|")
        if line.strip().startswith("|") and c and "`" in c[0]:
            out += [t for t in re.findall(r"`([A-Za-z0-9_]+)`", c[0]) if t not in out]
    return out


def migration_dirs_of(root):
    v = cfg(root, "MIGRATION_PATHS", "")
    dirs = [x.strip("/") for x in v.split() if x.upper() != "TODO"] if v else []
    return dirs or [x for x in MIGRATION_DIRS_DEFAULT if os.path.isdir(os.path.join(root, x))]


def migrated_tables(root):
    found = set()
    for d in migration_dirs_of(root):
        for dp, _, files in os.walk(os.path.join(root, d)):
            for f in files:
                try:
                    t = open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                for r in CREATE_RES:
                    found.update(r.findall(t))
                m = re.search(r"create_([a-z0-9_]+?)_table", f)
                if m:
                    found.add(m.group(1))
    return found


def missing_tables(root):
    tabs = schema_tables(root)
    if not tabs:
        return []
    have = migrated_tables(root)
    return [t for t in tabs if t not in have]


def cmd_schema(db, root, a):
    tabs = schema_tables(root)
    if not tabs:
        print(f"Không thấy mục `## Bảng` trong {cfg(root, 'SCHEMA_DOC', SCHEMA_DOC_DEFAULT)}: bỏ qua kiểm nền dữ liệu")
        return
    miss = missing_tables(root)
    print(f"Schema {len(tabs)} bảng · có migration {len(tabs) - len(miss)} · thiếu {len(miss)}")
    if miss:
        print("Thiếu: " + ", ".join(miss) + "\n→ làm M-DB trước (migration + model + quan hệ + enum + factory + seeder), module khác chờ")
        sys.exit(1)
    print("✅ Nền dữ liệu đủ: module chỉ phụ thuộc M-DB chạy song song được")


def schema_changes(root, branch):
    """Migration mới trong branch task mà đổi / xoá bảng chung (bảng có trong schema). Thêm cột / bảng mới thì không tính."""
    tabs = set(schema_tables(root))
    if not tabs:
        return []
    code, files = git(root, "diff", "--name-only", "--diff-filter=A", f"HEAD...{branch}", "--", *migration_dirs_of(root))
    hits = []
    for f in files.splitlines() if not code else []:
        code2, t = git(root, "show", f"{branch}:{f}")
        if code2:
            continue
        if not DESTRUCTIVE_RE.search(t):
            continue
        refs = {x for r in TABLE_REF_RES for x in r.findall(t)}
        hits += [f"{f} → {name}" for name in sorted(refs & tabs)]
    return hits


def main(argv=None):
    p = argparse.ArgumentParser(prog="pool.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("module")
    m.add_argument("module"), m.add_argument("--kind"), m.add_argument("--state"), m.add_argument("--title")
    ad = sp.add_parser("add")
    ad.add_argument("label"), ad.add_argument("--task-id", required=True), ad.add_argument("--title", required=True), ad.add_argument("--deps")
    sp.add_parser("fill"), sp.add_parser("status"), sp.add_parser("resume")
    s = sp.add_parser("set")
    s.add_argument("label"), s.add_argument("state"), s.add_argument("--note")
    cm = sp.add_parser("commit", help="agent xong: commit file vùng của role trong worktree của task")
    cm.add_argument("task"), cm.add_argument("role"), cm.add_argument("msg"), cm.add_argument("--set")
    mb = sp.add_parser("merge-begin")
    mb.add_argument("label"), mb.add_argument("--allow-schema-change", action="store_true", help="đã duyệt GAP đổi bảng chung")
    sp.add_parser("schema", help="bảng trong schema đã có migration chưa (thiếu → chỉ chạy M-0 / M-DB)")
    me = sp.add_parser("merge-end")
    me.add_argument("label"), me.add_argument("result", choices=["pass", "fail"]), me.add_argument("--note")
    sp.add_parser("claimable", help="module nhận được ngay / chờ phụ thuộc / đã có người nhận (theo origin/BASE_BRANCH)")
    cl = sp.add_parser("claim", help="nhận 1 module (team): branch từ develop, ghi Người chạy, push")
    cl.add_argument("module")
    sp.add_parser("sync", help="đồng bộ develop vào branch hiện tại, báo file cần đọc lại")
    sp.add_parser("handoff", help="kiểm bàn giao cuối Phase B")
    dr = sp.add_parser("drain", help="tạm không mở task mới (rebuild container), liệt kê task đang test")
    dr.add_argument("--off", action="store_true")
    sp.add_parser("reconcile", help="user đã merge tay branch task vào branch phiên → đánh DONE + dọn worktree")
    sd = sp.add_parser("side", help="task lẻ chạy song song ở terminal khác: worktree + cổng + DB riêng")
    sd.add_argument("task_id"), sd.add_argument("--base", default="HEAD"), sd.add_argument("--done", action="store_true")
    w = sp.add_parser("wait")
    w.add_argument("--interval", type=int, default=30), w.add_argument("--max", type=int, default=540)
    a = p.parse_args(argv)
    root = find_root()
    db = connect(root)
    try:
        globals()[f"cmd_{a.cmd.replace('-', '_')}"](db, root, a)
    finally:
        status_md(root)


if __name__ == "__main__":
    main()
