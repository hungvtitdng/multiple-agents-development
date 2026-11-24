#!/usr/bin/env python3
import glob
import json
import os
import re
import sqlite3
import sys
import time

STAGES = {
    "S1": ("SCOUT", 0, 15), "S2": ("DEBATE", 15, 35), "S3": ("CODE", 35, 60),
    "S4": ("TEST", 60, 80), "S5": ("REVIEW", 80, 95), "S6": ("ĐÓNG", 95, 100),
}
DESIGN_GATE = ["Loại", "Phương án chốt", "Security duyệt solution", "Workflow", "UI mockup"]
SMALL_GATE = ["Loại", "Tiêu chí nghiệm thu"]
BUILD_GATE = ["Lint/format", "Kết quả test", "Gap còn mở", "E2E"]
REVIEW_GATE = ["Code review", "Security review", "Cập nhật KB", "Bài học"]


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def start_dir():
    if not sys.stdin.isatty():
        try:
            data = json.loads(sys.stdin.read() or "{}")
            return (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
        except ValueError:
            pass
    return os.getcwd()


def field(text, name):
    m = re.search(rf"(?im)^[\s>*-]*{re.escape(name)}\s*:\s*(.*)$", text)
    v = re.sub(r"[`*_]", "", m.group(1)).strip() if m else ""
    return "" if v.upper().startswith("TODO") or v.startswith("<") else v


def gate_for(stage, text):
    if stage in ("S1", "S2"):
        return SMALL_GATE if field(text, "Loại").upper().startswith("NHỎ") else DESIGN_GATE
    if stage in ("S3", "S4"):
        return BUILD_GATE
    return REVIEW_GATE


def board_info(root, task):
    p = os.path.join(root, ".agent-team", "board.db")
    if not os.path.isfile(p):
        return [], 0
    try:
        db = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=2)
        r = db.execute("SELECT stage, round, roles FROM rounds WHERE task=? AND closed_at IS NULL "
                       "ORDER BY id DESC LIMIT 1", (task,)).fetchone()
        waiting = []
        if r:
            posted = {x[0] for x in db.execute(
                "SELECT DISTINCT role FROM messages WHERE task=? AND stage=? AND round=?", (task, r[0], r[1]))}
            waiting = [x for x in (r[2] or "").split(",") if x and x not in posted]
        whys = db.execute("SELECT count(*) FROM whys WHERE task=? AND status IN ('open','voting')",
                          (task,)).fetchone()[0]
        db.close()
        return waiting, whys
    except sqlite3.Error:
        return [], 0


def agent_info(root, task):
    """Agent đang chạy (heartbeat trong board.db): ⚠ khi im quá HANG_MINUTES (lệnh có timeout thì theo timeout)."""
    p = os.path.join(root, ".agent-team", "board.db")
    hang = 10
    try:
        hang = int(cfg(root, "HANG_MINUTES", "10") or 10)
    except (OSError, ValueError):
        pass
    if not os.path.isfile(p):
        return []
    import time
    try:
        db = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=2)
        rows = db.execute("SELECT role, last_seen, last_tool, busy_since, tool_timeout, step FROM agent_runs "
                          "WHERE task=? AND state='RUNNING'", (task,)).fetchall()
        db.close()
    except sqlite3.Error:
        return []
    out, now = [], int(time.time())
    for role, seen, tool, busy, tmo, step in rows:
        idle = now - seen
        limit = max(hang * 60, (tmo or 0) + 60) if busy else hang * 60
        if idle > limit:
            out.append(f"⚠ {role} im {idle // 60}p" + (f": {tool[:40]}" if tool else ""))
        else:
            out.append(f"{role} {idle}s trước" + (f" · {step}" if step else ""))  # nhịp tim: số giây nhảy về thấp = agent còn chạy
    return out


def first_word(text, name):
    return (field(text, name).split() or [""])[0].upper()


def module_dir(text):
    """`- Module: docs/product/modules/<tên>` → đường dẫn; `N/A (...)`, trống → ''."""
    m = re.match(r"(docs/\S+)", field(text, "Module"))
    return m.group(1).strip("/") if m else ""


def stage_table(stage):
    """Bảng ngang S1..S6: ✅ xong / ▶ đang làm / ⏳ chờ (theo .agent-team/stage)."""
    keys = list(STAGES)
    i = keys.index(stage)
    return box([f"{k} {STAGES[k][0].capitalize()}" for k in keys], [["✅" if j < i else "▶" if j == i else "⏳" for j in range(len(keys))]])


def table_rows(text, key):
    """Dòng bảng có cột đầu `M-n` / `T-n` (bỏ dòng chưa điền tên)."""
    rows = []
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) > 2 and re.match(rf"^{key}-(\d+|E2E|DB|SKEL)$", c[0]):
            rows.append(c)
    return rows


def read(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def phase_a_steps(root, text):
    """App / Module Phase A: 10 bước cố định, ✅ theo cổng + file có thật."""
    kind = first_word(text, "Loại")
    d = os.path.join(root, module_dir(text) if kind == "MODULE" else "docs/product")
    gate = read(os.path.join(d, "MODULE.md" if kind == "MODULE" else "APP.md"))
    files = os.listdir(d) if os.path.isdir(d) else []
    ddir = os.path.join(d, "design")
    flows = read(os.path.join(d, "flows.md"))
    if kind == "MODULE":
        last = ("Chia task + ghép KB", first_word(gate, "Ghép KB") == "YES"
                and bool(table_rows(gate, "T")) and all(r[1] for r in table_rows(gate, "T")))
    else:
        last = ("Chia module", bool(table_rows(gate, "M")) and all(r[1] for r in table_rows(gate, "M")))
    return [
        ("Intake", first_word(gate, "Intake") == "YES"),
        ("Vấn đề + mục tiêu", bool(re.search(r"(?m)^\s*-\s*G-\d+:\s*(?!TODO)\S", read(os.path.join(d, "problem.md"))))),
        ("Giải pháp + nháp nghiệp vụ", bool(re.search(r"(?m)^\|\s*R-\d+\s*\|", read(os.path.join(d, "requirements.md"))))
         and bool(re.search(r"(?m)^##\s*F-\d+:\s*(?!TODO)\S", flows))),
        ("Mockup", os.path.isdir(ddir) and any(re.match(r"^mockup-.+\.html$", f) for f in os.listdir(ddir))),
        ("Săn gap (Challenger)", first_word(gate, "Challenger") == "DONE"),
        ("Chốt câu hỏi", first_word(gate, "Debate") == "DONE"),
        ("Gửi form owner", any(re.match(r"^(QnA-v|owner-form-)\d+\.xlsx$", f) for f in files)),
        ("Owner duyệt", first_word(gate, "Owner duyệt") == "APPROVED"),
        ("Mockup + SPEC (gap-check)", first_word(gate, "Gap-check") == "PASS"),
        last,
    ]


def board_steps(root, task):
    """Danh sách bước Lead ghi (board.py plan): [(tiêu đề, trạng thái, role)]."""
    p = os.path.join(root, ".agent-team", "board.db")
    if not os.path.isfile(p):
        return []
    try:
        db = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=2)
        try:
            rows = db.execute("SELECT title, state, role, grp, started_at FROM plan_steps WHERE task=? ORDER BY n", (task,)).fetchall()
        except sqlite3.OperationalError:  # board.db của v0.20.0 chưa có cột grp
            rows = [r[:3] + (None, r[3]) for r in db.execute(
                "SELECT title, state, role, started_at FROM plan_steps WHERE task=? ORDER BY n", (task,))]
        db.close()
        return rows
    except sqlite3.Error:
        return []


def short(t, n=30):
    return t if len(t) <= n else t[:n - 1] + "…"


def steps_summary(steps):
    """bước 2/4: <tên> · còn: <các bước chưa làm>"""
    total = len(steps)
    doing = [i for i, x in enumerate(steps) if x[1] == "doing"]
    todo = [i for i, x in enumerate(steps) if x[1] == "todo"]
    if not doing and not todo:
        return [f"xong {total}/{total} bước"]
    if doing:
        out = [f"bước {'+'.join(str(i + 1) for i in doing)}/{total}: " + "; ".join(short(steps[i][0]) for i in doing)]
        rest = todo
    else:
        out = [f"bước tiếp {todo[0] + 1}/{total}: {short(steps[todo[0]][0])}"]
        rest = todo[1:]
    if rest:
        out.append("còn: " + ", ".join(short(steps[i][0], 20) for i in rest[:3]) + (" …" if len(rest) > 3 else ""))
    return out


def as_steps(phase):
    """Phase A: bước đầu chưa xong là bước đang làm."""
    first = next((i for i, (_, ok) in enumerate(phase) if not ok), None)
    return [(t, "done" if ok else "doing" if i == first else "todo", None, None, None) for i, (t, ok) in enumerate(phase)]


def parent_line(root, text):
    """App: x/N module xong · Module: x/N task xong (chỉ khi bảng đã điền)."""
    if module_dir(text) and first_word(text, "Loại") != "MODULE":
        rows, name = table_rows(read(os.path.join(root, module_dir(text), "MODULE.md")), "T"), "task"
    else:
        rows, name = table_rows(read(os.path.join(root, "docs", "product", "APP.md")), "M"), "module"
    rows = [r for r in rows if r[1]]
    if not rows:
        return ""
    done = sum(1 for r in rows if r[-1].upper().startswith("DONE"))
    return f"{'Module' if name == 'task' else 'App'}: {done}/{len(rows)} {name} xong"


def state(root):
    """(task, stage, text, steps, nguồn) của task mới nhất; None nếu chưa có stage."""
    try:
        stage = open(os.path.join(root, ".agent-team", "stage"), encoding="utf-8").read().strip().upper()
    except OSError:
        return None
    if stage not in STAGES:
        return None
    tasks = glob.glob(os.path.join(root, "docs", "agent-tasks", "*", "TASK.md"))
    if not tasks:
        return stage, None, "", [], ""
    path = max(tasks, key=os.path.getmtime)
    task = os.path.basename(os.path.dirname(path))
    text = read(path)
    if stage in ("S1", "S2") and first_word(text, "Loại") in ("APP", "MODULE"):
        return stage, task, text, as_steps(phase_a_steps(root, text)), "Phase A"
    return stage, task, text, board_steps(root, task), ""


def progress_line(root):
    st = state(root)
    if not st:
        return ""
    stage, task, text, steps, src = st
    if not task:
        return f"{stage} {STAGES[stage][0]}"
    parts = [f"[{task}] {stage} {src or STAGES[stage][0]}"]
    parts += steps_summary(steps) if steps else []
    waiting, whys = board_info(root, task)
    if waiting:
        parts.append("chờ: " + ", ".join(waiting))
    if whys:
        parts.append(f"WHY mở: {whys}")
    parts += agent_info(root, task)
    if not steps:
        missing = [k for k in gate_for(stage, text) if not field(text, k)]
        if missing:
            parts.append("thiếu: " + ", ".join(missing[:3]) + (" …" if len(missing) > 3 else ""))
    return " · ".join(parts)


MAX_STEP_ROWS = 8
MARK = {"done": "✅ Xong", "doing": "▶ Đang làm", "todo": "⏳ Chờ", "skip": "– Bỏ", "blocked": "⛔ Chặn"}


def cfg(root, key, default=""):
    """.claude/agent-team.local.config (riêng mỗi dev) trước, rồi .claude/agent-team.config."""
    for name in ("agent-team.local.config", "agent-team.config"):
        m = re.search(rf"(?m)^\s*{key}=\s*['\"]?([^'\"#\n]*)", read(os.path.join(root, ".claude", name)))
        if m and (m.group(1).strip() or name == "agent-team.config"):  # local để trống = không ghi đè
            return m.group(1).strip()
    return default


def dwidth(t):
    """Độ rộng hiển thị trên terminal: ký tự rộng (✅ ⏳, CJK) = 2, dấu kết hợp = 0."""
    import unicodedata
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in t)


def box(headers, rows):
    """Bảng có khung ┌─┬─┐, căn theo độ rộng hiển thị."""
    cols = [max(dwidth(x) for x in col) for col in zip(headers, *rows)]
    line = lambda l, m, r: l + m.join("─" * (w + 2) for w in cols) + r
    cell = lambda vals: "│" + "│".join(f" {v}{' ' * (w - dwidth(v))} " for v, w in zip(vals, cols)) + "│"
    return [line("┌", "┬", "┐"), cell(headers), line("├", "┼", "┤")] + [cell(r) for r in rows] + [line("└", "┴", "┘")]


def parent_block(root, text, task, cur_step, phase_a=False):
    """Tầng trên: bảng module của app (APP.md) hoặc task của module (MODULE.md). [] khi bảng chưa điền."""
    if module_dir(text) and first_word(text, "Loại") != "MODULE":
        src, key, name = read(os.path.join(root, module_dir(text), "MODULE.md")), "T", "task"
    elif phase_a:
        return []  # Phase A của app / module: chưa có danh sách con
    else:
        src, key, name = read(os.path.join(root, "docs", "product", "APP.md")), "M", "module"
    rows = [r for r in table_rows(src, key) if r[1]]
    if not rows:
        return []
    title = (re.search(r"(?m)^#\s+(.+)$", src) or [None, ""])[1].strip()
    done = [r[-1].upper().startswith("DONE") for r in rows]
    cur = next((i for i, r in enumerate(rows) if task in r[2:]), None)
    if cur is None:
        cur = next((i for i, d in enumerate(done) if not d), None)
    st = ["done" if d else "doing" if i == cur else "todo" for i, d in enumerate(done)]
    for i, r in enumerate(rows):
        if not done[i] and r[-1].upper().startswith("BLOCKED"):
            st[i] = "blocked"
    head = f"{'Module' if key == 'T' else 'App'}{' ' + short(title, 40) if title and not title.startswith('<') else ''} · {sum(done)}/{len(rows)} {name} xong"
    show = [i for i in range(len(rows)) if cur is not None and cur - 1 <= i <= cur + 1] or list(range(min(3, len(rows))))
    body = [[rows[i][0], short(rows[i][1], 28), MARK[st[i]] + (f" · {cur_step}" if st[i] == "doing" and cur_step else "")] for i in show]
    before = [st[i] for i in range(len(rows)) if i < show[0]]
    after = [st[i] for i in range(len(rows)) if i > show[-1]]
    if before:
        body.insert(0, ["…", f"+{len(before)} {name}", MARK["done"] if set(before) == {"done"} else "…"])
    if after:
        body.append(["…", f"+{len(after)} {name}", MARK["todo"] if set(after) == {"todo"} else "…"])
    return [head] + box([key, "Module" if key == "M" else "Task", "Trạng thái"], body)


def collapse(steps):
    """[(nhãn số, tiêu đề, role, trạng thái, phút, ∥)], gộp đoạn ✅ đầu / ⏳ cuối khi quá MAX_STEP_ROWS dòng."""
    now = int(time.time())
    size = {}
    for x in steps:
        size[x[3]] = size.get(x[3], 0) + 1
    rows = [(str(i), t, r or "", s, now - st if s == "doing" and st else None, g is not None and size[g] > 1)
            for i, (t, s, r, g, st) in enumerate(steps, 1)]

    def merge(a, b, state):
        names = ", ".join(short(x[1], 14) for x in rows[a:b])
        return (f"{rows[a][0]}–{rows[b - 1][0]}", short(names, 40), "", state, None, False)

    if len(rows) > MAX_STEP_ROWS:
        k = next((i for i, x in enumerate(rows) if x[3] != "done"), len(rows))
        if k > 1:
            rows = [merge(0, k, "done")] + rows[k:]
    if len(rows) > MAX_STEP_ROWS:
        k = len(rows)
        while k > 0 and rows[k - 1][3] == "todo":
            k -= 1
        keep = max(k, MAX_STEP_ROWS - 1)
        if len(rows) - keep > 1:
            rows = rows[:keep] + [merge(keep, len(rows), "todo")]
    return rows


POOL_COLS = ["Debate", "Code", "Test", "Review", "IT", "Merge"]
POOL_STAGE_COL = {"S1": 1, "S2": 1, "S3": 1, "S4": 2, "S5": 3, "S6": 3}  # stage của worktree → cột đang làm
POOL_MAX_ROWS = 16


def clock(sec):
    """Thời gian chạy: mm:ss, quá 1 giờ thì h:mm:ss."""
    sec = max(0, int(sec))
    h, m, s_ = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s_:02d}" if h else f"{m:02d}:{s_:02d}"


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def agent_pulse(root, wt, hang):
    """Agent đang chạy trong worktree + lần cuối dùng tool (nhịp tim): 'backend-dev 8s trước' / '⚠ backend-dev im 12p'."""
    try:
        c = sqlite3.connect(f"file:{os.path.join(root, wt, '.agent-team', 'board.db')}?mode=ro", uri=True, timeout=2)
        rows = c.execute("SELECT role, last_seen, busy_since, tool_timeout FROM agent_runs WHERE state='RUNNING' ORDER BY last_seen DESC").fetchall()
        c.close()
    except sqlite3.Error:
        return ""
    if not rows:
        return ""
    role, seen, busy, tmo = rows[0]
    idle = int(time.time()) - seen
    limit = max(hang, (tmo or 0) + 60) if busy else hang
    more = f" +{len(rows) - 1}" if len(rows) > 1 else ""
    return (f"⚠ {role}{more} im {idle // 60}p" if idle > limit else f"{role}{more} {idle}s trước")


def group_waiting(rows):
    """Task chờ liền nhau cùng trạng thái gộp 1 dòng: T-2..T-4 (3 task)."""
    out, keys = [], []
    for x in rows:
        if out and x[-1].startswith("⏳") and out[-1][2:] == x[2:]:
            keys[-1].append(x[1].split(" ")[0])
            continue
        out.append(list(x))
        keys.append([x[1].split(" ")[0]])
    for x, k in zip(out, keys):
        if len(k) > 1:
            x[1] = f"{k[0]}..{k[-1]} ({len(k)} task)"
    return out


def task_cells(root, r, design, now):
    """6 ô Debate · Code · Test · Review · IT · Merge + trạng thái chung của 1 task trong pool."""
    st, note = r["state"], (r["note"] or "")
    cells = ["💬 ▶" if design else "✅"] + ["⏳"] * 5
    if st == "DONE":
        return ["✅"] * 6, "✅ Merged"
    if st == "MERGE_WAIT":
        return ["✅"] * 4 + ["⏳", "⏳"], "🔀 Chờ merge"
    if st == "MERGING":
        t0 = mtime(os.path.join(root, ".git", "MERGE_HEAD"))  # git tạo lúc merge --no-commit
        el = clock(now - t0) if t0 else ""
        warn = " ⚠" if t0 and now - t0 > int(cfg(root, "MERGE_WARN_MINUTES", "20") or 20) * 60 else ""
        return ["✅"] * 4 + [f"🧪 ▶ {el}".strip(), "⏳"], f"🧪 Integration test {el}{warn}".strip()
    if st == "WAIT":
        return cells, ""
    stg = read(os.path.join(root, r["worktree"] or "", ".agent-team", "stage")).strip().upper() if r["worktree"] else ""
    cur = POOL_STAGE_COL.get(stg, 1)
    for i in range(1, cur):
        cells[i] = "✅"
    t0 = mtime(os.path.join(root, r["worktree"] or "", ".agent-team", "stage")) or r["started_at"]  # vào giai đoạn này lúc nào
    el = f" {clock(now - t0)}" if t0 else ""
    mark = {"RUNNING": "▶" + el, "FIX": "🔧" + el, "GAP": "⛔", "BLOCKED": "⛔"}.get(st, "▶")
    cells[cur] = mark
    if st == "FIX" and note.startswith("IT fail"):
        cells[4] = "✗"
    if st == "FIX" and note.startswith("conflict"):
        cells[5] = "✗"
    label = {"RUNNING": f"▶ {POOL_COLS[cur]}", "FIX": "🔧 Sửa", "GAP": "⛔ GAP", "BLOCKED": "⛔ Chặn"}.get(st, st)
    if note and st in ("FIX", "GAP", "BLOCKED"):
        label += f" ({short(note.split(':')[0], 12)})"
    if st in ("RUNNING", "FIX") and r["worktree"]:
        pulse = agent_pulse(root, r["worktree"], int(cfg(root, "HANG_MINUTES", "10") or 10) * 60)
        label += f" · {pulse}" if pulse else " · chưa có agent"
    return cells, label


def pool_block(root, all_rows=False):
    """Điều phối nhiều task (pool.py): 1 dòng / task, cột theo giai đoạn + trạng thái chung, gom theo module. [] khi không dùng pool."""
    p = os.path.join(root, ".agent-team", "board.db")
    if not os.path.isfile(p):
        return []
    try:
        db = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=2)
        db.row_factory = sqlite3.Row
        rows = db.execute("SELECT * FROM pool ORDER BY ord").fetchall()
        mods = {m["module"]: m for m in db.execute("SELECT * FROM pool_modules ORDER BY ord")}
        db.close()
    except sqlite3.Error:
        return []
    if not rows and not mods:
        return []
    try:  # luật READY / chờ của pool.py (phụ thuộc module, nền dữ liệu, hàng chờ debate)
        import importlib.util
        spec = importlib.util.spec_from_file_location("pool", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pool.py"))
        pool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pool)
        pdb = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=2)
        pdb.row_factory = sqlite3.Row
        wait_d = set(pool.plan_fill(pdb, root)[2])
    except Exception:
        pool, pdb, wait_d = None, None, set()
    app = read(os.path.join(root, "docs", "product", "APP.md"))
    table = [r for r in table_rows(app, "M") if r[1]]
    names = {r[0]: r[1] for r in table}
    app_done = {r[0] for r in table if r[-1].upper().startswith("DONE")}
    order = [r[0] for r in table] + [m for m in mods if m not in {r[0] for r in table}]
    order += [r["module"] for r in rows if r["module"] not in order]
    done_lbl = {r["label"] for r in rows if r["state"] == "DONE"}
    now = int(time.time())
    single = not table and len({r["module"] for r in rows} | set(mods)) == 1
    body, idle, running, debating = [], [], 0, 0
    for m in order:
        tasks = [r for r in rows if r["module"] == m]
        mst = mods[m]["state"] if m in mods else ""
        is_done = mst == "DONE" or m in app_done
        design = mst == "DESIGN"
        debating += design
        if is_done and all(t["state"] == "DONE" for t in tasks):
            body.append([m, f"({len(tasks)} task)" if tasks else "(đã xong)"] + ["✅"] * 6 + ["✅ Xong"])
            continue
        if not tasks:
            if design:
                dat = mods[m]["design_at"] if "design_at" in mods[m].keys() else None
                el = f" {clock(now - dat)}" if dat else ""
                body.append([m, "(chưa chia task)", "💬 ▶" + el] + ["⏳"] * 5 + ["💬 Debate" + el])
            elif mst == "SPLIT":
                body.append([m, "(chưa có task)", "✅"] + ["⏳"] * 5 + ["⚠ Chưa add task"])
            else:
                idle.append(m)
            continue
        merged = [t for t in tasks if t["state"] == "DONE"]
        for i, t in enumerate(tasks):
            cells, label = task_cells(root, t, design, now)
            if t["state"] in ("RUNNING", "FIX", "GAP"):
                running += 1
            if t["state"] == "WAIT":
                deps = [x.strip() for x in (t["deps"] or "").split(",") if x.strip() and x.strip() not in done_lbl]
                mw = pool.module_wait(pdb, root, m) if pool and not deps and not design else []
                label = ("⏳ Chờ " + ", ".join(d.replace(m + "/", "") for d in deps)) if deps else \
                    "💬 Chờ chia task" if design else ("⏳ Chờ " + ", ".join(mw)) if mw else "🟢 READY"
            body.append(["", short(t["label"].split("/")[-1] + " " + t["title"], 26)] + cells + [label])
        first = len(body) - len(tasks)  # dòng đầu của module: ghi tên module
        body[first][0] = m
        if not all_rows:
            body[first:] = group_waiting(body[first:])
        if not all_rows and merged and len(merged) < len(tasks) and len(body) > POOL_MAX_ROWS:  # gọn: task đã merge gộp 1 dòng
            keep = [x for x in body[first:] if x[-1] != "✅ Merged"]
            body[first:] = [[m, f"({len(merged)} task đã merge)"] + ["✅"] * 6 + ["✅ Merged"]] + [[""] + x[1:] for x in keep]
    for group, label in (([x for x in idle if x in wait_d], "⏳ Chờ slot debate"), ([x for x in idle if x not in wait_d], "⏳ Chờ phụ thuộc")):
        if group:
            nm = f"{group[0]}…" if len(group) > 1 else group[0]
            body.append([nm, f"{len(group)} module" if len(group) > 1 else short(names.get(group[0], ""), 26)]
                        + ["⏳", "", "", "", "", ""] + [label])
    if pdb:
        pdb.close()
    if not all_rows and len(body) > POOL_MAX_ROWS:
        cut = len(body) - POOL_MAX_ROWS + 1
        body = body[:POOL_MAX_ROWS - 1] + [["…", f"+{cut} dòng (pool.py status)", "", "", "", "", "", "", ""]]
    title = (re.search(r"(?m)^#\s+(.+)$", app) or [None, ""])[1].strip()
    total_m = len(table) or len(set(order))
    head = (f"App {short(title, 30)} · " if title and not title.startswith("<") else "") + \
        f"Module ✅ {sum(1 for m in order if (mods.get(m) and mods[m]['state'] == 'DONE') or m in app_done)}/{total_m} · " \
        f"chạy {running + debating}/{cfg(root, 'MAX_PARALLEL', '8')} (task {running} · 💬 debate {debating}/{cfg(root, 'MAX_DEBATE', '4')})"
    if single:
        m = order[0]
        head = f"{m} {short(names.get(m, ''), 30)} · {len(done_lbl)}/{len(rows)} task xong · chạy {running}/{cfg(root, 'MAX_PARALLEL', '8')}"
        return [head] + box(["Task"] + POOL_COLS + ["Trạng thái"], [x[1:] for x in body])
    return [head] + box(["Module", "Task"] + POOL_COLS + ["Trạng thái"], body)


def progress_table(root):
    """Bảng checklist: tầng trên (module / task) + các bước của task đang chạy."""
    st = state(root)
    if not st:
        return "\n".join(pool_block(root))  # giữa 2 lần thiết kế module: chỉ còn bảng điều phối
    stage, task, text, steps, src = st
    if not task:
        return f"{stage} {STAGES[stage][0]}"
    kind = first_word(text, "Loại")
    done = sum(1 for x in steps if x[1] == "done")
    doing = [i + 1 for i, x in enumerate(steps) if x[1] == "doing"]
    cur = f"bước {'+'.join(map(str, doing))}/{len(steps)}" if doing and steps else ""
    pool = pool_block(root)
    out = pool or parent_block(root, text, task, cur, bool(src))
    label = f"{'App' if kind == 'APP' else 'Module'} · Phase A" if src else f"{stage} {STAGES[stage][0]}"
    out.append(f"[{task}] {label}" + (f" · {done}/{len(steps)} xong" if steps else ""))
    if not src and not pool:
        out += stage_table(stage)
    if not pool and not steps:
        if stage in ("S3", "S4", "S5"):
            out.append("Chưa có danh sách bước (Lead: board.py plan " + task + ' --set "bước 1 @role ∥ bước 2 @role | ...")')
    elif not pool:
        rows = collapse(steps)
        has_role = any(r[2] for r in rows)
        body = [[n, short(t) + ("  ∥" if par else ""), *([r] if has_role else []),
                 MARK.get(s, "⏳ Chờ") + (f" {clock(mins)}" if mins is not None else "")] for n, t, r, s, mins, par in rows]
        out += box(["#", "Bước", *(["Role"] if has_role else []), "Trạng thái"], body)
    extra = []
    waiting, whys = board_info(root, task)
    if waiting:
        extra.append("chờ post: " + ", ".join(waiting))
    if not steps:
        missing = [k for k in gate_for(stage, text) if not field(text, k)]
        if missing:
            extra.append("thiếu: " + ", ".join(missing[:3]) + (" …" if len(missing) > 3 else ""))
    if whys:
        extra.append(f"WHY mở: {whys}")
    extra += agent_info(root, task)
    if extra:
        out.append(" · ".join(extra))
    return "\n".join(out)


def progress_list(root):
    """Lead dán vào chat: cùng bảng với status line."""
    return progress_table(root)


def main():
    lst = "--list" in sys.argv[1:]
    root = find_root(os.getcwd() if lst else start_dir())
    if root:
        one = cfg(root, "PROGRESS_LINES", "table") == "1"
        print(progress_list(root) if lst else progress_line(root) if one else progress_table(root))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[agent-team progress] {e}\n")
    sys.exit(0)
