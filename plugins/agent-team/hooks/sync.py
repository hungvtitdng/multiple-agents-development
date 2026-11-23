#!/usr/bin/env python3
"""agent-team sync (SessionStart): project đã init thì
- chép lại script của plugin sang .claude/agent-team/ khi khác bản (update plugin không tự chép);
- thêm statusLine vào .claude/settings.json nếu chưa có.
In 1-2 dòng cho Lead. Không bao giờ chặn: lỗi gì cũng exit 0.
Chạy tay: python3 <plugin>/hooks/sync.py <thư mục project>"""
import filecmp
import json
import os
import shutil
import sys

STATUS_CMD = "python3 .claude/agent-team/progress.py"
SCRIPTS = ("board.py", "progress.py", "gap-check.py", "owner-form.py", "kb-check.py", "agent-db-clone.sh")
TEMPLATES = ("TASK.md", "POST.md", "SUMMARY.md", "CONTEXT.md", "MOCKS.md")


def find_root(d):
    d = os.path.abspath(d)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def sync_scripts(plugin, root):
    src, dst = os.path.join(plugin, "scripts"), os.path.join(root, ".claude", "agent-team")
    os.makedirs(dst, exist_ok=True)
    done = []
    for f in SCRIPTS:
        s, t = os.path.join(src, f), os.path.join(dst, f)
        if not os.path.isfile(s):
            continue
        # board.py, progress.py luôn có; script khác chỉ cập nhật khi project đã dùng (đã có bản copy)
        if os.path.isfile(t) and filecmp.cmp(s, t, shallow=False):
            continue
        if not os.path.isfile(t) and f not in ("board.py", "progress.py"):
            continue
        shutil.copyfile(s, t)
        os.chmod(t, 0o755)
        done.append(f)
    return done


def stale_templates(plugin, root):
    out = []
    for f in TEMPLATES:
        s, t = os.path.join(plugin, "templates", f), os.path.join(root, ".claude", "agent-team", "templates", f)
        if os.path.isfile(s) and os.path.isfile(t) and not filecmp.cmp(s, t, shallow=False):
            out.append(f)
    return out


def ensure_status_line(root):
    p = os.path.join(root, ".claude", "settings.json")
    data = {}
    if os.path.isfile(p):
        try:
            data = json.load(open(p, encoding="utf-8"))
        except ValueError:
            return "settings.json lỗi JSON, không sửa: tự thêm statusLine"
        if not isinstance(data, dict):
            return "settings.json không phải object, không sửa"
    cur = data.get("statusLine")
    if cur:
        return "" if (cur.get("command") if isinstance(cur, dict) else "") == STATUS_CMD else \
            f"statusLine đang là lệnh khác, không ghi đè. Muốn xem bước: đổi thành `{STATUS_CMD}`"
    data["statusLine"] = {"type": "command", "command": STATUS_CMD}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return "đã thêm statusLine vào .claude/settings.json (hiện từ phiên sau / khi Claude Code đọc lại settings)"


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else None
    if not start:
        try:
            start = json.load(sys.stdin).get("cwd")
        except ValueError:
            start = None
    root = find_root(start or os.getcwd())
    if not root:
        return
    plugin = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    msgs = []
    done = sync_scripts(plugin, root)
    if done:
        msgs.append("đã cập nhật .claude/agent-team/ theo plugin: " + ", ".join(done))
    old = stale_templates(plugin, root)
    if old:
        msgs.append("templates khác bản plugin (không tự ghi đè, có thể bạn đã sửa): " + ", ".join(old))
    m = ensure_status_line(root)
    if m:
        msgs.append(m)
    if msgs:
        print("[agent-team] " + " · ".join(msgs))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if os.environ.get("AGENT_TEAM_DEBUG") == "1":
            sys.stderr.write(f"[agent-team sync] {e!r}\n")
    sys.exit(0)
