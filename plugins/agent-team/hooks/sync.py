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

STATUS_CMD = 'python3 "$(git rev-parse --path-format=absolute --git-common-dir)/../.claude/agent-team/progress.py"'
OLD_STATUS_CMDS = ("python3 .claude/agent-team/progress.py",)
SCRIPTS = ("board.py", "progress.py", "pool.py", "gap-check.py", "owner-form.py", "kb-check.py", "agent-db-clone.sh")
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
        # chép đủ mọi script (không commit: clone mới của người trong team chưa có file nào)
        if os.path.isfile(t) and filecmp.cmp(s, t, shallow=False):
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


GENERATED = (".claude/agent-team/*.py", ".claude/agent-team/*.sh", ".claude/agent-team/__pycache__/")


def tracked_generated(root):
    """Script do plugin chép (sync tạo lại mỗi phiên) mà đang bị commit → team mỗi người 1 bản, commit qua lại."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", ".claude/agent-team"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    return [f for f in r.stdout.splitlines() if f.endswith((".py", ".sh", ".pyc")) and "/templates/" not in f]


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
    if cur and (cur.get("command") if isinstance(cur, dict) else "") in OLD_STATUS_CMDS:
        cur = None
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
    tracked = tracked_generated(root)
    if tracked:
        msgs.append(f"{len(tracked)} script plugin đang bị commit (team dùng chung sẽ ghi đè qua lại): thêm vào .gitignore "
                    + " ".join(GENERATED) + " .claude/agent-team.local.config rồi `git rm -r --cached .claude/agent-team/*.py "
                    ".claude/agent-team/*.sh .claude/agent-team/__pycache__` (Lead làm, commit 1 lần)")
    if msgs:
        print("[agent-team] " + " · ".join(msgs))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if os.environ.get("AGENT_TEAM_DEBUG") == "1":
            sys.stderr.write(f"[agent-team sync] {e!r}\n")
    sys.exit(0)
