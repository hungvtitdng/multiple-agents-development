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


def cmd_read(db, a):
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

COND_KEYS = ["Loại", "Phương án chốt", "Security duyệt solution", "Kết quả test", "Lint/format", "Gap còn mở",
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
                      "impact": pick(r, "nếu sai"), "who": pick(r, "đề xuất"), "client": pick(r, "client")})
    seen = " ".join(" ".join(i.values()) for i in items)
    for w in db.execute("SELECT * FROM whys WHERE task=? AND status='assumption' ORDER BY id", (task,)):
        if f"WHY-{w['id']}" in seen:
            continue
        items.append({"point": w["question"], "choice": (w["note"] or "").split(": ", 1)[-1].split(". Không đồng ý")[0],
                      "why": f"Lead chốt sau {w['answers']} lần trả lời (WHY-{w['id']})", "impact": "",
                      "who": f"{w['asker']} → {w['target']}", "client": ""})
    return [i for i in items if i["point"]]


def assumption_block(items):
    if not items:
        return ["> [!NOTE]", "> Không có giả định: mọi điểm chưa rõ đã được xác nhận hoặc có trong yêu cầu.", ""]
    L = ["> [!CAUTION]",
         f"> **🔴 {len(items)} giả định cần client xác nhận.** Khi yêu cầu chưa rõ, team đã tự chọn cách hiểu dưới đây để không dừng việc. "
         "Vui lòng đánh dấu **Đúng / Sai** từng dòng; sai thì ghi cách đúng, team sẽ sửa.", "",
         "| # | 🔴 Điểm chưa rõ | Team đã chọn | Vì sao chọn | Nếu sai thì | Client xác nhận |", "|---|---|---|---|---|---|"]
    for n, i in enumerate(items, 1):
        L.append(f"| A-{n} | 🔴 **{cell(i['point'], 200)}** | {cell(i['choice'], 200)} | {cell(i['why'], 200)} | "
                 f"{cell(i['impact'] or 'Cần sửa lại phần liên quan', 200)} | {cell(i['client'], 80) if i['client'] and i['client'] != '-' else '☐ Đúng ☐ Sai: ……'} |")
    return L + [""]


def md_inline(s):
    import html
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)


def md_to_html(md, title):
    """Chuyển phần markdown do report sinh ra (heading, bảng, quote, list, code) sang HTML tự chứa."""
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre>" + md_inline("\n".join(lines[i + 1:j])) + "</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", l)
        if m:
            out.append(f"<h{len(m.group(1))}>{md_inline(m.group(2))}</h{len(m.group(1))}>")
        elif l.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i].lstrip(">").strip())
                i += 1
            kind = "caution" if block and block[0] == "[!CAUTION]" else "note" if block and block[0] == "[!NOTE]" else "quote"
            body = [b for b in block if not b.startswith("[!")]
            out.append(f'<div class="{kind}">' + "<br>".join(md_inline(b) for b in body) + "</div>")
            continue
        elif l.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            red = any("🔴" in c for c in rows[0])
            html_rows = ["<tr>" + "".join(f"<th>{md_inline(c)}</th>" for c in rows[0]) + "</tr>"]
            for r in rows[2:]:
                html_rows.append(f'<tr{" class=red" if red else ""}>' + "".join(f"<td>{md_inline(c)}</td>" for c in r) + "</tr>")
            out.append('<div class="tw"><table>' + "".join(html_rows) + "</table></div>")
            continue
        elif re.match(r"^\s*([-*]|\d+\.)\s+", l):
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{md_inline(x)}</li>" for x in items) + "</ul>")
            continue
        elif l.strip():
            out.append(f"<p>{md_inline(l)}</p>")
        i += 1
    css = """body{font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:#1f2328;background:#fff;max-width:1100px;margin:0 auto;padding:24px 16px}
h1{font-size:24px;margin:0 0 8px}h2{font-size:19px;margin:28px 0 8px;padding-bottom:4px;border-bottom:1px solid #d0d7de}
h3{font-size:16px;margin:18px 0 6px}.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:8px 0;font-size:14px}
th,td{border:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top}th{background:#f6f8fa}
code,pre{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#f6f8fa;border-radius:4px}code{padding:1px 4px}pre{padding:10px;overflow-x:auto}
.quote,.note{border-left:4px solid #8c959f;padding:8px 12px;color:#57606a;margin:8px 0}.note{border-color:#0969da;color:#1f2328}
.caution{border:2px solid #cf222e;background:#ffebe9;color:#82071e;padding:12px 14px;border-radius:6px;margin:12px 0}
tr.red td{color:#82071e;background:#fff5f5}tr.red td:first-child{font-weight:600}td:first-child{white-space:nowrap}
@media print{body{max-width:none}.tw{overflow:visible}}"""
    import html
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{css}</style></head><body>" + "\n".join(out) + "</body></html>\n")


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
    with open(hout, "w", encoding="utf-8") as f:
        f.write(md_to_html(md, f"Báo cáo {a.task}"))
    print(f"Đã tạo báo cáo {out} và {hout}")


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
    r.add_argument("--since", type=int)
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
    rp = sp.add_parser("report")
    rp.add_argument("task"), rp.add_argument("--task-md"), rp.add_argument("--out")
    a = p.parse_args(argv)
    db = connect()
    globals()[f"cmd_{a.cmd.replace('-', '_')}"](db, a)


if __name__ == "__main__":
    main()
