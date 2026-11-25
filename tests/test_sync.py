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
check("chép đủ mọi script (clone mới của người trong team chưa có)", os.path.exists(os.path.join(d, ".claude", "agent-team", "gap-check.py"))
      and os.path.exists(os.path.join(d, ".claude", "agent-team", "agent-db.sh")) and os.path.exists(os.path.join(d, ".claude", "agent-team", "agent-db-clone.sh")))
check("chép xong có quyền chạy", os.access(os.path.join(d, ".claude", "agent-team", "board.py"), os.X_OK))
tpl = os.path.join(d, ".claude", "agent-team", "e2e-template")
check("chép khung E2E chuẩn vào .claude/agent-team/e2e-template/",
      all(os.path.isfile(os.path.join(tpl, f)) for f in ("playwright.config.ts", "e2e/project.ts", "e2e/auth.setup.ts", "e2e/smoke.spec.ts", "e2e/support/db.ts")))
open(os.path.join(tpl, "e2e", "smoke.spec.ts"), "w").write("cũ\n")
_, out2 = run(os.path.join(d, "app"))
check("khung E2E khác plugin → chép lại", "e2e-template/" in out2 and open(os.path.join(tpl, "e2e", "smoke.spec.ts")).read() != "cũ\n")
_, out2 = run(os.path.join(d, "app"))
check("khung E2E đã khớp → không chép lại", "e2e-template/" not in out2)
tsrc = lambda f: open(os.path.join(PLUGIN, "templates", "e2e", f), encoding="utf-8").read()
check("khung E2E: reset qua $APP_EXEC, không ghi cứng container", "APP_EXEC" in tsrc("e2e/support/db.ts")
      and "agent-e2e-" not in "".join(tsrc(f) for f in ("e2e/support/db.ts", "e2e/auth.setup.ts", "e2e/smoke.spec.ts")))
check("khung E2E: workers theo chiều rộng, @responsive, ảnh vào EVIDENCE_DIR", "workers: widths.length" in tsrc("playwright.config.ts")
      and "@responsive" in tsrc("playwright.config.ts") and "EVIDENCE_DIR" in tsrc("e2e/support/responsive.ts"))
check("template đã sửa: chỉ báo, không ghi đè", "POST.md" in out and dst("templates/POST.md") == "tôi đã sửa\n")
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("chưa có settings.json → tạo với statusLine (chạy progress.py của thư mục chính, kể cả khi đứng trong worktree)", "git-common-dir" in st["statusLine"]["command"])
check("in 1 dòng báo Lead", out.startswith("[agent-team]") and "board.py" in out)

code, out = run(d)
check("lần 2 không đổi gì: chỉ còn báo template", "board.py" not in out and "statusLine" not in out)

json.dump({"permissions": {"allow": ["Bash(ls)"]}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
run(d)
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("settings.json có key khác: thêm statusLine, giữ key cũ", st["permissions"]["allow"] == ["Bash(ls)"] and "statusLine" in st)
json.dump({"permissions": {"allow": ["Bash(.claude/agent-team/agent-db-clone.sh:*)"]}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
run(d), run(d)
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("quyền tên cũ agent-db-clone.sh → thêm quyền agent-db.sh 1 lần, giữ quyền cũ",
      st["permissions"]["allow"] == ["Bash(.claude/agent-team/agent-db-clone.sh:*)", "Bash(.claude/agent-team/agent-db.sh:*)"])

json.dump({"statusLine": {"type": "command", "command": "my-line.sh"}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
code, out = run(d)
st = json.load(open(os.path.join(d, ".claude", "settings.json")))
check("statusLine lệnh khác: không ghi đè, có báo", st["statusLine"]["command"] == "my-line.sh" and "không ghi đè" in out)

open(os.path.join(d, ".claude", "settings.json"), "w").write("{hỏng")
code, out = run(d)
check("settings.json lỗi JSON: không sửa, exit 0", code == 0 and open(os.path.join(d, ".claude", "settings.json")).read() == "{hỏng")

code, _ = subprocess.run([sys.executable, SYNC], input="không phải json", capture_output=True, text=True, cwd=d).returncode, None
check("stdin không phải JSON: vẫn exit 0", code == 0)

# ---- v0.28.0: script plugin đang bị commit → cảnh báo ----
g = tempfile.mkdtemp()
subprocess.run(["git", "init", "-q"], cwd=g)
os.makedirs(os.path.join(g, ".claude", "agent-team", "templates"))
open(os.path.join(g, ".claude", "agent-team.config"), "w").write("X=1\n")
json.dump({"statusLine": {"type": "command", "command": "python3 .claude/agent-team/progress.py"}}, open(os.path.join(g, ".claude", "settings.json"), "w"))
open(os.path.join(g, ".claude", "agent-team", "board.py"), "w").write("x\n")
open(os.path.join(g, ".claude", "agent-team", "templates", "POST.md"), "w").write("x\n")
subprocess.run(["git", "add", "-f", "."], cwd=g)
code, out = run(g)
check("script plugin đang commit → báo cách gỡ khỏi git (template không tính)", "script plugin đang bị commit" in out and "git rm -r --cached" in out)
subprocess.run(["git", "rm", "-q", "-r", "-f", "--cached", ".claude/agent-team/board.py"], cwd=g)
check("gỡ khỏi git rồi thì không báo nữa", "đang bị commit" not in run(g)[1])

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
