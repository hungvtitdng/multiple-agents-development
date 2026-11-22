#!/usr/bin/env python3
"""agent-team board: phòng debate dạng chat, lưu SQLite (.agent-team/board.db).

Lead:  team <task> --roles a,b | open <task> <S#> <R#> [--roles a,b] [--goal ".."] | close | summary | export
       report <task>   → docs/agent-tasks/<task>/REPORT.md (bảng debate + quyết định, để user đọc)
       why-close <task> <n> --as ruling|assumption --note ".."
Role:  post <task> --role <role> [--reply ID] [--mention a,b] [--body ".." | stdin]
Mọi người: read <task> [--all | --stage S2 --round 1 | --mention role | --since ID] | status <task> | whys <task> [--open]

WHY trong bài post (mỗi dòng một lệnh, dòng sau không có từ khoá thì nối vào nội dung):
  WHY @role: <câu hỏi>         tạo WHY-n hỏi role đó
  RE WHY-n: <trả lời + bằng chứng>   chỉ người bị hỏi; xoá phiếu cũ, cả team biểu quyết lại
  AGREE WHY-n                  đồng ý làm theo câu trả lời
  DISAGREE WHY-n: <vì sao ...?>  không đồng ý, bắt buộc kèm lý do/câu hỏi tiếp
WHY đóng khi MỌI thành viên team (trừ người trả lời) AGREE.
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import time

MAX_LINES = 80
MAX_CHARS = 8000
MENTION_RE = re.compile(r"@([a-z][a-z-]+)")

SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
  id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, stage TEXT NOT NULL, round INTEGER NOT NULL,
  goal TEXT, roles TEXT, opened_at INTEGER NOT NULL, closed_at INTEGER,
  UNIQUE(task, stage, round));
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, stage TEXT NOT NULL, round INTEGER NOT NULL,
  role TEXT NOT NULL, reply_to INTEGER, mentions TEXT, body TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, stage TEXT NOT NULL, round INTEGER NOT NULL,
  body TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS idx_msg_task ON messages(task, stage, round);
CREATE TABLE IF NOT EXISTS team (task TEXT NOT NULL, role TEXT NOT NULL, PRIMARY KEY(task, role));
CREATE TABLE IF NOT EXISTS whys (
  id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL, msg_id INTEGER, asker TEXT NOT NULL, target TEXT NOT NULL,
  question TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', answer TEXT, answers INTEGER NOT NULL DEFAULT 0,
  note TEXT, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS votes (
  why_id INTEGER NOT NULL, role TEXT NOT NULL, vote TEXT NOT NULL, reason TEXT, msg_id INTEGER,
  PRIMARY KEY(why_id, role));
CREATE TABLE IF NOT EXISTS vote_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, why_id INTEGER NOT NULL, role TEXT NOT NULL, vote TEXT NOT NULL,
  reason TEXT, answer_no INTEGER, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS agent_runs (
  task TEXT NOT NULL, role TEXT NOT NULL, run TEXT NOT NULL, started_at INTEGER NOT NULL, last_seen INTEGER NOT NULL,
  last_tool TEXT, busy_since INTEGER, tool_timeout INTEGER, state TEXT NOT NULL DEFAULT 'RUNNING',
  step TEXT, eta_min INTEGER, result TEXT, ended_at INTEGER, PRIMARY KEY(task, role, run));
"""
OPEN_STATUS = ("open", "voting")
_P = r"^\s*(?:[-*]\s*)?"
KW = [
    ("why", re.compile(_P + r"WHY\s+@([a-z][a-z-]+)\s*:\s*(\S.*)$", re.I)),
    ("re", re.compile(_P + r"RE\s+WHY-(\d+)\s*:\s*(\S.*)$", re.I)),
    ("disagree", re.compile(_P + r"DISAGREE\s+WHY-(\d+)\b\s*:?\s*(.*)$", re.I)),
    ("agree", re.compile(_P + r"AGREE\s+WHY-(\d+)\b()", re.I)),
]


class BoardError(Exception):
    pass


def die(msg):
    sys.stderr.write(f"board: {msg}\n")
    sys.exit(1)


def find_root():
    d = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return os.getcwd()
        d = os.path.dirname(d)


def connect():
    path = os.environ.get("AGENT_TEAM_BOARD_DB") or os.path.join(find_root(), ".agent-team", "board.db")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=15000")
    db.executescript(SCHEMA)
    return db


def norm_role(r):
    return (r or "").strip().lower().split(":")[-1]


def read_body(args):
    body = args.body if args.body is not None else ("" if sys.stdin.isatty() else sys.stdin.read())
    body = body.strip("\n")
    if not body.strip():
        die("nội dung trống (dùng --body hoặc stdin)")
    if body.count("\n") + 1 > MAX_LINES or len(body) > MAX_CHARS:
        die(f"bài quá dài (tối đa {MAX_LINES} dòng / {MAX_CHARS} ký tự). Viết gọn theo mẫu POST.md")
    return body


def open_round(db, task):
    return db.execute("SELECT * FROM rounds WHERE task=? AND closed_at IS NULL ORDER BY id DESC LIMIT 1", (task,)).fetchone()


def fmt_msg(m):
    head = f"#{m['id']} [{m['stage']}-R{m['round']}] {m['role']}"
    if m["reply_to"]:
        head += f" (trả lời #{m['reply_to']})"
    if m["mentions"]:
        head += " → " + " ".join("@" + x for x in m["mentions"].split(","))
    return f"{head}\n{m['body']}\n"


def fmt_summary(s):
    return f"== Tóm tắt {s['stage']}-R{s['round']} (Lead) ==\n{s['body']}\n"


# ---------- lệnh ----------

def cmd_open(db, a):
    if open_round(db, a.task):
        die("đang có lượt mở, đóng lượt cũ trước (close)")
    stage = a.stage.upper()
    if not re.fullmatch(r"S[1-6]", stage):
        die("stage phải là S1..S6")
    roles = ",".join(norm_role(r) for r in (a.roles or "").split(",") if r.strip())
    try:
        db.execute("INSERT INTO rounds(task, stage, round, goal, roles, opened_at) VALUES(?,?,?,?,?,?)",
                   (a.task, stage, a.round, a.goal or "", roles, int(time.time())))
    except sqlite3.IntegrityError:
        die(f"lượt {stage}-R{a.round} đã tồn tại")
    db.commit()
    print(f"Đã mở {stage}-R{a.round}" + (f", role: {roles}" if roles else ""))


def cmd_close(db, a):
    r = open_round(db, a.task) or die("không có lượt đang mở")
    posted = db.execute("SELECT count(*) FROM messages WHERE task=? AND stage=? AND round=?", (a.task, r["stage"], r["round"])).fetchone()[0]
    summed = db.execute("SELECT count(*) FROM summaries WHERE task=? AND stage=? AND round=?", (a.task, r["stage"], r["round"])).fetchone()[0]
    if posted and not summed:
        die(f"chưa tóm tắt {r['stage']}-R{r['round']}: chạy `board.py summary {a.task}` trước khi đóng (lượt sau mọi người chỉ đọc tóm tắt)")
    db.execute("UPDATE rounds SET closed_at=? WHERE id=?", (int(time.time()), r["id"]))
    db.commit()
    print(f"Đã đóng {r['stage']}-R{r['round']}")


# ---------- WHY: hỏi vì sao đến khi cả team đồng ý ----------

def team_of(db, task):
    return {r["role"] for r in db.execute("SELECT role FROM team WHERE task=?", (task,))}


def parse_actions(body):
    """[(loại, khoá, nội dung)]; dòng không có từ khoá nối vào nội dung của lệnh trước."""
    acts = []
    for line in body.splitlines():
        for kind, rx in KW:
            m = rx.match(line)
            if m:
                acts.append([kind, m.group(1).lower(), m.group(2).strip()])
                break
        else:
            if acts and line.strip() and acts[-1][0] != "agree":
                acts[-1][2] = (acts[-1][2] + "\n" + line.strip()).strip()
            elif not line.strip() and acts:
                acts.append(["_stop", "", ""])
    return [x for x in acts if x[0] != "_stop"]


def get_why(db, task, n):
    w = db.execute("SELECT * FROM whys WHERE id=? AND task=?", (int(n), task)).fetchone()
    if not w:
        raise BoardError(f"không có WHY-{n}")
    if w["status"] not in OPEN_STATUS:
        raise BoardError(f"WHY-{n} đã đóng ({w['status']})")
    return w


def missing_voters(db, w, team):
    agreed = {r["role"] for r in db.execute("SELECT role FROM votes WHERE why_id=? AND vote='AGREE'", (w["id"],))}
    return sorted(team - {w["target"]} - agreed)


def apply_whys(db, task, role, msg_id, body):
    out, team = [], None
    for kind, key, text in parse_actions(body):
        team = team if team is not None else team_of(db, task)
        if not team:
            raise BoardError("Lead chưa chốt team debate (board.py team <task> --roles ...)")
        if role not in team:
            raise BoardError(f"'{role}' không thuộc team debate ({', '.join(sorted(team))})")
        now = int(time.time())
        if kind == "why":
            if key not in team:
                raise BoardError(f"@{key} không thuộc team debate")
            if key == role:
                raise BoardError("không tự hỏi chính mình")
            cur = db.execute("INSERT INTO whys(task, msg_id, asker, target, question, created_at) VALUES(?,?,?,?,?,?)",
                             (task, msg_id, role, key, text, now))
            out.append(f"Tạo WHY-{cur.lastrowid} → @{key}")
            continue
        w = get_why(db, task, key)
        if kind == "re":
            if role != w["target"]:
                raise BoardError(f"WHY-{key} hỏi @{w['target']}, chỉ người đó trả lời")
            db.execute("UPDATE whys SET answer=?, answers=answers+1, status='voting' WHERE id=?", (text, w["id"]))
            db.execute("DELETE FROM votes WHERE why_id=?", (w["id"],))
            out.append(f"Đã trả lời WHY-{key}, chờ biểu quyết: {', '.join(sorted(team - {role}))}")
            continue
        if w["status"] != "voting":
            raise BoardError(f"WHY-{key} chưa có câu trả lời mới để biểu quyết")
        if role == w["target"]:
            raise BoardError("người trả lời không tự biểu quyết")
        if kind != "disagree" or text:
            db.execute("INSERT INTO vote_log(why_id, role, vote, reason, answer_no, created_at) VALUES(?,?,?,?,?,?)",
                       (w["id"], role, kind.upper(), text or None, w["answers"], now))
        if kind == "disagree":
            if not text:
                raise BoardError(f"DISAGREE WHY-{key} phải kèm lý do / câu hỏi tiếp")
            db.execute("INSERT OR REPLACE INTO votes(why_id, role, vote, reason, msg_id) VALUES(?,?,?,?,?)",
                       (w["id"], role, "DISAGREE", text, msg_id))
            db.execute("UPDATE whys SET status='open' WHERE id=?", (w["id"],))
            out.append(f"WHY-{key}: {role} không đồng ý, chờ @{w['target']} trả lời tiếp")
        else:
            db.execute("INSERT OR REPLACE INTO votes(why_id, role, vote, reason, msg_id) VALUES(?,?,?,?,?)",
                       (w["id"], role, "AGREE", None, msg_id))
            miss = missing_voters(db, w, team)
            if miss:
                out.append(f"WHY-{key}: {role} đồng ý, còn chờ: {', '.join(miss)}")
            else:
                db.execute("UPDATE whys SET status='agreed' WHERE id=?", (w["id"],))
                out.append(f"WHY-{key}: cả team đồng ý → đã thống nhất")
    return out


def why_lines(db, task, only_open=False):
    team, lines = team_of(db, task), []
    q = "SELECT * FROM whys WHERE task=?" + (" AND status IN ('open','voting')" if only_open else "") + " ORDER BY id"
    for w in db.execute(q, (task,)):
        head = f"WHY-{w['id']} [{w['status']}] {w['asker']} → @{w['target']}: {w['question']}"
        if w["status"] == "open" and not w["answers"]:
            head += f"\n   chờ @{w['target']} trả lời"
        elif w["status"] == "open":
            reasons = [f"{v['role']}: {v['reason']}" for v in db.execute(
                "SELECT * FROM votes WHERE why_id=? AND vote='DISAGREE'", (w["id"],))]
            head += f"\n   trả lời lần {w['answers']}: {w['answer']}\n   không đồng ý → " + " | ".join(reasons) + \
                    f"\n   chờ @{w['target']} trả lời tiếp"
        elif w["status"] == "voting":
            head += f"\n   trả lời: {w['answer']}\n   chờ biểu quyết: {', '.join(missing_voters(db, w, team)) or '-'}"
        else:
            head += f"\n   kết luận: {w['answer'] or ''}" + (f"\n   ghi chú: {w['note']}" if w["note"] else "")
        lines.append(head)
    return lines


def cmd_team(db, a):
    roles = sorted({norm_role(r) for r in a.roles.split(",") if r.strip()})
    if len(roles) < 2:
        die("team debate cần ít nhất 2 role")
    db.execute("DELETE FROM team WHERE task=?", (a.task,))
    db.executemany("INSERT INTO team(task, role) VALUES(?,?)", [(a.task, r) for r in roles])
    db.commit()
    print("Team debate: " + ", ".join(roles))


def cmd_whys(db, a):
    lines = why_lines(db, a.task, a.open)
    print("\n".join(lines) if lines else "(không có WHY" + (" đang mở)" if a.open else ")"))


def cmd_why_close(db, a):
    w = db.execute("SELECT * FROM whys WHERE id=? AND task=?", (a.n, a.task)).fetchone() or die(f"không có WHY-{a.n}")
    if w["status"] not in OPEN_STATUS:
        die(f"WHY-{a.n} đã đóng ({w['status']})")
    if w["answers"] < 2:
        die("chỉ phán quyết khi đã giằng co: cần ít nhất 2 lần trả lời")
    sec = db.execute("SELECT 1 FROM votes WHERE why_id=? AND role='security' AND vote='DISAGREE'", (w["id"],)).fetchone()
    if sec:
        die("Security không đồng ý: Lead không được phán quyết thay, phải xử lý tới khi Security AGREE")
    team = team_of(db, a.task)
    agreed = {r["role"] for r in db.execute("SELECT role FROM votes WHERE why_id=? AND vote='AGREE'", (w["id"],))}
    dissent = sorted(team - {w["target"]} - agreed)
    note = f"{a.as_} bởi Lead: {a.note}. Không đồng ý / chưa biểu quyết: {', '.join(dissent) or '-'}"
    db.execute("UPDATE whys SET status=?, note=? WHERE id=?", ("ruled" if a.as_ == "ruling" else "assumption", note, w["id"]))
    db.commit()
    print(f"Đã đóng WHY-{a.n}: {note}")


def cmd_post(db, a):
    row = run_row(db, a.task, norm_role(a.role), current_run(db, a.task))
    if row and row["state"] == "DONE":
        die(f"{norm_role(a.role)} đã DONE ở lượt này. KẾT THÚC NGAY: trả kết quả về Lead, không post thêm")
    role = norm_role(a.role) or die("thiếu --role")
    r = open_round(db, a.task) or die("không có lượt đang mở, Lead chưa mở lượt")
    allowed = [x for x in (r["roles"] or "").split(",") if x]
    if allowed and role not in allowed and role != "lead":
        die(f"role '{role}' không tham gia lượt {r['stage']}-R{r['round']} ({', '.join(allowed)})")
    body = read_body(a)
    if a.reply and not db.execute("SELECT 1 FROM messages WHERE id=? AND task=?", (a.reply, a.task)).fetchone():
        die(f"không có tin #{a.reply}")
    mentions = {norm_role(x) for x in (a.mention or "").split(",") if x.strip()} | set(MENTION_RE.findall(body))
    mentions.discard(role)
    cur = db.execute("INSERT INTO messages(task, stage, round, role, reply_to, mentions, body, created_at) VALUES(?,?,?,?,?,?,?,?)",
                     (a.task, r["stage"], r["round"], role, a.reply, ",".join(sorted(mentions)), body, int(time.time())))
    try:
        notes = apply_whys(db, a.task, role, cur.lastrowid, body)
    except BoardError as e:
        db.rollback()
        die(f"bài không được post: {e}")
    db.commit()
    print(f"Đã post #{cur.lastrowid} vào {r['stage']}-R{r['round']}")
    for n in notes:
        print("  " + n)


def read_why(db, task, n):
    """1 câu WHY: câu hỏi, trả lời hiện tại, lịch sử phiếu, các dòng bài post nhắc tới nó. Dùng khi cần phán quyết."""
    w = db.execute("SELECT * FROM whys WHERE id=? AND task=?", (n, task)).fetchone() or die(f"không có WHY-{n}")
    print(f"WHY-{n} [{w['status']}] {w['asker']} → {w['target']}: {w['question']}")
    print(f"Trả lời (lần {w['answers']}): {w['answer'] or '-'}" + (f"\nGhi chú: {w['note']}" if w["note"] else ""))
    for l in db.execute("SELECT * FROM vote_log WHERE why_id=? ORDER BY id", (w["id"],)):
        print(f"  {l['vote']} {l['role']} (lần {l['answer_no']})" + (f": {l['reason']}" if l["reason"] else ""))
    tag = re.compile(rf"\bWHY-{n}\b")
    for m in db.execute("SELECT * FROM messages WHERE task=? AND body LIKE ? ORDER BY id", (task, f"%WHY-{n}%")):
        lines = [x for x in m["body"].splitlines() if tag.search(x)]
        if lines:
            print(f"#{m['id']} [{m['stage']}-R{m['round']}] {m['role']}: " + " | ".join(lines))


def cmd_read(db, a):
    if a.why:
        return read_why(db, a.task, a.why)
    q, args = "SELECT * FROM messages WHERE task=?", [a.task]
    if a.mention:
        q += " AND (',' || mentions || ',') LIKE ?"
        args.append(f"%,{norm_role(a.mention)},%")
    if a.since:
        q += " AND id > ?"
        args.append(a.since)
    if a.stage:
        q += " AND stage=?"
        args.append(a.stage.upper())
    if a.round:
        q += " AND round=?"
        args.append(a.round)
    filtered = a.all or a.mention or a.since or a.stage or a.round
    if not filtered:
        # mặc định: tóm tắt các lượt đã đóng + toàn bộ lượt đang mở (hoặc lượt cuối)
        r = open_round(db, a.task) or db.execute(
            "SELECT * FROM rounds WHERE task=? ORDER BY id DESC LIMIT 1", (a.task,)).fetchone()
        for s in db.execute("SELECT * FROM summaries WHERE task=? ORDER BY id", (a.task,)):
            print(fmt_summary(s))
        if not r:
            print("(chưa có lượt nào)")
            return
        q += " AND stage=? AND round=?"
        args += [r["stage"], r["round"]]
        print(f"== Lượt {r['stage']}-R{r['round']}{' (đang mở)' if r['closed_at'] is None else ''}: {r['goal'] or ''} ==")
    rows = db.execute(q + " ORDER BY id", args).fetchall()
    for m in rows:
        print(fmt_msg(m))
    if not rows:
        print("(không có tin nào)")


def pending_mentions(db, task):
    out = []
    for m in db.execute("SELECT * FROM messages WHERE task=? AND mentions != '' ORDER BY id", (task,)):
        for who in m["mentions"].split(","):
            done = db.execute(
                "SELECT 1 FROM messages WHERE task=? AND role=? AND id>? AND (reply_to=? OR stage||round != ?||?) LIMIT 1",
                (task, who, m["id"], m["id"], m["stage"], m["round"])).fetchone()
            if not done:
                out.append(f"@{who} chưa trả lời #{m['id']} ({m['role']})")
    return out


def cmd_status(db, a):
    r = open_round(db, a.task)
    if not r:
        print("Không có lượt đang mở")
    else:
        posted = {x["role"] for x in db.execute(
            "SELECT DISTINCT role FROM messages WHERE task=? AND stage=? AND round=?", (a.task, r["stage"], r["round"]))}
        want = [x for x in (r["roles"] or "").split(",") if x]
        print(f"Đang mở {r['stage']}-R{r['round']}: {r['goal'] or ''}")
        print("Đã post: " + (", ".join(sorted(posted)) or "-"))
        if want:
            print("Chưa post: " + (", ".join(x for x in want if x not in posted) or "-"))
    for p in pending_mentions(db, a.task):
        print(p)
    team = team_of(db, a.task)
    if team:
        print("Team debate: " + ", ".join(sorted(team)))
    opened = why_lines(db, a.task, only_open=True)
    print(f"WHY chưa thống nhất: {len(opened)}")
    for line in opened:
        print(line)
    root = find_root()
    run = current_run(db, a.task, root)
    view = agent_view(db, a.task, run, expected_roles(db, a.task, None), hang_minutes(root) * 60,
                      r["opened_at"] if r else int(time.time()))
    if view:
        print(f"Agent ({run}):")
        for _, _, line in view:
            print("  " + line)


def cmd_summary(db, a):
    r = open_round(db, a.task) or db.execute(
        "SELECT * FROM rounds WHERE task=? ORDER BY id DESC LIMIT 1", (a.task,)).fetchone() or die("chưa có lượt nào")
    body = read_body(a)
    db.execute("INSERT INTO summaries(task, stage, round, body, created_at) VALUES(?,?,?,?,?)",
               (a.task, r["stage"], r["round"], body, int(time.time())))
    db.commit()
    print(f"Đã ghi tóm tắt {r['stage']}-R{r['round']}")


def cmd_export(db, a):
    out = a.out or os.path.join(find_root(), "docs", "agent-tasks", a.task, "board", "DEBATE.md")
    lines = [f"# Debate - {a.task}", "", "> Xuất từ board SQLite (`board.py export`). Không sửa tay.", ""]
    for r in db.execute("SELECT * FROM rounds WHERE task=? ORDER BY id", (a.task,)):
        lines += [f"## {r['stage']}-R{r['round']}: {r['goal'] or ''}", ""]
        if r["roles"]:
            lines += [f"Role: {r['roles'].replace(',', ', ')}", ""]
        for m in db.execute("SELECT * FROM messages WHERE task=? AND stage=? AND round=? ORDER BY id",
                            (a.task, r["stage"], r["round"])):
            lines += ["### " + fmt_msg(m).split("\n", 1)[0], "", m["body"], ""]
        for s in db.execute("SELECT * FROM summaries WHERE task=? AND stage=? AND round=? ORDER BY id",
                            (a.task, r["stage"], r["round"])):
            lines += ["**Tóm tắt của Lead**", "", s["body"], ""]
    wl = why_lines(db, a.task)
    if wl:
        lines += ["## WHY", "", "```"] + wl + ["```", ""]
    pend = pending_mentions(db, a.task)
    if pend:
        lines += ["## @ chưa trả lời", ""] + [f"- {p}" for p in pend] + [""]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"Đã xuất {out}")


# ---------- báo cáo 1 task: debate + quyết định, để user đọc ----------

COND_KEYS = ["Loại", "Phương án chốt", "Workflow", "UI mockup", "Security duyệt solution", "Kết quả test", "Lint/format", "Gap còn mở",
             "Code review", "Security review", "Cập nhật KB", "Bài học"]


def task_sections(text):
    """{'0': (tiêu đề, nội dung), '7b': ...} theo heading `## <số>. <tiêu đề>`."""
    out, key = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d+[a-z]?)\.\s*(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = [m.group(2).strip(), []]
        elif line.startswith("## "):
            key = None
        elif key:
            out[key][1].append(line)
    return {k: (t, "\n".join(b).strip()) for k, (t, b) in out.items()}


def cond_value(text, name):
    m = re.search(rf"(?im)^[\s>*-]*{re.escape(name)}\s*:\s*(.*)$", text)
    return m.group(1).strip() if m else "-"


def cell(s, n=120):
    s = " ".join((s or "-").split()).replace("|", "\\|")
    return s if len(s) <= n else s[:n - 1] + "…"


def md_table(body):
    """Bảng markdown đầu tiên trong body → [dict theo tên cột]."""
    rows = [l for l in body.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    split = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    head = split(rows[0])
    out = []
    for l in rows[2:]:
        cells = split(l)
        if any(cells):
            out.append(dict(zip(head, cells + [""] * (len(head) - len(cells)))))
    return out


def pick(row, *keys):
    for k, v in row.items():
        if any(x.lower() in k.lower() for x in keys):
            return v
    return ""


def collect_assumptions(db, task, sec):
    """Giả định: TASK.md mục 2 + WHY Lead chốt bằng assumption (chưa có trong mục 2)."""
    items = []
    for r in md_table(sec.get("2", ("", ""))[1]):
        items.append({"point": pick(r, "chưa rõ"), "choice": pick(r, "đã chọn", "cách hiểu"), "why": pick(r, "lý do"),
                      "alt": pick(r, "khác"), "pros": pick(r, "ưu"), "cons": pick(r, "nhược"), "level": pick(r, "mức"),
                      "impact": pick(r, "nếu sai"), "who": pick(r, "đề xuất"), "client": pick(r, "client")})
    seen = " ".join(" ".join(i.values()) for i in items)
    for w in db.execute("SELECT * FROM whys WHERE task=? AND status='assumption' ORDER BY id", (task,)):
        if f"WHY-{w['id']}" in seen:
            continue
        items.append({"point": w["question"], "choice": (w["note"] or "").split(": ", 1)[-1].split(". Không đồng ý")[0],
                      "why": f"Lead chốt sau {w['answers']} lần trả lời (WHY-{w['id']})", "impact": "",
                      "alt": "", "pros": "", "cons": "", "level": "",
                      "who": f"{w['asker']} → {w['target']}", "client": ""})
    rank = lambda i: {"cao": 0, "trung": 1, "thấp": 2}.get((i["level"].split() or ["?"])[0].lower(), 1)
    return sorted([i for i in items if i["point"]], key=rank)


def assumption_block(items):
    if not items:
        return ["> [!NOTE]", "> Không có giả định: mọi điểm chưa rõ đã được xác nhận hoặc có trong yêu cầu.", ""]
    L = ["> [!CAUTION]",
         f"> **🔴 {len(items)} giả định cần client xác nhận.** Khi yêu cầu chưa rõ, team đã tự chọn cách hiểu dưới đây để không dừng việc. "
         "Vui lòng đánh dấu **Đúng / Sai** từng dòng; sai thì ghi cách đúng, team sẽ sửa.", "",
         "| # | 🔴 Điểm chưa rõ | Team đã chọn (vì sao) | Phương án khác đã xét | Ưu | Nhược | Nếu sai thì | Mức ảnh hưởng | Client xác nhận |",
         "|---|---|---|---|---|---|---|---|---|"]
    for n, i in enumerate(items, 1):
        L.append(f"| A-{n} | 🔴 **{cell(i['point'], 200)}** | **{cell(i['choice'], 160)}** · {cell(i['why'], 200)} | {cell(i['alt'], 160)} | "
                 f"{cell(i['pros'], 160)} | {cell(i['cons'], 160)} | {cell(i['impact'] or 'Cần sửa lại phần liên quan', 200)} | "
                 f"{cell(i['level'], 40)} | {cell(i['client'], 80) if i['client'] and i['client'] != '-' else '☐ Đúng ☐ Sai: ……'} |")
    return L + [""]


def md_inline(s):
    import html
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)


def esc(x):
    import html
    return html.escape(str(x or ""), quote=True)


def options_of(body):
    """### A. tên + nội dung → [(mã, tên, nội dung)]."""
    out = []
    for part in re.split(r"(?m)^###\s+", body or "")[1:]:
        head, _, rest = part.partition("\n")
        m = re.match(r"([A-Z])\.?\s*(.*)", head.strip())
        if m:
            out.append((m.group(1), m.group(2), rest.strip()))
    return out


def scores_of(body):
    """Bảng điểm → ({mã: tổng}, điểm tối đa)."""
    rows = md_table(body or "")
    if not rows:
        return {}, 0
    codes = [k for k in rows[0] if re.fullmatch(r"[A-Z]", k)]
    total, mx = {c: 0 for c in codes}, 0
    given = None
    for r in rows:
        crit = r.get("Tiêu chí", "")
        if "tổng" in crit.lower():
            given = {c: r.get(c, "") for c in codes}
            continue
        w = int((re.findall(r"\d+", r.get("Trọng số", "1")) or ["1"])[0])
        mx += 5 * w
        for c in codes:
            v = re.findall(r"\d+", r.get(c, ""))
            total[c] += w * int(v[0]) if v else 0
    if given and all(re.fullmatch(r"\d+", given[c] or "") for c in codes):
        total = {c: int(given[c]) for c in codes}
    return total, mx


DIAGRAMS = [("workflow.md", "Workflow nghiệp vụ"), ("state.md", "Sơ đồ trạng thái"), ("sequence.md", "Sơ đồ kỹ thuật (sequence)")]


def mermaid_svg(code, root):
    """Vẽ Mermaid thành SVG bằng mmdc (cache theo nội dung). None nếu không có mmdc hoặc lỗi."""
    import hashlib
    import shutil
    import subprocess
    import tempfile
    if os.environ.get("AGENT_TEAM_NO_MMDC") or not shutil.which("mmdc"):
        return None
    cache = os.path.join(root, ".agent-team", "mermaid-cache")
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, hashlib.sha1(code.encode()).hexdigest() + ".svg")
    if not os.path.isfile(out):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in.mmd")
            open(src, "w", encoding="utf-8").write(code)
            try:
                subprocess.run(["mmdc", "-i", src, "-o", out, "-b", "white", "-q"], capture_output=True, timeout=120)
            except Exception:
                return None
    if not os.path.isfile(out):
        return None
    svg = open(out, encoding="utf-8").read()
    uid = "mmd-" + os.path.basename(out)[:10]  # id riêng mỗi sơ đồ, tránh trùng style/marker khi nhúng nhiều SVG
    return svg[svg.find("<svg"):].replace("my-svg", uid) if "<svg" in svg else None


def inline_shared(html_text, ddir):
    """Mockup link _wf.css / _wf.js dùng chung: chèn thẳng nội dung để nhúng được vào REPORT.html (iframe srcdoc không tải file ngoài)."""
    def body(name):
        p = os.path.join(ddir, name)
        return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    html_text = re.sub(r'<link[^>]+href="_wf\.css"[^>]*>', lambda m: f"<style>{body('_wf.css')}</style>", html_text)
    return re.sub(r'<script[^>]+src="_wf\.js"[^>]*>\s*</script>', lambda m: f"<script>{body('_wf.js')}</script>", html_text)


def load_design(tdir):
    """{'diagrams': [(file, tiêu đề, [(mermaid, ghi chú)])], 'mockups': [(file, tên màn, html)]}."""
    ddir = os.path.join(tdir, "design")
    res = {"diagrams": [], "mockups": []}
    if not os.path.isdir(ddir):
        return res
    for f, title in DIAGRAMS:
        p = os.path.join(ddir, f)
        if os.path.isfile(p):
            text = open(p, encoding="utf-8").read()
            codes = re.findall(r"```mermaid\s*\n(.*?)```", text, re.S)
            notes = re.sub(r"```mermaid.*?```", "", text, flags=re.S)
            notes = "\n".join(l for l in notes.splitlines() if l.strip() and not l.startswith("#") and not l.startswith(">"))
            res["diagrams"].append((f, title, codes, notes))
    for f in sorted(os.listdir(ddir)):
        if re.match(r"^mockup-.+\.html$", f):
            html_text = inline_shared(open(os.path.join(ddir, f), encoding="utf-8").read(), ddir)
            m = re.search(r"<title>(.*?)</title>", html_text, re.S)
            res["mockups"].append((f, (m.group(1).strip() if m else f[7:-5]), html_text))
    return res


def render_dashboard(task, ttext, sec, team, msgs, whys, logs, rounds, summaries, assumptions, design=None, root="."):
    cv = lambda k: cond_value(ttext, k)
    first = lambda k: (cv(k).split() or ["-"])[0].upper()
    good = {"PASS", "APPROVED", "YES", "0", "N/A"}
    gates = [("Kết quả test", "Test"), ("Lint/format", "Lint"), ("Code review", "Code review"),
             ("Security review", "Security"), ("Gap còn mở", "Gap còn mở"), ("Cập nhật KB", "KB")]
    done = all(first(k) in good for k, _ in gates)
    n_ok = sum(w["status"] == "agreed" for w in whys)
    req = "\n".join(x for x in sec.get("0", ("", ""))[1].splitlines() if x.strip() and not x.startswith(">"))
    H = []
    H.append(f'<header><div><p class="eyebrow">Báo cáo task</p><h1>{esc(task)}</h1>'
             f'<p class="muted">{esc(cv("Loại"))} · {time.strftime("%d/%m/%Y %H:%M")} · team: {esc(", ".join(team) or "-")}</p></div>'
             f'<span class="pill {"ok" if done else "warn"}">{"Hoàn thành" if done else "Đang làm"}</span></header>')
    if req:
        H.append(f'<blockquote><b>Yêu cầu gốc</b><br>{md_inline(req).replace(chr(10), "<br>")}</blockquote>')

    # giả định: bảng đỏ + client xác nhận
    lvl = lambda v: ("bad" if v.lower().startswith("cao") else "warn" if v.lower().startswith("trung") else "ok") if v else "warn"
    if assumptions:
        H.append(f'<section class="alert"><h2>🔴 {len(assumptions)} giả định cần bạn xác nhận</h2>'
                 '<p>Yêu cầu chưa nói rõ các điểm dưới đây, team đã tự chọn để không dừng việc (xếp theo mức ảnh hưởng). '
                 'Chọn <b>Đúng</b> hoặc <b>Sai</b> từng dòng, sai thì ghi cách đúng, rồi bấm <b>Copy câu trả lời</b> và gửi lại.</p>'
                 '<div class="tw"><table class="atable"><thead><tr><th>#</th><th>Điểm chưa rõ</th><th>Team đã chọn</th><th>Phương án khác đã xét</th>'
                 '<th>Ưu / Nhược của cách đã chọn</th><th>Ảnh hưởng nếu sai</th><th>Client xác nhận</th></tr></thead><tbody>')
        for n, i in enumerate(assumptions, 1):
            conf = i["client"] if i["client"] and i["client"] != "-" else ""
            vote = (f'<span class="pill-sm ok">{esc(conf)}</span>' if conf else
                    f'<div class="vote"><label><input type="radio" name="A-{n}" value="Đúng"> Đúng</label>'
                    f'<label><input type="radio" name="A-{n}" value="Sai"> Sai</label>'
                    '<input type="text" placeholder="Nếu sai: cách đúng là…"></div>')
            H.append(f'<tr class="arow" data-id="A-{n}"><td data-l="#" class="aid">A-{n}</td>'
                     f'<td data-l="Điểm chưa rõ" class="q">{md_inline(i["point"])}</td>'
                     f'<td data-l="Team đã chọn"><b>{md_inline(i["choice"])}</b><div class="sub">{md_inline(i["why"])}</div></td>'
                     f'<td data-l="Phương án khác">{md_inline(i["alt"] or "-")}</td>'
                     f'<td data-l="Ưu / Nhược"><div class="pro">+ {md_inline(i["pros"] or "-")}</div><div class="con">− {md_inline(i["cons"] or "-")}</div></td>'
                     f'<td data-l="Ảnh hưởng nếu sai"><span class="pill-sm {lvl(i["level"])}">{esc(i["level"] or "Chưa đánh giá")}</span>'
                     f'<div class="sub">{md_inline(i["impact"] or "Cần sửa lại phần liên quan")}</div></td>'
                     f'<td data-l="Client xác nhận">{vote}</td></tr>')
        H.append('</tbody></table></div><div class="copyrow"><button class="copybtn">Copy câu trả lời</button><span class="copied"></span></div></section>')
    else:
        H.append('<section class="okbox">Không có giả định: mọi điểm chưa rõ đã được xác nhận.</section>')

    # thiết kế: sơ đồ (SVG vẽ sẵn) + mockup đen trắng, client xác nhận
    design = design or {"diagrams": [], "mockups": []}
    if design["diagrams"] or design["mockups"]:
        vote = lambda key: (f'<div class="vote row"><label><input type="radio" name="{key}" value="Đúng"> Đúng ý</label>'
                            f'<label><input type="radio" name="{key}" value="Sai"> Chưa đúng</label>'
                            '<input type="text" placeholder="Chưa đúng ở đâu, cần thế nào…"></div>')
        H.append('<section><h2>Thiết kế: workflow và màn hình</h2><p class="muted">Sơ đồ và wireframe đen trắng để thống nhất luồng và chức năng. '
                 'Màu sắc, font khi làm thật sẽ theo giao diện hiện tại của dự án. Xác nhận từng mục bên dưới, rồi bấm <b>Copy câu trả lời</b>.</p>')
        for n, (f, title, codes, notes) in enumerate(design["diagrams"], 1):
            body = ""
            for code in codes:
                svg = mermaid_svg(code, root)
                body += (f'<div class="diagram">{svg}</div>' if svg else
                         f'<pre class="mmd">{esc(code)}</pre><p class="muted small">Chưa vẽ được hình: cài Mermaid CLI '
                         '(<code>npm i -g @mermaid-js/mermaid-cli</code>) rồi chạy lại <code>board.py report</code>.</p>')
            H.append(f'<div class="arow dblock" data-id="W-{n} {esc(title)}"><h3>W-{n} · {esc(title)} <span class="muted small">design/{esc(f)}</span></h3>'
                     + body + (f'<p class="muted">{md_inline(notes)}</p>' if notes else "") + vote(f"W-{n}") + '</div>')
        for n, (f, title, html_text) in enumerate(design["mockups"], 1):
            H.append(f'<div class="arow dblock" data-id="M-{n} {esc(title)}"><h3>M-{n} · Màn hình: {esc(title)} <span class="muted small">design/{esc(f)}</span></h3>'
                     f'<iframe class="mock" title="{esc(title)}" sandbox="allow-scripts" srcdoc="{esc(html_text)}"></iframe>'
                     + vote(f"M-{n}") + '</div>')
        H.append('<div class="copyrow"><button class="copybtn">Copy câu trả lời</button><span class="copied"></span></div></section>')

    # ô tóm tắt
    H.append('<section><h2>Kết quả</h2><div class="kpis">')
    H.append(f'<div class="kpi wide"><span>Phương án chốt</span><b>{md_inline(cv("Phương án chốt"))}</b></div>')
    for k, label in gates:
        v = cv(k)
        H.append(f'<div class="kpi {"ok" if first(k) in good else "bad"}"><span>{esc(label)}</span><b>{esc(v.split("(")[0].strip() or "-")}</b></div>')
    n_open = sum(w["status"] in OPEN_STATUS for w in whys)
    H.append(f'<div class="kpi {"bad" if n_open else "ok"}"><span>WHY đã đóng</span><b>{len(whys) - n_open}/{len(whys)}</b>'
             f'<span>{n_ok} cả team đồng ý · {len(whys) - n_open - n_ok} Lead chốt</span></div></div></section>')

    # quyết định: bảng so sánh phương án (cột = phương án)
    opts = options_of(sec.get("3", ("", ""))[1])
    score_rows = md_table(sec.get("5", ("", ""))[1])
    totals, mx = scores_of(sec.get("5", ("", ""))[1])
    chosen = sec.get("6", ("", ""))[1]
    codes = [o[0] for o in opts] or list(totals)
    if codes:
        best = max(totals.values()) if totals else None
        win = {c for c in codes if totals.get(c) is not None and totals.get(c) == best}
        field = lambda body, *keys: next((re.sub(r"^\s*[-*]\s*[^:]+:\s*", "", l) for l in body.splitlines()
                                          if re.match(r"^\s*[-*]\s*(" + "|".join(keys) + r")\s*:", l, re.I)), "")
        info = {o[0]: o for o in opts}
        th = "".join(f'<th class="{"win" if c in win else ""}"><span class="optcode">{esc(c)}</span> {md_inline(info[c][1] if c in info else "")}'
                     + ('<br><span class="pill-sm ok">Điểm cao nhất</span>' if c in win else "") + "</th>" for c in codes)
        rows = []
        for label, keys, cls in [("Mô tả", ("mô tả", "tổng thể"), ""), ("Ưu", ("ưu",), "pro"), ("Nhược", ("nhược",), "con"),
                                 ("Rủi ro", ("rủi ro",), "con"), ("Kết luận", ("kết luận",), "")]:
            vals = [field(info[c][2], *keys) if c in info else "" for c in codes]
            if any(vals):
                rows.append(f'<tr><th>{label}</th>' + "".join(f'<td class="{cls} {"win" if c in win else ""}">{md_inline(v or "-")}</td>'
                                                              for c, v in zip(codes, vals)) + "</tr>")
        for r in score_rows:
            crit = r.get("Tiêu chí", "")
            if "tổng" in crit.lower():
                continue
            cells = []
            for c in codes:
                v = (re.findall(r"\d+", r.get(c, "")) or [""])[0]
                bar = f'<div class="bar sm"><i style="width:{int(v) * 20 if v else 0}%"></i></div>' if v else ""
                cells.append(f'<td class="num {"win" if c in win else ""}">{esc(v or "-")}/5{bar}</td>')
            rows.append(f'<tr><th>{md_inline(crit)} <span class="muted">{esc(r.get("Trọng số", ""))}</span></th>' + "".join(cells) + "</tr>")
        if totals:
            rows.append('<tr class="total"><th>Tổng điểm</th>' + "".join(
                f'<td class="num {"win" if c in win else ""}"><b>{totals.get(c, "-")}</b>/{mx}<div class="bar"><i style="width:{round(100 * totals.get(c, 0) / mx) if mx else 0}%"></i></div></td>'
                for c in codes) + "</tr>")
        H.append('<section><h2>Phương án và điểm</h2><div class="tw"><table class="otable"><thead><tr><th></th>' + th + '</tr></thead><tbody>'
                 + "".join(rows) + '</tbody></table></div>')
        if chosen:
            items = [re.sub(r"^\s*[-*]\s*", "", l) for l in chosen.splitlines() if l.strip()]
            H.append('<div class="decision"><h3>Quyết định</h3><ul>' + "".join(f"<li>{md_inline(x)}</li>" for x in items) + '</ul></div>')
        H.append('</section>')

    # timeline debate
    if rounds:
        H.append('<section><h2>Diễn biến debate</h2><ol class="timeline">')
        for r in rounds:
            who = {}
            for m in msgs:
                if m["stage"] == r["stage"] and m["round"] == r["round"]:
                    who[m["role"]] = who.get(m["role"], 0) + 1
            sm = summaries.get((r["stage"], r["round"]), "")
            H.append(f'<li><div class="tl-head"><b>{r["stage"]}-R{r["round"]}</b> {esc(r["goal"])}</div>'
                     f'<div class="chips">{"".join(f"<span class=chip>{esc(k)} · {v}</span>" for k, v in who.items()) or "<span class=muted>không có bài post</span>"}</div>'
                     + (f'<p>{md_inline(sm)}</p>' if sm else "") + '</li>')
        H.append('</ol></section>')

    # WHY
    if whys:
        label = {"agreed": ("ok", "Cả team đồng ý"), "ruled": ("warn", "Lead phán quyết"), "assumption": ("bad", "Giả định"),
                 "open": ("warn", "Chờ trả lời"), "voting": ("warn", "Chờ biểu quyết")}
        H.append(f'<section><h2>WHY: hỏi đến khi cả team đồng ý</h2><div class="whys">')
        for w in whys:
            cls, txt = label.get(w["status"], ("warn", w["status"]))
            agree = sorted({l["role"] for l in logs if l["why_id"] == w["id"] and l["vote"] == "AGREE" and l["answer_no"] == w["answers"]})
            dis = [l for l in logs if l["why_id"] == w["id"] and l["vote"] == "DISAGREE"]
            H.append(f'<article class="why"><div class="why-top"><b>WHY-{w["id"]}</b><span class="muted">{esc(w["asker"])} → {esc(w["target"])}</span>'
                     f'<span class="pill-sm {cls}">{txt}</span></div><h3>{md_inline(w["question"])}</h3>'
                     f'<p class="answer">{md_inline(w["answer"] or "Chưa trả lời")}</p>'
                     + (f'<p class="note">{md_inline(w["note"])}</p>' if w["note"] else "")
                     + '<div class="chips">' + "".join(f'<span class="chip ok">✓ {esc(x)}</span>' for x in agree)
                     + "".join(f'<span class="chip bad" title="{esc(l["reason"])}">✗ {esc(l["role"])} (lần {l["answer_no"]})</span>' for l in dis)
                     + '</div>'
                     + (('<details><summary>Lý do không đồng ý</summary><ul>' + "".join(
                         f'<li><b>{esc(l["role"])}</b> (lần trả lời {l["answer_no"]}): {md_inline(l["reason"])}</li>' for l in dis) + '</ul></details>') if dis else "")
                     + '</article>')
        H.append('</div></section>')

    # bảng còn lại
    def table(title, num, collapsed=False):
        rows = md_table(sec.get(num, ("", ""))[1])
        if not rows:
            return
        head = list(rows[0].keys())
        t = '<div class="tw"><table><tr>' + "".join(f"<th>{md_inline(h)}</th>" for h in head) + "</tr>" + "".join(
            "<tr>" + "".join(f"<td>{md_inline(r.get(h, ''))}</td>" for h in head) + "</tr>" for r in rows) + "</table></div>"
        H.append(f'<section><details{" " if collapsed else " open"}><summary><h2>{esc(title)}</h2></summary>{t}</details></section>')
    table("Ý kiến từng role", "7")
    table("Phán quyết của Lead", "8")
    table("Gap phát hiện khi làm", "14")
    table("Kết quả test", "10", True)
    table("Kết quả review", "11", True)
    roles = sorted({m["role"] for m in msgs} | set(team))
    if roles:
        H.append('<section><details><summary><h2>Tham gia theo role</h2></summary><div class="tw"><table><tr><th>Role</th><th>Bài post</th>'
                 '<th>WHY đã hỏi</th><th>WHY bị hỏi</th><th>Đồng ý</th><th>Không đồng ý</th></tr>' + "".join(
                     f'<tr><td>{esc(r)}</td><td>{sum(m["role"] == r for m in msgs)}</td><td>{sum(w["asker"] == r for w in whys)}</td>'
                     f'<td>{sum(w["target"] == r for w in whys)}</td><td>{sum(l["role"] == r and l["vote"] == "AGREE" for l in logs)}</td>'
                     f'<td>{sum(l["role"] == r and l["vote"] == "DISAGREE" for l in logs)}</td></tr>' for r in roles) + '</table></div></details></section>')
    H.append('<footer class="muted">Tạo bằng <code>board.py report</code> từ board SQLite + TASK.md. Không sửa tay, chạy lại lệnh để cập nhật.</footer>')

    css = """:root{--bg:#f6f7f9;--card:#fff;--text:#1d2330;--muted:#667085;--line:#e4e7ec;--ok:#067647;--okbg:#ecfdf3;--bad:#b42318;--badbg:#fef3f2;--warn:#b54708;--warnbg:#fffaeb;--accent:#3538cd;--accentbg:#eef4ff}
@media (prefers-color-scheme:dark){:root{--bg:#0f1218;--card:#171b24;--text:#e6e9ef;--muted:#98a2b3;--line:#2a303c;--ok:#47cd89;--okbg:#0c2a1c;--bad:#f97066;--badbg:#2d1414;--warn:#fdb022;--warnbg:#2b2110;--accent:#8098f9;--accentbg:#1a2040}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}h1{font-size:26px;margin:2px 0 4px;word-break:break-all}h2{font-size:18px;margin:0 0 12px}h3{font-size:15px;margin:4px 0 8px}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:16px}.eyebrow{margin:0;text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:var(--muted)}
.muted{color:var(--muted)}section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
blockquote{margin:0 0 14px;padding:12px 16px;background:var(--accentbg);border-left:4px solid var(--accent);border-radius:8px}
.pill,.pill-sm{display:inline-block;border-radius:999px;font-weight:600;white-space:nowrap}.pill{padding:6px 14px}.pill-sm{padding:2px 10px;font-size:12px}
.ok{color:var(--ok);background:var(--okbg)}.bad{color:var(--bad);background:var(--badbg)}.warn{color:var(--warn);background:var(--warnbg)}
.alert{border:2px solid var(--bad);background:var(--badbg)}.alert h2,.alert>p{color:var(--bad)}.okbox{color:var(--ok);background:var(--okbg)}
.atable td.q{color:var(--bad);font-weight:600;min-width:170px}.atable td{min-width:130px}.atable td.aid{min-width:0;font-weight:700;color:var(--bad);white-space:nowrap}
div.pro{color:var(--ok)}div.con{color:var(--bad);margin-top:4px}.atable .pill-sm{margin-bottom:4px}
.sub{color:var(--muted);font-size:13px;margin-top:4px}td.pro{color:var(--ok)}td.con{color:var(--bad)}.alert table{background:var(--card);border-radius:10px}
.vote{display:flex;flex-direction:column;gap:6px;min-width:150px}.vote label{white-space:nowrap}
.otable th{width:170px}.otable thead th{width:auto;color:var(--text);font-size:15px}.otable td.win,.otable th.win{background:var(--okbg)}
.otable td.num{white-space:nowrap}.bar.sm{height:5px;margin-top:4px;width:80px}.otable tr.total td{font-size:16px}
.otable .optcode{width:26px;height:26px;margin-right:6px}
@media (max-width:720px){.atable thead{display:none}.atable,.atable tbody,.atable tr,.atable td{display:block;width:100%}
.atable tr{border:1px solid var(--bad);border-radius:10px;margin-bottom:10px;padding:6px 10px;background:var(--card)}
.atable td{border:0;padding:4px 0;min-width:0}.atable td:before{content:attr(data-l);display:block;font-size:12px;color:var(--muted)}}
dl{margin:0}dt{font-size:12px;color:var(--muted);margin-top:8px}dd{margin:2px 0 0}
dd.chosen{font-weight:600}
.vote input[type=text]{flex:1 1 100%;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--text)}.confirmed{margin:10px 0 0;color:var(--ok)}
.copyrow{margin-top:12px;display:flex;gap:10px;align-items:center}button{background:var(--bad);color:#fff;border:0;border-radius:8px;padding:9px 16px;font-weight:600;cursor:pointer}
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}.kpi{border-radius:10px;padding:10px 12px;border:1px solid var(--line)}.kpi span{display:block;font-size:12px;opacity:.85}.kpi b{font-size:17px}
.kpi.wide{grid-column:1/-1;background:var(--accentbg);color:var(--text)}.kpi.wide b{font-size:15px}
.opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}.opt{border:1px solid var(--line);border-radius:12px;padding:14px}.opt.win{border:2px solid var(--ok)}
.optcode{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:8px;background:var(--accentbg);color:var(--accent);font-weight:700}.win .optcode{background:var(--okbg);color:var(--ok)}
.bar{height:8px;background:var(--line);border-radius:99px;overflow:hidden;margin-top:8px}.bar i{display:block;height:100%;background:var(--accent)}.win .bar i{background:var(--ok)}.score{margin:4px 0;font-weight:600;font-size:13px}
.opt .pill-sm{color:var(--ok);background:var(--okbg)}.decision{margin-top:14px;padding:12px 14px;border-radius:10px;background:var(--okbg)}.decision h3{color:var(--ok)}.decision ul{margin:0;padding-left:18px}
.timeline{list-style:none;margin:0;padding:0 0 0 18px;border-left:2px solid var(--line)}.timeline li{position:relative;padding:0 0 14px 12px}.timeline li:before{content:"";position:absolute;left:-25px;top:5px;width:12px;height:12px;border-radius:50%;background:var(--accent)}
.timeline p{margin:6px 0 0;color:var(--muted)}.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.chip{font-size:12px;padding:2px 8px;border-radius:999px;background:var(--bg);border:1px solid var(--line)}
.chip.ok,.chip.bad{border-color:transparent}.whys{display:grid;gap:12px}.why{border:1px solid var(--line);border-radius:12px;padding:14px}.why-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.answer{margin:6px 0;padding:8px 10px;border-radius:8px;background:var(--bg)}.note{color:var(--warn);font-size:13px}details summary{cursor:pointer}details summary h2{display:inline;margin:0}
.tw{overflow-x:auto;margin-top:10px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
.dblock{border:1px solid var(--line);border-radius:12px;padding:14px;margin-top:12px}.diagram{background:#fff;border-radius:10px;padding:10px;overflow-x:auto;text-align:center}
.diagram svg{max-width:100%;height:auto}.mock{width:100%;height:560px;border:1px solid var(--line);border-radius:10px;background:#fff}.small{font-size:12px;font-weight:400}
.vote.row{flex-direction:row;flex-wrap:wrap;align-items:center;margin-top:10px}.vote.row input[type=text]{flex:1 1 220px}pre.mmd{background:var(--bg);padding:10px;border-radius:8px;overflow-x:auto;font-size:12px}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:var(--bg);padding:1px 5px;border-radius:4px}footer{margin-top:20px;font-size:13px}
@media print{body{background:#fff}section{break-inside:avoid}.copyrow,.vote{display:none}details{display:block}}"""
    js = """document.querySelectorAll('.copybtn').forEach(function(btn){btn.addEventListener('click',function(){
var out=[];document.querySelectorAll('.arow').forEach(function(c){var id=c.dataset.id,r=c.querySelector('input[type=radio]:checked'),t=c.querySelector('input[type=text]');
if(!r&&!(t&&t.value)&&!c.querySelector('input[type=radio]'))return;
out.push(id+': '+(r?r.value:'chưa chọn')+(t&&t.value?' - '+t.value:''));});var txt=out.join('\\n');
var msg=btn.parentNode.querySelector('.copied');
(navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){msg.textContent='Đã copy cả giả định và thiết kế, dán vào email/chat gửi team.';},
function(){prompt('Copy nội dung sau:',txt);});});});"""
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Báo cáo {esc(task)}</title><style>{css}</style></head><body><main>' + "\n".join(H) + f"</main><script>{js}</script></body></html>\n")


def cmd_report(db, a):
    root = find_root()
    tdir = os.path.join(root, "docs", "agent-tasks", a.task)
    tpath = a.task_md or os.path.join(tdir, "TASK.md")
    ttext = open(tpath, encoding="utf-8").read() if os.path.isfile(tpath) else ""
    sec = task_sections(ttext)
    team = sorted(team_of(db, a.task))
    msgs = db.execute("SELECT * FROM messages WHERE task=? ORDER BY id", (a.task,)).fetchall()
    whys = db.execute("SELECT * FROM whys WHERE task=? ORDER BY id", (a.task,)).fetchall()
    logs = db.execute("SELECT l.* FROM vote_log l JOIN whys w ON w.id=l.why_id WHERE w.task=? ORDER BY l.id", (a.task,)).fetchall()
    st = {s: sum(w["status"] == s for w in whys) for s in ("agreed", "ruled", "assumption", "open", "voting")}
    L = [f"# Báo cáo task `{a.task}`", "",
         f"> Tạo bằng `board.py report` lúc {time.strftime('%Y-%m-%d %H:%M')}. Nguồn: board SQLite + `TASK.md`. Không sửa tay, chạy lại lệnh để cập nhật.", ""]

    L += ["## Giả định cần client xác nhận", ""] + assumption_block(collect_assumptions(db, a.task, sec))
    design = load_design(tdir)
    if design["diagrams"] or design["mockups"]:
        L += ["## Thiết kế: workflow và màn hình (client xác nhận)", ""]
        for n, (f, title, codes, notes) in enumerate(design["diagrams"], 1):
            L += [f"### W-{n} · {title} (`design/{f}`)", ""] + sum([["```mermaid", c.rstrip(), "```", ""] for c in codes], []) + ["☐ Đúng ý ☐ Chưa đúng: ……", ""]
        for n, (f, title, _) in enumerate(design["mockups"], 1):
            L += [f"- M-{n} · Màn hình **{title}**: mở `design/{f}` bằng trình duyệt · ☐ Đúng ý ☐ Chưa đúng: ……"]
        L += [""]
    L += ["## 1. Kết quả", "", "| Mục | Giá trị |", "|---|---|"]
    L += [f"| {k} | {cell(cond_value(ttext, k))} |" for k in COND_KEYS]
    if sec.get("0", ("", ""))[1]:
        L += ["", "**Yêu cầu gốc:**", ""] + ["> " + x for x in sec["0"][1].splitlines()[:8] if not x.startswith(">")]
    L += [""]

    L += ["## 2. Debate qua số liệu", "", "| Chỉ số | Giá trị |", "|---|---|",
          f"| Team debate | {', '.join(team) or '-'} |",
          f"| Số lượt | {db.execute('SELECT count(*) FROM rounds WHERE task=?', (a.task,)).fetchone()[0]} |",
          f"| Số bài post | {len(msgs)} |",
          f"| WHY đã hỏi | {len(whys)} |",
          f"| WHY cả team đồng ý | {st['agreed']} |",
          f"| WHY Lead phán quyết / Assumption | {st['ruled']} / {st['assumption']} |",
          f"| WHY còn mở | {st['open'] + st['voting']} |",
          f"| Tổng số lần trả lời WHY | {sum(w['answers'] for w in whys)} |",
          f"| Số phiếu DISAGREE | {sum(l['vote'] == 'DISAGREE' for l in logs)} |", ""]
    roles = sorted({m["role"] for m in msgs} | set(team))
    L += ["| Role | Bài post | WHY đã hỏi | WHY bị hỏi | AGREE | DISAGREE |", "|---|---|---|---|---|---|"]
    for r in roles:
        L.append(f"| {r} | {sum(m['role'] == r for m in msgs)} | {sum(w['asker'] == r for w in whys)} | "
                 f"{sum(w['target'] == r for w in whys)} | {sum(l['role'] == r and l['vote'] == 'AGREE' for l in logs)} | "
                 f"{sum(l['role'] == r and l['vote'] == 'DISAGREE' for l in logs)} |")
    L += [""]

    L += ["## 3. Diễn biến từng lượt", "", "| Lượt | Mục tiêu | Ai post (số bài) | Tóm tắt của Lead |", "|---|---|---|---|"]
    for r in db.execute("SELECT * FROM rounds WHERE task=? ORDER BY id", (a.task,)):
        cnt = {}
        for m in msgs:
            if m["stage"] == r["stage"] and m["round"] == r["round"]:
                cnt[m["role"]] = cnt.get(m["role"], 0) + 1
        summ = db.execute("SELECT body FROM summaries WHERE task=? AND stage=? AND round=? ORDER BY id DESC LIMIT 1",
                          (a.task, r["stage"], r["round"])).fetchone()
        L.append(f"| {r['stage']}-R{r['round']} | {cell(r['goal'])} | {', '.join(f'{k} ({v})' for k, v in cnt.items()) or '-'} | "
                 f"{cell(summ['body'] if summ else '', 160)} |")
    L += [""]

    L += ["## 4. WHY: câu hỏi, kết luận, ai đồng ý", "",
          "| WHY | Hỏi → | Câu hỏi | Kết luận cuối | Lần trả lời | Đồng ý | Không đồng ý (lý do, lần trả lời) | Trạng thái |",
          "|---|---|---|---|---|---|---|---|"]
    for w in whys:
        agree = sorted({l["role"] for l in logs if l["why_id"] == w["id"] and l["vote"] == "AGREE" and l["answer_no"] == w["answers"]})
        dis = [f"{l['role']}: {l['reason']} (lần {l['answer_no']})" for l in logs if l["why_id"] == w["id"] and l["vote"] == "DISAGREE"]
        concl = w["answer"] or ""
        if w["note"]:
            concl += f" · {w['note']}"
        L.append(f"| WHY-{w['id']} | {w['asker']} → {w['target']} | {cell(w['question'])} | {cell(concl, 160)} | {w['answers']} | "
                 f"{', '.join(agree) or '-'} | {cell('; '.join(dis), 200)} | {w['status']} |")
    if not whys:
        L.append("| - | - | - | - | - | - | - | - |")
    L += [""]

    for num, title in [("3", "Phương án"), ("5", "Bảng điểm"), ("6", "Phương án chốt"), ("7", "Ý kiến từng role"),
                       ("8", "Phán quyết của Lead"), ("14", "Gap phát hiện khi làm"),
                       ("10", "Kết quả test"), ("11", "Kết quả review")]:
        body = sec.get(num, ("", ""))[1]
        if body:
            L += [f"## {title} (TASK.md mục {num})", "", body, ""]
    out = a.out or os.path.join(tdir, "REPORT.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    md = "\n".join(L).rstrip() + "\n"
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    hout = os.path.splitext(out)[0] + ".html"
    rounds = db.execute("SELECT * FROM rounds WHERE task=? ORDER BY id", (a.task,)).fetchall()
    summaries = {}
    for x in db.execute("SELECT * FROM summaries WHERE task=? ORDER BY id", (a.task,)):
        summaries[(x["stage"], x["round"])] = x["body"]
    with open(hout, "w", encoding="utf-8") as f:
        f.write(render_dashboard(a.task, ttext, sec, team, msgs, whys, logs, rounds, summaries,
                                 collect_assumptions(db, a.task, sec), design, root))
    print(f"Đã tạo báo cáo {out} và {hout}")


# ---------- trạng thái agent (nhịp tim): hook ghi, Lead `wait`, status line đọc ----------

def current_run(db, task, root=None):
    """Lượt đang mở (S2-R3), không có thì giai đoạn hiện tại (S3), không có nữa thì '-'."""
    r = open_round(db, task)
    if r:
        return f"{r['stage']}-R{r['round']}"
    try:
        return open(os.path.join(root or find_root(), ".agent-team", "stage"), encoding="utf-8").read().strip().upper() or "-"
    except OSError:
        return "-"


def hang_minutes(root):
    try:
        for line in open(os.path.join(root, ".claude", "agent-team.config"), encoding="utf-8", errors="ignore"):
            m = re.match(r"^\s*HANG_MINUTES=\s*['\"]?(\d+)", line)
            if m:
                return int(m.group(1))
    except OSError:
        pass
    return 10


def run_row(db, task, role, run):
    return db.execute("SELECT * FROM agent_runs WHERE task=? AND role=? AND run=?", (task, role, run)).fetchone()


def touch_run(db, task, role, run, **kw):
    now = int(time.time())
    if not run_row(db, task, role, run):
        db.execute("INSERT INTO agent_runs(task, role, run, started_at, last_seen) VALUES(?,?,?,?,?)", (task, role, run, now, now))
    sets = ", ".join(f"{k}=?" for k in kw)
    db.execute(f"UPDATE agent_runs SET last_seen=?{', ' + sets if sets else ''} WHERE task=? AND role=? AND run=?",
               (now, *kw.values(), task, role, run))
    db.commit()


def cmd_done(db, a):
    role, run = norm_role(a.role), current_run(db, a.task)
    row = run_row(db, a.task, role, run)
    if row and row["state"] == "DONE":
        die(f"{role} đã DONE ở {run}. KẾT THÚC NGAY: trả kết quả về Lead, không post / done lại")
    body = read_body(a)
    if body.count("\n") + 1 > 5:
        die("kết quả done tối đa 5 dòng (chi tiết đã nằm trên board / file)")
    touch_run(db, a.task, role, run, state="DONE", result=body, ended_at=int(time.time()), busy_since=None)
    print(f"Đã ghi DONE {role} ({run}). KẾT THÚC NGAY: trả kết quả về Lead, không chờ Lead trả lời.")


def cmd_progress(db, a):
    role, run = norm_role(a.role), current_run(db, a.task)
    touch_run(db, a.task, role, run, step=a.step, eta_min=a.eta)
    print(f"Đã ghi tiến độ {role}: {a.step}" + (f", còn ~{a.eta} phút" if a.eta else ""))


def typical_minutes(db, role):
    xs = sorted((r[0] - r[1]) / 60 for r in db.execute(
        "SELECT ended_at, started_at FROM agent_runs WHERE role=? AND state='DONE' AND ended_at IS NOT NULL", (role,)))
    return round(xs[len(xs) // 2]) if xs else None


def agent_view(db, task, run, roles, hang_s, since):
    """[(role, kind, dòng)] kind: done | running | stuck | waiting."""
    now, out = int(time.time()), []
    rows = {r["role"]: r for r in db.execute("SELECT * FROM agent_runs WHERE task=? AND run=?", (task, run))}
    for role in roles or sorted(rows):
        r = rows.get(role)
        if not r:
            idle = now - since
            out.append((role, "stuck" if idle > hang_s else "waiting",
                        f"{role}: chưa bắt đầu ({idle // 60} phút)" + (" ⚠ có thể bị từ chối chạy / chờ duyệt quyền" if idle > hang_s else "")))
            continue
        if r["state"] == "DONE":
            out.append((role, "done", f"{role}: DONE · {(r['result'] or '').splitlines()[0][:120] if r['result'] else ''}"))
            continue
        idle = now - r["last_seen"]
        limit = max(hang_s, (r["tool_timeout"] or 0) + 60) if r["busy_since"] else hang_s
        typ = typical_minutes(db, role)
        info = (f" · {r['step']}" if r["step"] else "") + (f" · còn ~{r['eta_min']} phút" if r["eta_min"] else "") + \
               (f" · thường mất ~{typ} phút" if typ else "")
        tool = f" · {'đang chạy' if r['busy_since'] else 'tool cuối'}: {r['last_tool']}" if r["last_tool"] else ""
        if idle > limit:
            out.append((role, "stuck", f"{role}: ⚠ im {idle // 60} phút{tool}{info}"))
        else:
            out.append((role, "running", f"{role}: đang làm (lần cuối {idle}s trước){tool}{info}"))
    return out


def expected_roles(db, task, a_roles):
    if a_roles:
        return [norm_role(x) for x in a_roles.split(",") if x.strip()]
    r = open_round(db, task)
    return [x for x in ((r["roles"] if r else "") or "").split(",") if x]


def cmd_wait(db, a):
    """Đọc trạng thái mỗi `--interval` giây. Trả về khi: mọi agent DONE (0), có agent im quá ngưỡng (3), hết `--max` giây (4)."""
    root = find_root()
    hang_s = (a.hang or hang_minutes(root)) * 60
    r = open_round(db, a.task)
    since = r["opened_at"] if r else int(time.time())
    start = time.time()
    while True:
        run = current_run(db, a.task, root)
        roles = expected_roles(db, a.task, a.roles)
        view = agent_view(db, a.task, run, roles, hang_s, since)
        if not view:
            print("Không có agent nào để chờ (thêm --roles a,b)")
            return
        kinds = {k for _, k, _ in view}
        done_all = kinds == {"done"}
        if done_all or "stuck" in kinds or time.time() - start >= a.max:
            head = ("XONG: mọi agent DONE" if done_all else "CÓ AGENT TREO: dừng (TaskStop) rồi gọi lại kèm lý do"
                    if "stuck" in kinds else "CHƯA XONG, đang chạy bình thường: gọi wait lần nữa")
            print(f"[{run}] {head}")
            print("\n".join(line for _, _, line in view))
            sys.exit(0 if done_all else 3 if "stuck" in kinds else 4)
        time.sleep(a.interval)
        db.commit()  # đọc bản mới nhất (WAL)


def cmd_stuck(db, a):
    root = find_root()
    hang_s = (a.hang or hang_minutes(root)) * 60
    run = current_run(db, a.task, root)
    r = open_round(db, a.task)
    view = agent_view(db, a.task, run, expected_roles(db, a.task, None), hang_s, r["opened_at"] if r else int(time.time()))
    bad = [(role, line) for role, k, line in view if k == "stuck"]
    if not bad:
        print("Không có agent treo")
        return
    for role, line in bad:
        print(line)
        row = run_row(db, a.task, role, run)
        if row and row["busy_since"] and row["last_tool"] and row["last_tool"].startswith("Bash: "):
            key = row["last_tool"][6:].split("&&")[0].strip()[:40]
            print(f"  tắt lệnh đang kẹt (terminal khác): pgrep -fl {json.dumps(key)}  →  kill <PID>")


def heartbeat(event, data):
    """Hook gọi: Pre / Post (mọi tool) và SubagentStop. Chỉ ghi cho subagent (có agent_type). Không bao giờ chặn."""
    role = norm_role(data.get("agent_type") or "")
    if not role:
        return
    os.chdir(data.get("cwd") or os.getcwd())
    root = find_root()
    if not os.path.isfile(os.path.join(root, ".claude", "agent-team.config")):
        return
    tasks = [p for p in (os.path.join(root, "docs", "agent-tasks", d, "TASK.md")
                         for d in (os.listdir(os.path.join(root, "docs", "agent-tasks")) if os.path.isdir(os.path.join(root, "docs", "agent-tasks")) else []))
             if os.path.isfile(p)]
    if not tasks:
        return
    task = os.path.basename(os.path.dirname(max(tasks, key=os.path.getmtime)))
    db = connect()
    run = current_run(db, task, root)
    if event == "stop":
        row = run_row(db, task, role, run)
        if row and row["state"] != "DONE":
            touch_run(db, task, role, run, state="DONE", busy_since=None, ended_at=int(time.time()),
                      result=row["result"] or "(agent kết thúc nhưng chưa chạy board.py done: xem bài post / kết quả trả về)")
        return
    ti = data.get("tool_input") or {}
    tool = data.get("tool_name") or "?"
    desc = f"Bash: {ti.get('command', '')}" if tool == "Bash" else f"{tool}: {os.path.basename(ti.get('file_path') or ti.get('path') or ti.get('pattern') or '')}"
    desc = " ".join(desc.split())[:80]
    if event == "pre":
        m = re.search(r"\btimeout\s+(\d+)", ti.get("command", "") if tool == "Bash" else "")
        touch_run(db, task, role, run, last_tool=desc, busy_since=int(time.time()), tool_timeout=int(m.group(1)) if m else None)
    else:
        touch_run(db, task, role, run, busy_since=None)


def main(argv=None):
    p = argparse.ArgumentParser(prog="board.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    o = sp.add_parser("open")
    o.add_argument("task"), o.add_argument("stage"), o.add_argument("round", type=int)
    o.add_argument("--roles"), o.add_argument("--goal")
    for name in ("close", "status"):
        sp.add_parser(name).add_argument("task")
    po = sp.add_parser("post")
    po.add_argument("task"), po.add_argument("--role", required=True)
    po.add_argument("--reply", type=int), po.add_argument("--mention"), po.add_argument("--body")
    r = sp.add_parser("read")
    r.add_argument("task"), r.add_argument("--all", action="store_true")
    r.add_argument("--stage"), r.add_argument("--round", type=int), r.add_argument("--mention")
    r.add_argument("--since", type=int), r.add_argument("--why", type=int, help="chỉ 1 câu WHY: câu hỏi, trả lời, phiếu, dòng nhắc tới")
    s = sp.add_parser("summary")
    s.add_argument("task"), s.add_argument("--body")
    e = sp.add_parser("export")
    e.add_argument("task"), e.add_argument("--out")
    t = sp.add_parser("team")
    t.add_argument("task"), t.add_argument("--roles", required=True)
    w = sp.add_parser("whys")
    w.add_argument("task"), w.add_argument("--open", action="store_true")
    c = sp.add_parser("why-close")
    c.add_argument("task"), c.add_argument("n", type=int)
    c.add_argument("--as", dest="as_", choices=["ruling", "assumption"], required=True), c.add_argument("--note", required=True)
    d = sp.add_parser("done", help="agent báo xong (≤ 5 dòng kết quả), sau đó không post thêm ở lượt này")
    d.add_argument("task"), d.add_argument("--role", required=True), d.add_argument("--body")
    g = sp.add_parser("progress", help="agent báo tiến độ việc dài")
    g.add_argument("task"), g.add_argument("--role", required=True), g.add_argument("--step", required=True), g.add_argument("--eta", type=int)
    wt = sp.add_parser("wait", help="Lead chờ agent nền: đọc trạng thái mỗi --interval giây")
    wt.add_argument("task"), wt.add_argument("--roles"), wt.add_argument("--hang", type=int, help="phút im lặng coi là treo (mặc định HANG_MINUTES / 10)")
    wt.add_argument("--interval", type=int, default=30), wt.add_argument("--max", type=int, default=540, help="giây tối đa 1 lần chờ (lệnh Bash tối đa 10 phút)")
    sk = sp.add_parser("stuck", help="agent đang treo + lệnh đang kẹt")
    sk.add_argument("task"), sk.add_argument("--hang", type=int)
    rp = sp.add_parser("report")
    rp.add_argument("task"), rp.add_argument("--task-md"), rp.add_argument("--out")
    a = p.parse_args(argv)
    db = connect()
    globals()[f"cmd_{a.cmd.replace('-', '_')}"](db, a)


if __name__ == "__main__":
    main()
