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
BAR = 10


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


def progress_line(root):
    try:
        stage = open(os.path.join(root, ".agent-team", "stage"), encoding="utf-8").read().strip().upper()
    except OSError:
        return ""
    if stage not in STAGES:
        return ""
    tasks = glob.glob(os.path.join(root, "docs", "agent-tasks", "*", "TASK.md"))
    if not tasks:
        return f"{stage} {STAGES[stage][0]}"
    path = max(tasks, key=os.path.getmtime)
    task = os.path.basename(os.path.dirname(path))
    text = open(path, encoding="utf-8", errors="ignore").read()
    name, lo, hi = STAGES[stage]
    gate = gate_for(stage, text)
    missing = [k for k in gate if not field(text, k)]
    pct = round(lo + (hi - lo) * (len(gate) - len(missing)) / len(gate))
    filled = round(pct * BAR / 100)
    parts = [f"[{task}] {stage} {name} {'▓' * filled}{'░' * (BAR - filled)} {pct}%"]
    waiting, whys = board_info(root, task)
    if waiting:
        parts.append("chờ: " + ", ".join(waiting))
    if whys:
        parts.append(f"WHY mở: {whys}")
    parts += agent_info(root, task)
    if missing:
        parts.append("thiếu: " + ", ".join(missing[:3]) + (" …" if len(missing) > 3 else ""))
    return " · ".join(parts)


def main():
    root = find_root(start_dir())
    if root:
        print(progress_line(root))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[agent-team progress] {e}\n")
    sys.exit(0)
