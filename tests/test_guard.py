#!/usr/bin/env python3
"""Test guard.py: python3 tests/test_guard.py"""
import json
import os
import subprocess
import sys
import tempfile

GUARD = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "hooks", "guard.py")


def run(tool, tool_input, role=None, cwd=None, mode=None, session="s1"):
    data = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or os.getcwd(), "session_id": session}
    if role:
        data["agent_type"] = f"agent-team:{role}"
    args = [mode] if mode else []
    r = subprocess.run([sys.executable, GUARD, *args], input=json.dumps(data), capture_output=True, text=True)
    return r.returncode


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def make_repo():
    d = tempfile.mkdtemp()
    sh(d, "git", "init", "-q", "-b", "develop")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    open(os.path.join(d, "a.rb"), "w").write("x = 1\n")
    sh(d, "git", "add", ".")
    sh(d, "git", "commit", "-qm", "init")
    return d


repo = make_repo()
B, OK = 2, 0
cases = [
    # (mô tả, tool, input, role, cwd, kỳ vọng)
    ("đọc .env", "Read", {"file_path": "/p/.env"}, None, None, B),
    ("đọc .env.production", "Read", {"file_path": "/p/.env.production"}, None, None, B),
    ("đọc .env.example", "Read", {"file_path": "/p/.env.example"}, None, None, OK),
    ("đọc master.key", "Read", {"file_path": "/p/config/master.key"}, None, None, B),
    ("cat .env", "Bash", {"command": "cat .env"}, None, None, B),
    ("printenv", "Bash", {"command": "printenv"}, None, None, B),
    ("docker inspect", "Bash", {"command": "docker inspect db"}, None, None, B),
    ("migrate DB thật", "Bash", {"command": "docker compose exec app bin/rails db:migrate"}, "backend-dev", None, B),
    ("migrate DB thật trong sh -c", "Bash", {"command": "docker compose exec app sh -c \"bin/rails db:migrate\""}, "backend-dev", None, B),
    ("migrate qua clone", "Bash", {"command": ".claude/agent-team/agent-db-clone.sh migrate T1"}, "backend-dev", None, OK),
    ("grep db:migrate", "Bash", {"command": "grep -rn \"db:migrate\" ."}, "code-reviewer", None, OK),
    ("force push", "Bash", {"command": "git push -f origin agent/x"}, None, repo, B),
    ("push develop", "Bash", {"command": "git push origin develop"}, None, repo, B),
    ("push khi đang ở develop", "Bash", {"command": "git push"}, None, repo, B),
    ("commit trên develop", "Bash", {"command": "git commit -m x"}, "backend-dev", repo, B),
    ("reset --hard", "Bash", {"command": "git reset --hard HEAD~1"}, None, None, B),
    ("rm -rf .", "Bash", {"command": "rm -rf ."}, None, None, B),
    ("reviewer git diff", "Bash", {"command": "git diff develop...HEAD"}, "code-reviewer", None, OK),
    ("reviewer grep hash rocket", "Bash", {"command": "grep -rn \"=> \" app/ | head -20"}, "code-reviewer", None, OK),
    ("reviewer rspec trong docker", "Bash", {"command": "docker compose exec -T app bundle exec rspec spec/models"}, "test-reviewer", None, OK),
    ("reviewer rubocop -a", "Bash", {"command": "bundle exec rubocop -a"}, "code-reviewer", None, B),
    ("reviewer ghi file bằng >", "Bash", {"command": "echo x > app/a.rb"}, "code-reviewer", None, B),
    ("reviewer sed -i", "Bash", {"command": "sed -i 's/a/b/' app/a.rb"}, "security", None, B),
    ("reviewer git commit", "Bash", {"command": "git commit -m x"}, "solution-reviewer", None, B),
    ("reviewer Edit code", "Edit", {"file_path": "/p/app/a.rb"}, "code-reviewer", "/p", B),
    ("reviewer ghi ngoài board", "Write", {"file_path": "/p/docs/agent-tasks/T1/notes/code-reviewer.md"}, "code-reviewer", "/p", B),
    ("security brakeman", "Bash", {"command": "bundle exec brakeman -q"}, "security", None, OK),
    ("security npm audit fix", "Bash", {"command": "npm audit fix"}, "security", None, B),
    ("dev Edit code", "Edit", {"file_path": "/p/app/a.rb"}, "backend-dev", "/p", OK),
    ("dev rspec", "Bash", {"command": "bundle exec rspec"}, "backend-dev", None, OK),
]

fail = 0


def check(desc, tool, ti, role, cwd, exp):
    global fail
    got = run(tool, ti, role, cwd)
    fail += got != exp
    print(f"{'PASS' if got == exp else 'FAIL'}  {desc}  (expect {exp}, got {got})")


for c in cases:
    check(*c)
total = len(cases)
cases = []

# Branch agent: push có secret thì phải bị chặn
sh(repo, "git", "checkout", "-qb", "agent/t1")
open(os.path.join(repo, "b.rb"), "w").write('API_KEY = "AKIAABCDEFGHIJKLMNOP"\n')
sh(repo, "git", "add", ".")
sh(repo, "git", "commit", "-qm", "leak")
check("push có secret", "Bash", {"command": "git push -u origin agent/t1"}, None, repo, B)
total += 1
sh(repo, "git", "reset", "-q", "--hard", "HEAD~1")
open(os.path.join(repo, "c.rb"), "w").write('key = ENV.fetch("API_KEY")\n')
sh(repo, "git", "add", ".")
sh(repo, "git", "commit", "-qm", "ok")
cases.append(("push sạch từ agent/*", "Bash", {"command": "git push -u origin agent/t1"}, None, repo, OK))
cases.append(("commit trên agent/*", "Bash", {"command": "git commit -m x"}, "backend-dev", repo, OK))

# Debate board + .agent-team
proj = tempfile.mkdtemp()
board = os.path.join(proj, "docs/agent-tasks/T1/board")
os.makedirs(board)
open(os.path.join(board, "S2-R1-security-1.md"), "w").write("x")
os.makedirs(os.path.join(proj, ".agent-team/clones"))
open(os.path.join(proj, ".agent-team/clones/T1.state"), "w").write("x")
bp = "docs/agent-tasks/T1/board/"
sp = ".agent-team/clones/"
cases += [
    ("post bài của mình", "Write", {"file_path": bp + "S2-R1-security-2.md"}, "security", proj, OK),
    ("dev post bài của mình", "Write", {"file_path": bp + "S2-R2-backend-dev-1.md"}, "backend-dev", proj, OK),
    ("post bằng tên role khác", "Write", {"file_path": bp + "S2-R1-backend-dev-1.md"}, "security", proj, B),
    ("ghi đè bài đã post", "Write", {"file_path": bp + "S2-R1-security-1.md"}, "security", proj, B),
    ("sửa bài đã post", "Edit", {"file_path": bp + "S2-R1-security-1.md"}, "security", proj, B),
    ("role ghi SUMMARY.md", "Write", {"file_path": bp + "SUMMARY.md"}, "solution-architect", proj, B),
    ("role sửa TASK.md", "Edit", {"file_path": "docs/agent-tasks/T1/TASK.md"}, "backend-dev", proj, B),
    ("Lead ghi SUMMARY.md", "Write", {"file_path": bp + "SUMMARY.md"}, None, proj, OK),
    ("đọc board", "Read", {"file_path": bp + "S2-R1-security-1.md"}, "tester", proj, OK),
    ("ghi vào .agent-team", "Write", {"file_path": sp + "x.state"}, "security", proj, B),
    ("đọc state .agent-team", "Read", {"file_path": sp + "T1.state"}, "security", proj, B),
    ("grep .agent-team", "Grep", {"path": ".agent-team"}, "tester", proj, B),
    ("cat .agent-team bằng Bash", "Bash", {"command": "cat .agent-team/clones/*.state"}, "backend-dev", proj, B),
    ("Lead đọc .agent-team", "Read", {"file_path": sp + "T1.state"}, None, proj, OK),
    ("ghi board bằng Bash", "Bash", {"command": "echo hi > docs/agent-tasks/T1/board/S2-R1-backend-dev-9.md"}, "backend-dev", proj, B),
    ("ls board bằng Bash", "Bash", {"command": "ls -tr docs/agent-tasks/T1/board"}, "code-reviewer", proj, OK),
    ("dev chạy script clone", "Bash", {"command": ".claude/agent-team/agent-db-clone.sh verify T1"}, "backend-dev", proj, OK),
]

# Khóa vùng ghi theo config
zp = tempfile.mkdtemp()
os.makedirs(os.path.join(zp, ".claude"))
open(os.path.join(zp, ".claude/agent-team.config"), "w").write(
    'BE_PATHS="app lib config db/migrate"\nFE_PATHS="frontend"\nTEST_PATHS="spec test e2e"\n')
cases += [
    ("BE dev sửa app", "Edit", {"file_path": "app/a.rb"}, "backend-dev", zp, OK),
    ("BE dev sửa spec", "Edit", {"file_path": "spec/a_spec.rb"}, "backend-dev", zp, B),
    ("BE dev sửa frontend", "Write", {"file_path": "frontend/x.ts"}, "backend-dev", zp, B),
    ("FE dev sửa frontend", "Edit", {"file_path": "frontend/x.ts"}, "frontend-dev", zp, OK),
    ("FE dev sửa app", "Edit", {"file_path": "app/a.rb"}, "frontend-dev", zp, B),
    ("FE dev sửa file .test.ts", "Edit", {"file_path": "frontend/src/a.test.ts"}, "frontend-dev", zp, B),
    ("Tester sửa spec", "Write", {"file_path": "spec/a_spec.rb"}, "tester", zp, OK),
    ("Tester sửa .test.ts trong frontend", "Write", {"file_path": "frontend/src/a.test.ts"}, "tester", zp, OK),
    ("Tester sửa app", "Edit", {"file_path": "app/a.rb"}, "tester", zp, B),
    ("dev sửa release-notes", "Edit", {"file_path": "release-notes.md"}, "backend-dev", zp, OK),
    ("dev ghi spec bằng >", "Bash", {"command": "echo x > spec/a_spec.rb"}, "backend-dev", zp, B),
    ("Tester sed -i code", "Bash", {"command": "sed -i 's/a/b/' app/a.rb"}, "tester", zp, B),
    ("dev cat spec", "Bash", {"command": "cat spec/a_spec.rb"}, "backend-dev", zp, OK),
    ("dev chạy rspec", "Bash", {"command": "bundle exec rspec 2>&1 | tail -5"}, "backend-dev", zp, OK),
    ("Tester ghi /tmp", "Bash", {"command": "echo x > /tmp/o"}, "tester", zp, OK),
    ("Lead sửa spec", "Edit", {"file_path": "spec/a_spec.rb"}, None, zp, OK),
    ("requirement-reviewer sửa code", "Edit", {"file_path": "app/a.rb"}, "requirement-reviewer", zp, B),
    ("dev chmod mở khóa", "Bash", {"command": "chmod -R u+w spec"}, "backend-dev", zp, B),
    ("reviewer code-graph who-uses", "Bash", {"command": ".claude/agent-team/code-graph.py who-uses User"}, "code-reviewer", zp, OK),
    ("security code-graph uses", "Bash", {"command": ".claude/agent-team/code-graph.py uses app/a.rb"}, "security", zp, OK),
    ("reviewer code-graph build", "Bash", {"command": ".claude/agent-team/code-graph.py build"}, "code-reviewer", zp, B),
    ("dev python3 code-graph build", "Bash", {"command": "python3 .claude/agent-team/code-graph.py build"}, "backend-dev", zp, B),
    ("dev code-graph explain", "Bash", {"command": ".claude/agent-team/code-graph.py explain User"}, "backend-dev", zp, OK),
    ("Lead code-graph build", "Bash", {"command": ".claude/agent-team/code-graph.py build"}, None, zp, OK),
    ("dev sửa spec khi chưa có config", "Edit", {"file_path": "spec/a_spec.rb"}, "backend-dev", tempfile.mkdtemp(), OK),
]

for c in cases:
    check(*c)
total += len(cases)
# PostToolUse: ghi ngoài vùng bằng Bash (lách mẫu lệnh) phải bị hoàn tác theo diff
pr = make_repo()
os.makedirs(os.path.join(pr, ".claude"))
open(os.path.join(pr, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nTEST_PATHS="spec"\n')
os.makedirs(os.path.join(pr, "app"))
os.makedirs(os.path.join(pr, "spec"))
open(os.path.join(pr, "app/a.rb"), "w").write("a = 1\n")
open(os.path.join(pr, "spec/a_spec.rb"), "w").write("s = 1\n")
sh(pr, "git", "add", "app", "spec")
sh(pr, "git", "commit", "-qm", "base")


def post_case(desc, role, mutate, exp_code, expect):
    global fail, total
    run("Bash", {"command": "bundle exec rspec"}, role, pr, session=desc)
    mutate()
    got = run("Bash", {"command": "bundle exec rspec"}, role, pr, mode="post", session=desc)
    ok = got == exp_code and expect()
    fail += not ok
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {desc}  (expect {exp_code}, got {got})")


def w(rel, text):
    open(os.path.join(pr, rel), "w").write(text)


def r(rel):
    return open(os.path.join(pr, rel)).read() if os.path.exists(os.path.join(pr, rel)) else None


post_case("post: dev sửa spec đã track bị hoàn tác", "backend-dev", lambda: w("spec/a_spec.rb", "HACK\n"), B,
          lambda: r("spec/a_spec.rb") == "s = 1\n")
post_case("post: dev tạo spec mới bị xoá", "backend-dev", lambda: w("spec/new_spec.rb", "x\n"), B,
          lambda: r("spec/new_spec.rb") is None)
post_case("post: dev sửa app thì giữ", "backend-dev", lambda: w("app/a.rb", "a = 2\n"), OK,
          lambda: r("app/a.rb") == "a = 2\n")
post_case("post: dev sửa tiếp spec đã dirty sẵn của tester", "tester", lambda: w("spec/a_spec.rb", "T1\n"), OK,
          lambda: r("spec/a_spec.rb") == "T1\n")
post_case("post: dev ghi đè spec đang dirty, trả về bản của tester", "backend-dev", lambda: w("spec/a_spec.rb", "HACK2\n"), B,
          lambda: r("spec/a_spec.rb") == "T1\n")
post_case("post: tester sửa app bị hoàn tác", "tester", lambda: w("app/a.rb", "TESTER\n"), B,
          lambda: r("app/a.rb") == "a = 1\n" or r("app/a.rb") == "a = 2\n")
post_case("post: reviewer ghi file ngoài board bị xoá", "code-reviewer", lambda: w("notes.txt", "x\n"), B,
          lambda: r("notes.txt") is None)
post_case("post: Lead không bị theo dõi", None, lambda: w("spec/lead_spec.rb", "x\n"), OK,
          lambda: r("spec/lead_spec.rb") == "x\n")

# Chặn theo giai đoạn (không cần role)
sp2 = tempfile.mkdtemp()
os.makedirs(os.path.join(sp2, ".claude"))
os.makedirs(os.path.join(sp2, ".agent-team"))
open(os.path.join(sp2, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nFE_PATHS="frontend"\nTEST_PATHS="spec"\n')


def at_stage(stage, desc, tool, ti, role, exp):
    global fail, total
    sf = os.path.join(sp2, ".agent-team/stage")
    if stage:
        open(sf, "w").write(stage + "\n")
    elif os.path.exists(sf):
        os.remove(sf)
    got = run(tool, ti, role, sp2)
    fail += got != exp
    total += 1
    print(f"{'PASS' if got == exp else 'FAIL'}  [{stage or '-'}] {desc}  (expect {exp}, got {got})")


at_stage("S3", "dev sửa app", "Edit", {"file_path": "app/a.rb"}, "backend-dev", OK)
at_stage("S3", "tester sửa spec bị chặn", "Edit", {"file_path": "spec/a_spec.rb"}, "tester", B)
at_stage("S3", "dev sửa spec bị chặn", "Write", {"file_path": "spec/a_spec.rb"}, "backend-dev", B)
at_stage("S3", "agent không rõ role sửa spec bị chặn", "Write", {"file_path": "spec/a_spec.rb"}, None, B)
at_stage("S3", "Bash ghi spec bằng >, không rõ role", "Bash", {"command": "echo x > spec/a_spec.rb"}, None, B)
at_stage("S3", "Bash python ghi spec: vẫn qua Pre (Post sẽ hoàn tác)", "Bash", {"command": "python3 w.py"}, None, OK)
at_stage("S3", "sửa release-notes", "Edit", {"file_path": "release-notes.md"}, None, OK)
at_stage("S4", "tester sửa spec", "Write", {"file_path": "spec/a_spec.rb"}, "tester", OK)
at_stage("S4", "dev sửa app bị chặn", "Edit", {"file_path": "app/a.rb"}, "backend-dev", B)
at_stage("S4", "không rõ role sửa app bị chặn", "Edit", {"file_path": "app/a.rb"}, None, B)
at_stage("S1", "dev sửa app khi debate bị chặn", "Edit", {"file_path": "app/a.rb"}, "backend-dev", B)
at_stage("S1", "post board vẫn được", "Write", {"file_path": "docs/agent-tasks/T1/board/S1-R1-backend-dev-1.md"}, "backend-dev", OK)
at_stage("S5", "S5 không giới hạn theo giai đoạn", "Edit", {"file_path": "app/a.rb"}, "backend-dev", OK)
at_stage(None, "không có file stage", "Edit", {"file_path": "spec/a_spec.rb"}, None, OK)

# Post + stage: ghi sai vùng khi không biết role vẫn bị hoàn tác
os.makedirs(os.path.join(pr, ".agent-team"), exist_ok=True)
open(os.path.join(pr, ".agent-team/stage"), "w").write("S4\n")
post_case("post+stage S4: ghi app khi không rõ role bị hoàn tác", None, lambda: w("app/a.rb", "SNEAK\n"), B,
          lambda: r("app/a.rb") == "a = 2\n" or r("app/a.rb") == "a = 1\n")
post_case("post+stage S4: ghi spec khi không rõ role được giữ", None, lambda: w("spec/b_spec.rb", "ok\n"), OK,
          lambda: r("spec/b_spec.rb") == "ok\n")

# ---- Nhiều repo con (REPOS) + knowledge base docs/domain ----
mr = tempfile.mkdtemp()
for name in ("be", "fe"):
    d = os.path.join(mr, name)
    os.makedirs(os.path.join(d, "app" if name == "be" else "src"))
    sh(d, "git", "init", "-q", "-b", "develop")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    open(os.path.join(d, "app/a.rb" if name == "be" else "src/a.ts"), "w").write("x\n")
    sh(d, "git", "add", ".")
    sh(d, "git", "commit", "-qm", "init")
os.makedirs(os.path.join(mr, ".claude"))
os.makedirs(os.path.join(mr, "docs/domain"))
open(os.path.join(mr, ".claude/agent-team.config"), "w").write(
    'REPOS="be fe"\nBE_PATHS="be"\nFE_PATHS="fe"\nTEST_PATHS="be/spec fe/e2e"\n')
mcases = [
    ("multi: BE dev sửa be/app", "Edit", {"file_path": "be/app/a.rb"}, "backend-dev", mr, OK),
    ("multi: BE dev sửa fe/", "Edit", {"file_path": "fe/src/a.ts"}, "backend-dev", mr, B),
    ("multi: FE dev sửa be/", "Edit", {"file_path": "be/app/a.rb"}, "frontend-dev", mr, B),
    ("multi: Tester sửa be/spec", "Write", {"file_path": "be/spec/a_spec.rb"}, "tester", mr, OK),
    ("multi: dev sửa be/spec", "Write", {"file_path": "be/spec/a_spec.rb"}, "backend-dev", mr, B),
    ("multi: git -C be commit trên develop", "Bash", {"command": "git -C be commit -m x"}, "backend-dev", mr, B),
    ("multi: cd fe && git push origin develop", "Bash", {"command": "cd fe && git push origin develop"}, "frontend-dev", mr, B),
    ("multi: git -c k=v -C be push (đang ở develop)", "Bash", {"command": "git -c a.b=c -C be push"}, None, mr, B),
    ("multi: git -C be status", "Bash", {"command": "git -C be status"}, "code-reviewer", mr, OK),
    ("domain: BA ghi", "Write", {"file_path": "docs/domain/glossary.md"}, "business-analyst", mr, OK),
    ("domain: BA Edit", "Edit", {"file_path": "docs/domain/glossary.md"}, "business-analyst", mr, OK),
    ("domain: dev ghi bị chặn", "Write", {"file_path": "docs/domain/glossary.md"}, "backend-dev", mr, B),
    ("domain: tester ghi bị chặn", "Write", {"file_path": "docs/domain/rules.md"}, "tester", mr, B),
    ("domain: reviewer ghi bị chặn", "Write", {"file_path": "docs/domain/rules.md"}, "requirement-reviewer", mr, B),
    ("domain: security ghi bị chặn", "Write", {"file_path": "docs/domain/rules.md"}, "security", mr, B),
    ("domain: dev ghi bằng Bash bị chặn", "Bash", {"command": "echo x > docs/domain/glossary.md"}, "backend-dev", mr, B),
    ("domain: Lead ghi", "Write", {"file_path": "docs/domain/glossary.md"}, None, mr, OK),
    ("domain: dev đọc", "Read", {"file_path": "docs/domain/glossary.md"}, "backend-dev", mr, OK),
]
for c in mcases:
    check(*c)
total += len(mcases)


def multi_post(desc, role, rel, text, exp_code, expect):
    global fail, total
    run("Bash", {"command": "bundle exec rspec"}, role, mr, session=desc)
    open(os.path.join(mr, rel), "w").write(text)
    got = run("Bash", {"command": "bundle exec rspec"}, role, mr, mode="post", session=desc)
    ok = got == exp_code and expect()
    fail += not ok
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {desc}  (expect {exp_code}, got {got})")


rd = lambda rel: open(os.path.join(mr, rel)).read()
multi_post("multi post: BE dev ghi fe/ bị hoàn tác", "backend-dev", "fe/src/a.ts", "HACK\n", B, lambda: rd("fe/src/a.ts") == "x\n")
multi_post("multi post: BE dev sửa be/app thì giữ", "backend-dev", "be/app/a.rb", "y\n", OK, lambda: rd("be/app/a.rb") == "y\n")
multi_post("multi post: FE dev ghi be/app bị hoàn tác", "frontend-dev", "be/app/a.rb", "HACK\n", B, lambda: rd("be/app/a.rb") == "y\n")
multi_post("multi post: reviewer ghi be/ bị hoàn tác", "code-reviewer", "be/app/new.rb", "x\n", B, lambda: not os.path.exists(os.path.join(mr, "be/app/new.rb")))

# ---- Repo chính (API) + repo anh em (../FrontEnd), docs/.claude nằm trong repo chính ----
sib = os.path.realpath(tempfile.mkdtemp())
for name, f in (("API", "app/a.rb"), ("FrontEnd", "src/a.ts")):
    d = os.path.join(sib, name)
    os.makedirs(os.path.dirname(os.path.join(d, f)))
    sh(d, "git", "init", "-q", "-b", "develop")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    open(os.path.join(d, f), "w").write("x\n")
    sh(d, "git", "add", ".")
    sh(d, "git", "commit", "-qm", "init")
api = os.path.join(sib, "API")
os.makedirs(os.path.join(api, ".claude"))
open(os.path.join(api, ".claude/agent-team.config"), "w").write(
    'REPOS=". ../FrontEnd"\nBE_PATHS="app"\nFE_PATHS="../FrontEnd"\nTEST_PATHS="spec ../FrontEnd/e2e"\n')
scases = [
    ("sibling: FE dev sửa ../FrontEnd", "Edit", {"file_path": "../FrontEnd/src/a.ts"}, "frontend-dev", api, OK),
    ("sibling: BE dev sửa ../FrontEnd bị chặn", "Edit", {"file_path": "../FrontEnd/src/a.ts"}, "backend-dev", api, B),
    ("sibling: FE dev sửa app của API bị chặn", "Edit", {"file_path": "app/a.rb"}, "frontend-dev", api, B),
    ("sibling: FE dev sửa .test.ts ở FrontEnd bị chặn", "Edit", {"file_path": "../FrontEnd/src/a.test.ts"}, "frontend-dev", api, B),
    ("sibling: tester sửa .test.ts ở FrontEnd", "Write", {"file_path": "../FrontEnd/src/a.test.ts"}, "tester", api, OK),
    ("sibling: dev sửa file _test ngoài mọi repo thì không chặn", "Write", {"file_path": "/tmp/x_test.py"}, "backend-dev", api, OK),
    ("sibling: reviewer sửa ../FrontEnd bị chặn", "Write", {"file_path": "../FrontEnd/src/a.ts"}, "code-reviewer", api, B),
    ("sibling: git -C ../FrontEnd push develop", "Bash", {"command": "git -C ../FrontEnd push origin develop"}, "frontend-dev", api, B),
    ("sibling: git -C ../FrontEnd status", "Bash", {"command": "git -C ../FrontEnd status"}, "code-reviewer", api, OK),
    ("sibling: BA ghi docs/domain trong repo chính", "Write", {"file_path": "docs/domain/glossary.md"}, "business-analyst", api, OK),
    ("sibling: dev ghi docs/domain bị chặn", "Write", {"file_path": "docs/domain/glossary.md"}, "backend-dev", api, B),
]
for c in scases:
    check(*c)
total += len(scases)


def sib_post(desc, role, path, text, exp_code, expect):
    global fail, total
    run("Bash", {"command": "bundle exec rspec"}, role, api, session=desc)
    open(path, "w").write(text)
    got = run("Bash", {"command": "bundle exec rspec"}, role, api, mode="post", session=desc)
    ok = got == exp_code and expect()
    fail += not ok
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {desc}  (expect {exp_code}, got {got})")


fe_file = os.path.join(sib, "FrontEnd/src/a.ts")
sib_post("sibling post: BE dev ghi FrontEnd bị hoàn tác", "backend-dev", fe_file, "HACK\n", B, lambda: open(fe_file).read() == "x\n")
sib_post("sibling post: FE dev ghi FrontEnd thì giữ", "frontend-dev", fe_file, "y\n", OK, lambda: open(fe_file).read() == "y\n")

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
