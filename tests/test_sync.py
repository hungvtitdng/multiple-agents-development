#!/usr/bin/env python3
"""Test hooks/sync.py: python3 tests/test_sync.py"""
import json
import os
import subprocess
import sys
import tempfile

PLUGIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team")
SYNC = os.path.join(PLUGIN, "hooks", "sync.py")
fail = total = 0


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


def run(cwd, stdin=True):
    r = subprocess.run([sys.executable, SYNC], input=json.dumps({"cwd": cwd}) if stdin else "", capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


d = tempfile.mkdtemp()
check("không phải project agent-team: không làm gì", run(d) == (0, "") and not os.path.exists(os.path.join(d, ".claude")))

os.makedirs(os.path.join(d, ".claude", "agent-team", "templates"))
open(os.path.join(d, ".claude", "agent-team.config"), "w").write("X=1\n")
open(os.path.join(d, ".claude", "agent-team", "board.py"), "w").write("# cũ\n")
open(os.path.join(d, ".claude", "agent-team", "templates", "POST.md"), "w").write("tôi đã sửa\n")
code, out = run(os.path.join(d, "app"))
src = lambda f: open(os.path.join(PLUGIN, "scripts", f), encoding="utf-8").read()
dst = lambda f: open(os.path.join(d, ".claude", "agent-team", f), encoding="utf-8").read()
check("board.py cũ → chép bản plugin", code == 0 and dst("board.py") == src("board.py"))
check("progress.py chưa có → chép", dst("progress.py") == src("progress.py"))
check("script project chưa dùng (gap-check) → không chép", not os.path.exists(os.path.join(d, ".claude", "agent-team", "gap-check.py")))
check("chép xong có quyền chạy", os.access(os.path.join(d, ".claude", "agent-team", "board.py"), os.X_OK))
check("template đã sửa: chỉ báo, không ghi đè", "POST.md" in out and dst("templates/POST.md") == "tôi đã sửa\n")
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("chưa có settings.json → tạo với statusLine", st["statusLine"]["command"] == "python3 .claude/agent-team/progress.py")
check("in 1 dòng báo Lead", out.startswith("[agent-team]") and "board.py" in out)

code, out = run(d)
check("lần 2 không đổi gì: chỉ còn báo template", "board.py" not in out and "statusLine" not in out)

json.dump({"permissions": {"allow": ["Bash(ls)"]}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
run(d)
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("settings.json có key khác: thêm statusLine, giữ key cũ", st["permissions"]["allow"] == ["Bash(ls)"] and "statusLine" in st)

json.dump({"statusLine": {"type": "command", "command": "my-line.sh"}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
code, out = run(d)
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("statusLine lệnh khác: không ghi đè, có báo", st["statusLine"]["command"] == "my-line.sh" and "không ghi đè" in out)

open(os.path.join(d, ".claude", "settings.json"), "w").write("{hỏng")
code, out = run(d)
check("settings.json lỗi JSON: không sửa, exit 0", code == 0 and open(os.path.join(d, ".claude", "settings.json")).read() == "{hỏng")

code, _ = subprocess.run([sys.executable, SYNC], input="không phải json", capture_output=True, text=True, cwd=d).returncode, None
check("stdin không phải JSON: vẫn exit 0", code == 0)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
