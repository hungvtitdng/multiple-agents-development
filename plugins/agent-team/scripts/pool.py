#!/usr/bin/env python3
"""agent-team pool: Lead điều phối nhiều task chạy song song, mỗi task 1 git worktree, merge về branch của phiên.

Dữ liệu: bảng `pool`, `pool_modules` trong .agent-team/board.db của thư mục chính.
Config (.claude/agent-team.config, đọc lại mỗi lần chạy → đổi là tự scale):
  MAX_PARALLEL=8  WORKTREE_DIR=.worktrees  E2E_PORT_BASE=4000  INTEGRATION_CMD="..."

Lead:
  module <M-n> [--kind NHẸ|VỪA|NẶNG] [--state DESIGN|SPLIT|DONE] [--title ..]
  add <M-n/T-k> --task-id <id> --title ".." [--deps "M-1/T-1,M-2/T-3"]   (chỉ khi module đã chia task)
  fill            mở worktree cho task READY tới đủ MAX_PARALLEL (in việc Lead làm tiếp)
  set <M-n/T-k> <RUNNING|GAP|FIX|BLOCKED|MERGE_WAIT> [--note ".."]
  merge-begin <M-n/T-k>    merge --no-commit vào branch phiên; conflict → --abort, FIX
  merge-end <M-n/T-k> pass|fail [--note ".."]   pass: commit + xoá worktree + DONE; fail: --abort, FIX
  wait [--interval 30] [--max 540]   exit 0 có việc · 3 agent treo · 4 hết giờ chờ
  status | resume
"""
import argparse
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
LABEL_RE = re.compile(r"^M-(\d+|E2E)/T-\d+$")


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
    try:
        for line in open(os.path.join(root, ".claude", "agent-team.config"), encoding="utf-8", errors="ignore"):
            m = re.match(rf"^\s*{key}=(.*)$", line)
            if m:
                v = m.group(1).split("#")[0].strip().strip("'\"")
                return v or default
    except OSError:
        pass
    return default


def connect(root):
    os.makedirs(os.path.join(root, ".agent-team"), exist_ok=True)
    db = sqlite3.connect(os.environ.get("AGENT_TEAM_BOARD_DB") or os.path.join(root, ".agent-team", "board.db"), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=15000")
    db.executescript(SCHEMA)
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


def is_ready(db, r):
    if r["state"] != "WAIT":
        return False
    done = {x["label"] for x in db.execute("SELECT label FROM pool WHERE state='DONE'")}
    return all(d in done for d in deps_of(r))


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
    if a.state and a.state.upper() == "DESIGN":
        other = db.execute("SELECT module FROM pool_modules WHERE state='DESIGN' AND module!=?", (a.module,)).fetchone()
        if other:
            die(f"{other[0]} đang thiết kế: mỗi lúc chỉ 1 module debate (xong thì `module {other[0]} --state SPLIT`)")
    db.commit()
    m = db.execute("SELECT * FROM pool_modules WHERE module=?", (a.module,)).fetchone()
    print(f"{m['module']} · {m['kind'] or '-'} · {m['state']}")


def cmd_add(db, root, a):
    if not LABEL_RE.match(a.label):
        die("nhãn task dạng M-<n>/T-<k> (vd M-1/T-2)")
    mod = a.label.split("/")[0]
    m = db.execute("SELECT state FROM pool_modules WHERE module=?", (mod,)).fetchone()
    if not m or m["state"] not in ("SPLIT", "DONE"):
        die(f"{mod} chưa chốt thiết kế + chia task (`pool.py module {mod} --state SPLIT` sau debate): không thêm task của module đang debate")
    if not re.match(r"^[\w.-]+$", a.task_id):
        die("task-id chỉ gồm chữ, số, . _ - (dùng trong commit `[role] task-id: ...`)")
    for d in [x.strip() for x in (a.deps or "").split(",") if x.strip()]:
        if not LABEL_RE.match(d):
            die(f"phụ thuộc '{d}' phải dạng M-<n>/T-<k>")
    n = db.execute("SELECT count(*) FROM pool").fetchone()[0]
    db.execute("INSERT OR REPLACE INTO pool(label, task_id, module, title, deps, ord) VALUES(?,?,?,?,?,COALESCE((SELECT ord FROM pool WHERE label=?),?))",
               (a.label, a.task_id, mod, a.title, a.deps or "", a.label, n + 1))
    db.commit()
    print(f"Đã thêm {a.label} ({a.task_id})" + (f", chờ {a.deps}" if a.deps else ""))


def free_port(db, root):
    used = {r[0] for r in db.execute("SELECT port FROM pool WHERE port IS NOT NULL AND state != 'DONE'")}
    p = int(cfg(root, "E2E_PORT_BASE", "4000"))
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


def cmd_fill(db, root, a):
    limit, wdir = max_parallel(root), cfg(root, "WORKTREE_DIR", ".worktrees")
    busy = db.execute(f"SELECT count(*) FROM pool WHERE state IN ({','.join('?' * len(SLOT_STATES))})", SLOT_STATES).fetchone()[0]
    if db.execute("SELECT 1 FROM pool WHERE state='MERGING'").fetchone():
        print("Đang merge (MERGING): xong merge-end rồi fill (worktree mới phải tạo từ branch đã merge)")
        return
    ready = [r for r in db.execute("SELECT * FROM pool ORDER BY ord") if is_ready(db, r)]
    free = limit - busy
    print(f"Đang chạy {busy}/{limit} · READY {len(ready)}")
    if free <= 0 or not ready:
        return
    code, branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if code or branch in ("HEAD", "main", "master", "develop"):
        die(f"thư mục chính phải đứng ở branch của phiên (agent/<task-id app>), đang là '{branch}'")
    exclude_worktrees(root, wdir)
    for r in ready[:free]:
        path = os.path.join(root, wdir, r["task_id"])
        br = f"agent/{r['task_id']}"
        if not os.path.isdir(path):
            code, out = git(root, "worktree", "add", path, "-b", br, "HEAD")
            if code:
                code, out = git(root, "worktree", "add", path, br)  # branch đã có (chạy lại sau lỗi)
                if code:
                    print(f"✗ {r['label']}: không tạo được worktree: {out[:200]}")
                    continue
        port = r["port"] or free_port(db, root)
        os.makedirs(os.path.join(path, ".agent-team"), exist_ok=True)
        open(os.path.join(path, ".agent-team", "e2e_port"), "w").write(f"{port}\n")
        db.execute("UPDATE pool SET state='RUNNING', worktree=?, branch=?, port=?, started_at=COALESCE(started_at, ?), note=NULL WHERE label=?",
                   (os.path.relpath(path, root), br, port, int(time.time()), r["label"]))
        db.commit()
        print(f"▶ {r['label']} {r['title']} · worktree {os.path.relpath(path, root)} · branch {br} · E2E_PORT {port}")
    print("Tiếp: mỗi task mới → TASK.md `- Loại: ĐÃ CHIA` trong worktree, `cd <worktree> && echo S3 > .agent-team/stage`, `board.py plan`, gọi agent (nền)")


def cmd_set(db, root, a):
    r = row(db, a.label)
    st = a.state.upper()
    if st not in STATES or st in ("MERGING", "DONE"):
        die("trạng thái: RUNNING | GAP | FIX | BLOCKED | MERGE_WAIT | WAIT (MERGING / DONE do merge-begin / merge-end)")
    db.execute("UPDATE pool SET state=?, note=? WHERE label=?", (st, a.note, a.label))
    db.commit()
    print(f"{r['label']}: {r['state']} → {st}" + (f" ({a.note})" if a.note else ""))


def cmd_merge_begin(db, root, a):
    r = row(db, a.label)
    if r["state"] != "MERGE_WAIT":
        die(f"{a.label} đang {r['state']}: chỉ merge task MERGE_WAIT (code + test + review xong)")
    cur = db.execute("SELECT label FROM pool WHERE state='MERGING'").fetchone()
    if cur:
        die(f"{cur[0]} đang merge: merge lần lượt (merge-end trước)")
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
    it = cfg(root, "INTEGRATION_CMD", "") or "TEST_CMD + E2E toàn bộ (agent-db-clone.sh e2e)"
    print(f"Đã merge (chưa commit) {a.label}. Chạy integration test: {it}\nRồi: pool.py merge-end {a.label} pass|fail")


def maybe_module_done(db, root, mod):
    left = db.execute("SELECT count(*) FROM pool WHERE module=? AND state!='DONE'", (mod,)).fetchone()[0]
    m = db.execute("SELECT * FROM pool_modules WHERE module=?", (mod,)).fetchone()
    if left or not m or m["state"] != "SPLIT":
        return
    _, branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    tag = f"{branch.replace('agent/', '')}-{mod.lower().replace('-', '')}-done"
    code, out = git(root, "tag", tag)
    db.execute("UPDATE pool_modules SET state='DONE', tag=? WHERE module=?", (tag if not code else None, mod))
    db.commit()
    print(f"✅ {mod} xong" + (f" · tag {tag}" if not code else f" (không tạo được tag: {out[:120]})") + " · cập nhật Trạng thái DONE trong APP.md")


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
    if r["worktree"]:
        git(root, "worktree", "remove", "--force", os.path.join(root, r["worktree"]))
    db.execute("UPDATE pool SET state='DONE', ended_at=?, note=NULL WHERE label=?", (int(time.time()), a.label))
    db.commit()
    print(f"✅ {a.label} merged + IT pass (branch {r['branch']} giữ lại)")
    maybe_module_done(db, root, r["module"])


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
        ready = [r["label"] for r in db.execute("SELECT * FROM pool ORDER BY ord") if is_ready(db, r)]
        free = max_parallel(root) - busy
        merge = [r["label"] for r in db.execute("SELECT label FROM pool WHERE state='MERGE_WAIT' ORDER BY ord")]
        if stuck:
            print("CÓ AGENT TREO: TaskStop agent đó rồi gọi lại kèm lý do\n" + "\n".join(stuck))
            sys.exit(3)
        if done or (free > 0 and ready) or (merge and not db.execute("SELECT 1 FROM pool WHERE state='MERGING'").fetchone()):
            out = done + ([f"Còn {free} chỗ, READY: {', '.join(ready[:free])} → pool.py fill"] if free > 0 and ready else []) + \
                  ([f"Chờ merge: {', '.join(merge)} → pool.py merge-begin {merge[0]}"] if merge else [])
            print("CÓ VIỆC:\n" + "\n".join(out))
            sys.exit(0)
        if not rows and not ready and not merge:
            print("HẾT VIỆC trong pool (thiết kế module tiếp theo hoặc báo cáo cuối)")
            sys.exit(0)
        if time.time() - start >= a.max:
            print(f"CHƯA CÓ GÌ MỚI ({busy} task đang chạy): gọi wait lần nữa")
            sys.exit(4)
        time.sleep(a.interval)


MARK = {"WAIT": "⏳ Chờ", "RUNNING": "▶", "GAP": "⛔ GAP", "FIX": "🔧 Sửa", "BLOCKED": "⛔ Chặn",
        "MERGE_WAIT": "🔀 Chờ merge", "MERGING": "🔀 IT đang chạy", "DONE": "✅ Merged"}


def status_rows(db, root):
    out = []
    for r in db.execute("SELECT * FROM pool ORDER BY ord"):
        agents = ", ".join(x["role"] for x in wt_board(root, r) if x["state"] == "RUNNING") if r["state"] in ("RUNNING", "FIX", "GAP") else ""
        st = MARK.get(r["state"], r["state"])
        if r["state"] == "WAIT":
            st = "🟢 READY" if is_ready(db, r) else "⏳ Chờ " + ",".join(d.split("/")[-1] if d.split("/")[0] == r["module"] else d for d in deps_of(r))
        elif r["state"] in ("RUNNING", "FIX", "GAP"):
            stg = wt_stage(root, r)
            st += (f" {stg}" if stg else "") + (f" {(int(time.time()) - r['started_at']) // 60}p" if r["started_at"] else "")
        if r["note"] and r["state"] in ("FIX", "GAP", "BLOCKED"):
            st += f" · {r['note'][:30]}"
        out.append((r["label"], r["title"], agents, st, r["state"]))
    return out


def cmd_status(db, root, a):
    mods = db.execute("SELECT * FROM pool_modules ORDER BY ord").fetchall()
    design = [m["module"] for m in mods if m["state"] == "DESIGN"]
    rows = status_rows(db, root)
    busy = sum(1 for x in rows if x[4] in SLOT_STATES)
    print(f"Module ✅ {sum(1 for m in mods if m['state'] == 'DONE')}/{len(mods)} · thiết kế: {', '.join(design) or '-'} · chạy {busy}/{max_parallel(root)}")
    for label, title, agents, st, _ in rows:
        print(f"  {label:<10} {title[:30]:<30} {agents[:24]:<24} {st}")


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
    mb = sp.add_parser("merge-begin")
    mb.add_argument("label")
    me = sp.add_parser("merge-end")
    me.add_argument("label"), me.add_argument("result", choices=["pass", "fail"]), me.add_argument("--note")
    w = sp.add_parser("wait")
    w.add_argument("--interval", type=int, default=30), w.add_argument("--max", type=int, default=540)
    a = p.parse_args(argv)
    root = find_root()
    db = connect(root)
    globals()[f"cmd_{a.cmd.replace('-', '_')}"](db, root, a)


if __name__ == "__main__":
    main()
