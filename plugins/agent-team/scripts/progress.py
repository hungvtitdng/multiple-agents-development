#!/usr/bin/env python3
import glob
import json
import os
import re
import sqlite3
import sys

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
        m = re.search(r"(?m)^\s*HANG_MINUTES=\s*['\"]?(\d+)", open(os.path.join(root, ".claude", "agent-team.config"), encoding="utf-8").read())
        hang = int(m.group(1)) if m else 10
    except OSError:
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
        elif step:
            out.append(f"{role} {step}")
    return out


def first_word(text, name):
    return (field(text, name).split() or [""])[0].upper()


def table_rows(text, key):
    """Dòng bảng có cột đầu `M-n` / `T-n` (bỏ dòng chưa điền tên)."""
    rows = []
    for line in text.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) > 2 and re.match(rf"^{key}-(\d+|E2E)$", c[0]):
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
    d = os.path.join(root, field(text, "Module").strip("/") if kind == "MODULE" else "docs/product")
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
            rows = db.execute("SELECT title, state, role, grp FROM plan_steps WHERE task=? ORDER BY n", (task,)).fetchall()
        except sqlite3.OperationalError:  # board.db của v0.20.0 chưa có cột grp
            rows = [r + (None,) for r in db.execute("SELECT title, state, role FROM plan_steps WHERE task=? ORDER BY n", (task,))]
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
    return [(t, "done" if ok else "doing" if i == first else "todo", None, None) for i, (t, ok) in enumerate(phase)]


def parent_line(root, text):
    """App: x/N module xong · Module: x/N task xong (chỉ khi bảng đã điền)."""
    if field(text, "Module") and first_word(text, "Loại") != "MODULE":
        rows, name = table_rows(read(os.path.join(root, field(text, "Module").strip("/"), "MODULE.md")), "T"), "task"
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


def progress_list(root):
    """Danh sách đầy đủ để Lead dán vào chat."""
    st = state(root)
    if not st or not st[1]:
        return progress_line(root)
    stage, task, text, steps, src = st
    head = [x for x in (parent_line(root, text), f"[{task}] {stage} {src or STAGES[stage][0]}") if x]
    if not steps:
        return " · ".join(head) + "\nChưa có danh sách bước (Lead: board.py plan " + task + ' --set "bước 1 @role | ...")'
    w = max(len(x[0]) for x in steps)
    wr = max(len(x[2] or "") for x in steps)
    size = {}
    for x in steps:
        size[x[3]] = size.get(x[3], 0) + 1
    mark = {"done": "✅", "doing": "▶ ", "todo": "○ ", "skip": "– "}
    lines = [(f"{mark.get(s, '○ ')} {i}. {t.ljust(w)}  {(r or '').ljust(wr)}".rstrip() + ("  ∥" if g is not None and size[g] > 1 else ""))
             for i, (t, s, r, g) in enumerate(steps, 1)]
    if any(size[g] > 1 for g in size if g is not None):
        lines.append("(∥ = chạy song song)")
    return "\n".join([" · ".join(head)] + lines)


def main():
    lst = "--list" in sys.argv[1:]
    root = find_root(os.getcwd() if lst else start_dir())
    if root:
        print(progress_list(root) if lst else progress_line(root))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[agent-team progress] {e}\n")
    sys.exit(0)
