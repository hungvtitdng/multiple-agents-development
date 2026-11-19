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
    ("reviewer rspec trong docker", "Bash", {"command": "docker compose exec -T app bundle exec rspec spec/models"}, "test-designer", None, OK),
    ("reviewer rubocop -a", "Bash", {"command": "bundle exec rubocop -a"}, "code-reviewer", None, B),
    ("reviewer ghi file bằng >", "Bash", {"command": "echo x > app/a.rb"}, "code-reviewer", None, B),
    ("reviewer sed -i", "Bash", {"command": "sed -i 's/a/b/' app/a.rb"}, "security", None, B),
    ("reviewer git commit", "Bash", {"command": "git commit -m x"}, "scout", None, B),
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
os.makedirs(os.path.join(proj, ".claude"))
open(os.path.join(proj, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nFE_PATHS="frontend"\nTEST_PATHS="spec"\n')
bp = "docs/agent-tasks/T1/board/"
sp = ".agent-team/clones/"
cases += [
    # v0.3: agent trả kết quả cho Lead, chỉ Lead ghi board/TASK; Scout ghi CONTEXT.md
    ("security ghi board bị chặn", "Write", {"file_path": bp + "S2-R1-security-2.md"}, "security", proj, B),
    ("dev ghi board bị chặn", "Write", {"file_path": bp + "S2-R2-backend-dev-1.md"}, "backend-dev", proj, B),
    ("role sửa bài trên board", "Edit", {"file_path": bp + "S2-R1-security-1.md"}, "security", proj, B),
    ("role ghi SUMMARY.md", "Write", {"file_path": bp + "SUMMARY.md"}, "solution-architect", proj, B),
    ("role sửa TASK.md", "Edit", {"file_path": "docs/agent-tasks/T1/TASK.md"}, "backend-dev", proj, B),
    ("Lead ghi SUMMARY.md", "Write", {"file_path": bp + "SUMMARY.md"}, None, proj, OK),
    ("Lead ghi bài trên board", "Write", {"file_path": bp + "S2-R1-security-3.md"}, None, proj, OK),
    ("scout ghi CONTEXT.md", "Write", {"file_path": "docs/agent-tasks/T1/CONTEXT.md"}, "scout", proj, OK),
    ("scout ghi TASK.md bị chặn", "Write", {"file_path": "docs/agent-tasks/T1/TASK.md"}, "scout", proj, B),
    ("đọc board", "Read", {"file_path": bp + "S2-R1-security-1.md"}, "test-executor", proj, OK),
    ("ghi vào .agent-team", "Write", {"file_path": sp + "x.state"}, "security", proj, B),
    ("đọc state .agent-team", "Read", {"file_path": sp + "T1.state"}, "security", proj, B),
    ("grep .agent-team", "Grep", {"path": ".agent-team"}, "test-executor", proj, B),
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
    ("Tester sửa spec", "Write", {"file_path": "spec/a_spec.rb"}, "test-executor", zp, OK),
    ("Tester sửa .test.ts trong frontend", "Write", {"file_path": "frontend/src/a.test.ts"}, "test-executor", zp, OK),
    ("Tester sửa app", "Edit", {"file_path": "app/a.rb"}, "test-executor", zp, B),
    ("dev sửa release-notes", "Edit", {"file_path": "release-notes.md"}, "backend-dev", zp, OK),
    ("dev ghi spec bằng >", "Bash", {"command": "echo x > spec/a_spec.rb"}, "backend-dev", zp, B),
    ("Tester sed -i code", "Bash", {"command": "sed -i 's/a/b/' app/a.rb"}, "test-executor", zp, B),
    ("dev cat spec", "Bash", {"command": "cat spec/a_spec.rb"}, "backend-dev", zp, OK),
    ("dev chạy rspec", "Bash", {"command": "bundle exec rspec 2>&1 | tail -5"}, "backend-dev", zp, OK),
    ("Tester ghi /tmp", "Bash", {"command": "echo x > /tmp/o"}, "test-executor", zp, OK),
    ("Lead sửa spec", "Edit", {"file_path": "spec/a_spec.rb"}, None, zp, OK),
    ("requirement-reviewer sửa code", "Edit", {"file_path": "app/a.rb"}, "test-designer", zp, B),
    ("dev chmod mở khóa", "Bash", {"command": "chmod -R u+w spec"}, "backend-dev", zp, B),
    ("reviewer graphify explain", "Bash", {"command": 'graphify explain "User"'}, "code-reviewer", zp, OK),
    ("security graphify affected + --graph", "Bash", {"command": 'graphify affected "User" --graph graphify-out/merged-graph.json'}, "security", zp, OK),
    ("scout graphify query", "Bash", {"command": 'graphify query "ai tạo đơn hàng" | head -40'}, "scout", zp, OK),
    ("reviewer graphify update bị chặn", "Bash", {"command": "graphify update ."}, "code-reviewer", zp, B),
    ("dev graphify merge-graphs bị chặn", "Bash", {"command": "graphify merge-graphs a.json b.json"}, "backend-dev", zp, B),
    ("dev graphify explain", "Bash", {"command": 'graphify explain "User"'}, "backend-dev", zp, OK),
    ("Lead graphify update", "Bash", {"command": "graphify update . && graphify update ../fe"}, None, zp, OK),
    ("Lead graphify merge-graphs", "Bash", {"command": "graphify merge-graphs graphify-out/graph.json ../fe/graphify-out/graph.json --out graphify-out/merged-graph.json"}, None, zp, OK),
    ("Lead graphify extract (gọi LLM) bị chặn", "Bash", {"command": "graphify extract ."}, None, zp, B),
    ("Lead graphify hook install bị chặn", "Bash", {"command": "graphify hook install"}, None, zp, B),
    ("Lead graphify install bị chặn", "Bash", {"command": "graphify install"}, None, zp, B),
    ("Lead uvx graphifyy extract bị chặn", "Bash", {"command": "uvx graphifyy extract ."}, None, zp, B),
    ("graphify-mcp bị chặn", "Bash", {"command": "graphify-mcp"}, None, zp, B),
    ("scout chạy kb-check", "Bash", {"command": ".claude/agent-team/kb-check.py"}, "scout", zp, OK),
    ("scout python3 kb-check --json", "Bash", {"command": "python3 .claude/agent-team/kb-check.py --json"}, "scout", zp, B),
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
post_case("post: dev sửa tiếp spec đã dirty sẵn của tester", "test-executor", lambda: w("spec/a_spec.rb", "T1\n"), OK,
          lambda: r("spec/a_spec.rb") == "T1\n")
post_case("post: dev ghi đè spec đang dirty, trả về bản của tester", "backend-dev", lambda: w("spec/a_spec.rb", "HACK2\n"), B,
          lambda: r("spec/a_spec.rb") == "T1\n")
post_case("post: tester sửa app bị hoàn tác", "test-executor", lambda: w("app/a.rb", "TESTER\n"), B,
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
at_stage("S3", "tester sửa spec bị chặn", "Edit", {"file_path": "spec/a_spec.rb"}, "test-executor", B)
at_stage("S3", "dev sửa spec bị chặn", "Write", {"file_path": "spec/a_spec.rb"}, "backend-dev", B)
at_stage("S3", "agent không rõ role sửa spec bị chặn", "Write", {"file_path": "spec/a_spec.rb"}, None, B)
at_stage("S3", "Bash ghi spec bằng >, không rõ role", "Bash", {"command": "echo x > spec/a_spec.rb"}, None, B)
at_stage("S3", "Bash python ghi spec: vẫn qua Pre (Post sẽ hoàn tác)", "Bash", {"command": "python3 w.py"}, None, OK)
at_stage("S3", "sửa release-notes", "Edit", {"file_path": "release-notes.md"}, None, OK)
at_stage("S4", "tester sửa spec", "Write", {"file_path": "spec/a_spec.rb"}, "test-executor", OK)
at_stage("S4", "dev sửa app bị chặn", "Edit", {"file_path": "app/a.rb"}, "backend-dev", B)
at_stage("S4", "không rõ role sửa app bị chặn", "Edit", {"file_path": "app/a.rb"}, None, B)
at_stage("S1", "dev sửa app khi debate bị chặn", "Edit", {"file_path": "app/a.rb"}, "backend-dev", B)
at_stage("S1", "BA ghi KB vẫn được", "Write", {"file_path": "docs/business-rules.md"}, "business-analyst", OK)
at_stage("S1", "dev ghi board bị chặn", "Write", {"file_path": "docs/agent-tasks/T1/board/S1-R1-backend-dev-1.md"}, "backend-dev", B)
at_stage("S3", "scout không ghi KB khi đang có task", "Write", {"file_path": "docs/architecture.md"}, "scout", B)
at_stage(None, "scout dựng nháp KB khi init (chưa có stage)", "Write", {"file_path": "docs/architecture.md"}, "scout", OK)
at_stage(None, "scout không ghi code khi init", "Write", {"file_path": "app/a.rb"}, "scout", B)
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
    ("multi: Tester sửa be/spec", "Write", {"file_path": "be/spec/a_spec.rb"}, "test-executor", mr, OK),
    ("multi: dev sửa be/spec", "Write", {"file_path": "be/spec/a_spec.rb"}, "backend-dev", mr, B),
    ("multi: git -C be commit trên develop", "Bash", {"command": "git -C be commit -m x"}, "backend-dev", mr, B),
    ("multi: cd fe && git push origin develop", "Bash", {"command": "cd fe && git push origin develop"}, "frontend-dev", mr, B),
    ("multi: git -c k=v -C be push (đang ở develop)", "Bash", {"command": "git -c a.b=c -C be push"}, None, mr, B),
    ("multi: git -C be status", "Bash", {"command": "git -C be status"}, "code-reviewer", mr, OK),
    ("domain: BA ghi", "Write", {"file_path": "docs/domain/glossary.md"}, "business-analyst", mr, OK),
    ("domain: BA Edit", "Edit", {"file_path": "docs/domain/glossary.md"}, "business-analyst", mr, OK),
    ("domain: dev ghi bị chặn", "Write", {"file_path": "docs/domain/glossary.md"}, "backend-dev", mr, B),
    ("domain: tester ghi bị chặn", "Write", {"file_path": "docs/domain/rules.md"}, "test-executor", mr, B),
    ("domain: reviewer ghi bị chặn", "Write", {"file_path": "docs/domain/rules.md"}, "test-designer", mr, B),
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
    ("sibling: tester sửa .test.ts ở FrontEnd", "Write", {"file_path": "../FrontEnd/src/a.test.ts"}, "test-executor", api, OK),
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

# ---- v0.3: sở hữu knowledge base theo thư mục ----
kb = [
    ("kb: BA ghi business-rules", "docs/business-rules.md", "business-analyst", OK),
    ("kb: BA ghi architecture bị chặn", "docs/architecture.md", "business-analyst", B),
    ("kb: Architect ghi architecture/", "docs/architecture/overview.md", "solution-architect", OK),
    ("kb: Architect ghi engineering/", "docs/engineering/coding-standards.md", "solution-architect", OK),
    ("kb: TA ghi api/", "docs/api/endpoints.md", "technical-architect", OK),
    ("kb: BE dev ghi api/", "docs/api/endpoints.md", "backend-dev", OK),
    ("kb: BE dev ghi database/", "docs/database/schema.md", "backend-dev", OK),
    ("kb: BE dev ghi engineering bị chặn", "docs/engineering/x.md", "backend-dev", B),
    ("kb: FE dev ghi modules/", "docs/modules/trip/README.md", "frontend-dev", OK),
    ("kb: FE dev ghi api bị chặn", "docs/api/x.md", "frontend-dev", B),
    ("kb: Test Design ghi testing/", "docs/testing/coverage-matrix.md", "test-designer", OK),
    ("kb: Test Execution ghi testing/", "docs/testing/test-report.md", "test-executor", OK),
    ("kb: Test Execution ghi security bị chặn", "docs/security/findings.md", "test-executor", B),
    ("kb: Security ghi security/", "docs/security/findings.md", "security", OK),
    ("kb: Security ghi testing bị chặn", "docs/testing/x.md", "security", B),
    ("kb: Code Reviewer ghi docs bị chặn", "docs/modules/trip/README.md", "code-reviewer", B),
    ("kb: Lead ghi design.md", "docs/design.md", None, OK),
    ("kb: BA ghi file chưa phân chủ bị chặn", "docs/design.md", "business-analyst", B),
    ("kb: dev ghi docs/README.md bị chặn", "docs/README.md", "backend-dev", B),
    ("kb: BA ghi docs/domain cũ", "docs/domain/glossary.md", "business-analyst", OK),
]
for desc, p, role, exp in kb:
    check(desc, "Write", {"file_path": p}, role, mr, exp)
total += len(kb)

# ---- v0.3: commit một dòng, không trailer (chỉ khi project có agent-team.config) ----
cr = make_repo()
sh(cr, "git", "checkout", "-qb", "agent/c1")
os.makedirs(os.path.join(cr, ".claude"))
open(os.path.join(cr, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
commits = [
    ("commit đúng format", 'git commit -m "[backend-dev] T1: add validation"', OK),
    ("commit -am đúng format", 'git commit -am "[lead] T1: update stage"', OK),
    ("commit thiếu role", 'git commit -m "add validation"', B),
    ("commit hai -m (có body)", 'git commit -m "[backend-dev] T1: add x" -m "body"', B),
    ("commit có trailer trong 1 dòng", 'git commit -m "[lead] T1: x Co-Authored-By: Claude"', B),
    ("commit --signoff", 'git commit -s -m "[lead] T1: x"', B),
    ("commit không có -m", "git commit", B),
    ("commit heredoc nhiều dòng", "git commit -m \"$(cat <<'EOF'\n[lead] T1: x\n\nbody\nEOF\n)\"", B),
]
for desc, cmd, exp in commits:
    check(desc, "Bash", {"command": cmd}, None, cr, exp)
total += len(commits)

# ---- v0.3: Lead đổi giai đoạn phải đủ điều kiện trong TASK.md ----
gp = tempfile.mkdtemp()
os.makedirs(os.path.join(gp, ".claude"))
os.makedirs(os.path.join(gp, "docs/agent-tasks/T1"))
open(os.path.join(gp, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')


def gate(desc, text, tool, ti, role, exp):
    global fail, total
    open(os.path.join(gp, "docs/agent-tasks/T1/TASK.md"), "w").write(text)
    got = run(tool, ti, role, gp)
    fail += got != exp
    total += 1
    print(f"{'PASS' if got == exp else 'FAIL'}  gate: {desc}  (expect {exp}, got {got})")


S3 = {"command": "echo S3 > .agent-team/stage"}
S5 = {"command": "echo S5 > .agent-team/stage"}
S6 = {"command": "echo S6 > .agent-team/stage"}
gate("S3 khi TASK còn TODO", "- Loại: TODO (NHỎ/VỪA/LỚN)\n", "Bash", S3, None, B)
gate("S3 VỪA thiếu phương án", "- Loại: VỪA\n- Phương án chốt: TODO\n", "Bash", S3, None, B)
gate("S3 VỪA thiếu Security duyệt", "- Loại: VỪA\n- Phương án chốt: A+B\n- Security duyệt solution: TODO\n", "Bash", S3, None, B)
gate("S3 VỪA đủ", "- Loại: VỪA\n- Phương án chốt: A+B\n- Security duyệt solution: APPROVED\n- Workflow: N/A\n- UI mockup: N/A\n", "Bash", S3, None, OK)
gate("S3 VỪA thiếu Workflow/UI mockup", "- Loại: VỪA\n- Phương án chốt: A+B\n- Security duyệt solution: APPROVED\n", "Bash", S3, None, B)
gate("S3 Workflow YES nhưng chưa có file", "- Loại: VỪA\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: YES\n- UI mockup: N/A\n", "Bash", S3, None, B)
gate("S3 NHỎ thiếu tiêu chí", "- Loại: NHỎ\n", "Bash", S3, None, B)
gate("S3 NHỎ đủ", "- Loại: NHỎ\n- Tiêu chí nghiệm thu: sửa text nút Lưu\n", "Bash", S3, None, OK)
gate("S3 qua Write tool khi thiếu", "- Loại: TODO\n", "Write", {"file_path": ".agent-team/stage", "content": "S3\n"}, None, B)
gate("S3 qua Write tool khi đủ", "- Loại: NHỎ\n- Tiêu chí nghiệm thu: x\n", "Write", {"file_path": ".agent-team/stage", "content": "S3\n"}, None, OK)
BOARD_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "board.py")
bd_run = lambda *a, stdin=None: subprocess.run([sys.executable, BOARD_PY, *a], input=stdin, cwd=gp, capture_output=True, text=True)
bd_run("open", "T1", "S2", "2")
bd_run("team", "T1", "--roles", "lead,business-analyst,solution-architect")
bd_run("post", "T1", "--role", "business-analyst", stdin="WHY @solution-architect: vì sao cần bảng mới?\n")
OKS3 = "- Loại: VỪA\n- Phương án chốt: A+B\n- Security duyệt solution: APPROVED\n- Workflow: N/A\n- UI mockup: N/A\n"
gate("S3 còn WHY chưa thống nhất", OKS3, "Bash", S3, None, B)
bd_run("post", "T1", "--role", "solution-architect", stdin="RE WHY-1: vì 1 đơn huỷ nhiều lần (order.rb:42)\n")
bd_run("post", "T1", "--role", "business-analyst", stdin="AGREE WHY-1\n")
gate("S3 còn người chưa biểu quyết", OKS3, "Bash", S3, None, B)
bd_run("post", "T1", "--role", "lead", stdin="AGREE WHY-1\n")
gate("S3 mọi WHY đã thống nhất", OKS3, "Bash", S3, None, OK)
gate("role xem whys", OKS3, "Bash", {"command": ".claude/agent-team/board.py whys T1 --open"}, "test-designer", OK)
gate("role chốt team bị chặn", OKS3, "Bash", {"command": ".claude/agent-team/board.py team T1 --roles a,b"}, "business-analyst", B)
gate("role why-close bị chặn", OKS3, "Bash", {"command": ".claude/agent-team/board.py why-close T1 1 --as ruling --note x"}, "solution-architect", B)
gate("S5 test FAIL", "- Kết quả test: FAIL\n- Lint/format: PASS\n", "Bash", S5, None, B)
gate("S5 thiếu lint", "- Kết quả test: PASS\n", "Bash", S5, None, B)
gate("S5 đủ", "- Kết quả test: PASS\n- Lint/format: N/A\n- Gap còn mở: 0\n", "Bash", S5, None, OK)
gate("S5 còn gap mở", "- Kết quả test: PASS\n- Lint/format: PASS\n- Gap còn mở: 2\n", "Bash", S5, None, B)
gate("S5 chưa điền gap", "- Kết quả test: PASS\n- Lint/format: PASS\n- Gap còn mở: TODO\n", "Bash", S5, None, B)
DONE = "- Code review: APPROVED\n- Security review: APPROVED\n- Cập nhật KB: YES\n- Bài học: YES\n"
gate("S6 thiếu Security review", DONE.replace("- Security review: APPROVED\n", ""), "Bash", S6, None, B)
gate("S6 thiếu KB", DONE.replace("YES\n- Bài học", "TODO\n- Bài học"), "Bash", S6, None, B)
gate("S6 thiếu bài học", DONE.replace("- Bài học: YES", "- Bài học: TODO"), "Bash", S6, None, B)
gate("S6 đủ", DONE, "Bash", S6, None, OK)
gate("S6 KB không cần + không có bài học", "- Code review: APPROVED\n- Security review: APPROVED\n- Cập nhật KB: KHÔNG CẦN\n- Bài học: KHÔNG CÓ\n", "Bash", S6, None, OK)
gate("S2 không có điều kiện", "- Loại: TODO\n", "Bash", {"command": "echo S2 > .agent-team/stage"}, None, OK)
gate("xoá stage khi đóng", "- Loại: TODO\n", "Bash", {"command": "rm .agent-team/stage"}, None, OK)
gate("ghi stage không đúng dạng", "- Loại: TODO\n", "Bash", {"command": "echo done > .agent-team/stage"}, None, B)
gate("agent ghi stage bị chặn", "- Loại: NHỎ\n- Tiêu chí nghiệm thu: x\n", "Bash", S3, "backend-dev", B)

# ---- challenger không biết ticket: không đọc docs/, chỉ thấy code + diff ----
ch = [
    ("challenger đọc TASK.md bị chặn", "Read", {"file_path": "docs/agent-tasks/T1/TASK.md"}, "challenger", gp, B),
    ("challenger đọc KB bị chặn", "Read", {"file_path": "docs/testing/test-report.md"}, "challenger", gp, B),
    ("challenger cat TASK bằng Bash bị chặn", "Bash", {"command": "cat docs/agent-tasks/T1/TASK.md"}, "challenger", gp, B),
    ("challenger grep agent-tasks bị chặn", "Grep", {"path": "docs/agent-tasks"}, "challenger", gp, B),
    ("challenger Glob agent-tasks bị chặn", "Glob", {"glob": "docs/agent-tasks/**"}, "challenger", gp, B),
    ("challenger đọc code", "Read", {"file_path": "app/a.rb"}, "challenger", gp, OK),
    ("challenger git diff", "Bash", {"command": "git diff develop...HEAD"}, "challenger", gp, OK),
    ("challenger sửa code bị chặn", "Edit", {"file_path": "app/a.rb"}, "challenger", gp, B),
    ("challenger ghi board bị chặn", "Write", {"file_path": "docs/agent-tasks/T1/board/S5-R1-challenger-1.md"}, "challenger", gp, B),
    ("Lead đọc TASK.md", "Read", {"file_path": "docs/agent-tasks/T1/TASK.md"}, None, gp, OK),
]
for c in ch:
    check(*c)
total += len(ch)

# ---- board SQLite (board.py): role chỉ post/read/status, chỉ post bằng tên mình ----
BD = ".claude/agent-team/board.py"
HD = BD + " post T1 --role business-analyst <<'EOF'\nA > B vì N+1\nbundle exec rubocop -a\nEOF"
bd = [
    ("BA post bằng heredoc (thân bài có > và -a)", "Bash", {"command": HD}, "business-analyst", gp, OK),
    ("BA post --role=business-analyst", "Bash", {"command": BD + " post T1 --role=business-analyst --body 'ok'"}, "business-analyst", gp, OK),
    ("BA post bằng tên SA bị chặn", "Bash", {"command": BD + " post T1 --role solution-architect --body x"}, "business-analyst", gp, B),
    ("BA đọc board", "Bash", {"command": BD + " read T1"}, "business-analyst", gp, OK),
    ("security xem status", "Bash", {"command": BD + " status T1"}, "security", gp, OK),
    ("BA mở lượt bị chặn", "Bash", {"command": BD + " open T1 S2 1"}, "business-analyst", gp, B),
    ("SA ghi summary bị chặn", "Bash", {"command": BD + " summary T1 --body x"}, "solution-architect", gp, B),
    ("backend-dev export bị chặn", "Bash", {"command": BD + " export T1"}, "backend-dev", gp, B),
    ("challenger đọc board bị chặn", "Bash", {"command": BD + " read T1"}, "challenger", gp, B),
    ("role chạy qua python3 bị chặn (chạy thẳng)", "Bash", {"command": "python3 " + BD + " read T1"}, "code-reviewer", gp, B),
    ("heredoc ngoài board vẫn bị soi", "Bash", {"command": "cat <<'EOF' > app/x.rb\nx\nEOF"}, "code-reviewer", gp, B),
    ("Lead mở lượt", "Bash", {"command": BD + " open T1 S2 1 --roles business-analyst"}, None, gp, OK),
    ("Lead export", "Bash", {"command": BD + " export T1"}, None, gp, OK),
    ("Lead post --role lead", "Bash", {"command": BD + " post T1 --role lead --body x"}, None, gp, OK),
    ("dev gọi board qua biến để mạo danh bị chặn", "Bash", {"command": "B=" + BD + "; $B post T1 --role security --body x"}, "backend-dev", gp, B),
    ("dev post bằng tên mình", "Bash", {"command": BD + " post T1 --role backend-dev --reply 3 --body 'đã sửa'"}, "backend-dev", gp, OK),
]
for c in bd:
    check(*c)
total += len(bd)

# ---- migration: chỉ sinh bằng generator trong container ----
mp = tempfile.mkdtemp()
os.makedirs(os.path.join(mp, ".claude"))
os.makedirs(os.path.join(mp, "db/migrate"))
open(os.path.join(mp, ".claude/agent-team.config"), "w").write('BE_PATHS="app db"\nMIGRATION_PATHS="db/migrate"\n')
open(os.path.join(mp, "db/migrate/20261119000001_add_x.rb"), "w").write("x")
mg = [
    ("dev tự tạo file migration bị chặn", "Write", {"file_path": "db/migrate/20261119000002_add_y.rb"}, "backend-dev", mp, B),
    ("Lead tự tạo file migration bị chặn", "Write", {"file_path": "db/migrate/20261119000002_add_y.rb"}, None, mp, B),
    ("tạo migration bằng Bash bị chặn", "Bash", {"command": "cat > db/migrate/20261119000003_z.rb <<'EOF'\nx\nEOF"}, "backend-dev", mp, B),
    ("đổi tên migration (mv) bị chặn", "Bash", {"command": "mv db/migrate/20261119000001_add_x.rb db/migrate/20261119000009_add_x.rb"}, "backend-dev", mp, B),
    ("chép file vào thư mục migration bị chặn", "Bash", {"command": "cp /tmp/a.rb db/migrate"}, "backend-dev", mp, B),
    ("Edit file migration đã sinh", "Edit", {"file_path": "db/migrate/20261119000001_add_x.rb"}, "backend-dev", mp, OK),
    ("Write ghi đè file đã sinh", "Write", {"file_path": "db/migrate/20261119000001_add_x.rb"}, "backend-dev", mp, OK),
    ("sinh bằng generator trong container", "Bash", {"command": ".claude/agent-team/agent-db-clone.sh generate T1 AddStatusToOrders status:string"}, "backend-dev", mp, OK),
    ("tạo file ngoài thư mục migration", "Write", {"file_path": "db/seeds/x.rb"}, "backend-dev", mp, OK),
]
for c in mg:
    check(*c)
total += len(mg)

# ---- thiết kế task: design/ ----
dz = "docs/agent-tasks/T1/design/"
dg = [
    ("ui-designer ghi mockup", "Write", {"file_path": dz + "mockup-huy-don.html"}, "ui-designer", gp, OK),
    ("ui-designer sửa code bị chặn", "Edit", {"file_path": "app/a.rb"}, "ui-designer", gp, B),
    ("ui-designer ghi workflow bị chặn", "Write", {"file_path": dz + "workflow.md"}, "ui-designer", gp, B),
    ("BA ghi workflow", "Write", {"file_path": dz + "workflow.md"}, "business-analyst", gp, OK),
    ("BA ghi state", "Write", {"file_path": dz + "state.md"}, "business-analyst", gp, OK),
    ("BA ghi mockup bị chặn", "Write", {"file_path": dz + "mockup-a.html"}, "business-analyst", gp, B),
    ("Architect ghi sequence", "Write", {"file_path": dz + "sequence.md"}, "solution-architect", gp, OK),
    ("dev ghi vào design bị chặn", "Write", {"file_path": dz + "sequence.md"}, "frontend-dev", gp, B),
    ("tên file lạ trong design bị chặn", "Write", {"file_path": dz + "notes.md"}, "business-analyst", gp, B),
    ("ui-designer vẫn không ghi TASK.md", "Write", {"file_path": "docs/agent-tasks/T1/TASK.md"}, "ui-designer", gp, B),
]
for c in dg:
    check(*c)
total += len(dg)
os.makedirs(os.path.join(gp, dz), exist_ok=True)
open(os.path.join(gp, dz, "workflow.md"), "w").write("x")
gate("S3 Workflow YES có file, UI mockup YES thiếu file",
     "- Loại: VỪA\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: YES\n- UI mockup: YES\n", "Bash", S3, None, B)
open(os.path.join(gp, dz, "mockup-huy-don.html"), "w").write("x")
gate("S3 Workflow + UI mockup đủ file",
     "- Loại: VỪA\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: YES\n- UI mockup: YES\n", "Bash", S3, None, OK)

# ---- App Mode: docs/product + cổng owner ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from product_fixture import GOOD, write_product  # noqa: E402

ap = tempfile.mkdtemp()
os.makedirs(os.path.join(ap, ".claude"))
os.makedirs(os.path.join(ap, "docs/agent-tasks/A1"))
open(os.path.join(ap, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nFE_PATHS="web"\n')
pz = "docs/product/"
pr = [
    ("BA ghi requirements", "Write", {"file_path": pz + "requirements.md"}, "business-analyst", ap, OK),
    ("BA ghi flows", "Write", {"file_path": pz + "flows.md"}, "business-analyst", ap, OK),
    ("BA ghi APP.md bị chặn (chỉ Lead)", "Write", {"file_path": pz + "APP.md"}, "business-analyst", ap, B),
    ("BA ghi questions bị chặn (chỉ Lead)", "Write", {"file_path": pz + "questions.md"}, "business-analyst", ap, B),
    ("BA ghi mockup sản phẩm bị chặn", "Write", {"file_path": pz + "design/mockup-a.html"}, "business-analyst", ap, B),
    ("ui-designer ghi mockup sản phẩm", "Write", {"file_path": pz + "design/mockup-a.html"}, "ui-designer", ap, OK),
    ("ui-designer ghi screens", "Write", {"file_path": pz + "screens.md"}, "ui-designer", ap, OK),
    ("ui-designer ghi requirements bị chặn", "Write", {"file_path": pz + "requirements.md"}, "ui-designer", ap, B),
    ("Architect ghi requirements bị chặn", "Write", {"file_path": pz + "requirements.md"}, "solution-architect", ap, B),
    ("Lead ghi APP.md", "Write", {"file_path": pz + "APP.md"}, None, ap, OK),
    ("challenger đọc docs/product bị chặn", "Read", {"file_path": pz + "brief.md"}, "challenger", ap, B),
]
for c in pr:
    check(*c)
total += len(pr)


GAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "gap-check.py")


def app_gate(desc, task, exp, overrides=None, drop=(), product=True, stage=None, spec=True, after=None):
    """spec: sinh SPEC.md trước; after: sửa file sau khi sinh SPEC (làm SPEC cũ)."""
    global fail, total
    import shutil
    shutil.rmtree(os.path.join(ap, "docs/product"), ignore_errors=True)
    if product:
        write_product(ap, overrides, drop)
        if spec:
            subprocess.run([sys.executable, GAP, "--spec", ap], capture_output=True)
        if after:
            write_product(ap, after)
    open(os.path.join(ap, "docs/agent-tasks/A1/TASK.md"), "w").write(task)
    got = run("Bash", stage or S3, None, ap)
    fail += got != exp
    total += 1
    print(f"{'PASS' if got == exp else 'FAIL'}  app gate: {desc}  (expect {exp}, got {got})")


APP_TASK = "- Loại: APP\n- Phương án chốt: Rails + React\n- Security duyệt solution: APPROVED\n"
app_gate("APP đủ tài liệu + owner duyệt -> sang S3 (khung project)", APP_TASK, OK)
app_gate("APP thiếu phương án chốt", APP_TASK.replace("Rails + React", "TODO"), B)
app_gate("APP owner chưa duyệt", APP_TASK, B, {"APP.md": GOOD["APP.md"].replace("APPROVED", "TODO")})
app_gate("APP challenger chưa soi", APP_TASK, B, {"APP.md": GOOD["APP.md"].replace("DONE", "TODO")})
app_gate("APP câu hỏi CAO còn mở", APP_TASK, B, {"questions.md": GOOD["questions.md"] + "| Q-3 | Cọc? | CAO | MỞ | |\n"})
app_gate("APP ý owner chưa có yêu cầu", APP_TASK, B, {"brief.md": GOOD["brief.md"] + "- B-3: báo cáo\n"})
app_gate("APP chưa có docs/product", APP_TASK, B, product=False)
MOD = "- Loại: VỪA\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: N/A\n- UI mockup: N/A\n"
app_gate("module khi owner đã duyệt -> sang S3", MOD, OK)
app_gate("module khi owner chưa duyệt bị chặn", MOD, B, {"APP.md": GOOD["APP.md"].replace("APPROVED", "TODO")})
app_gate("task thường, không có App Mode -> như cũ", MOD, OK, product=False)
app_gate("APP chưa sinh SPEC.md", APP_TASK, B, spec=False)
STALE = {"requirements.md": GOOD["requirements.md"].replace("Khách đặt lịch", "Khách đặt lịch online")}
app_gate("APP sửa tài liệu sau khi sinh SPEC (SPEC cũ)", APP_TASK, B, after=STALE)
app_gate("S6 module: tài liệu + SPEC khớp", DONE, OK, stage=S6)
app_gate("S6 module: quên sinh lại SPEC sau khi sửa yêu cầu", DONE, B, stage=S6, after=STALE)
app_gate("S6 module: thêm ý owner mà chưa có yêu cầu", DONE, B, stage=S6, overrides={"brief.md": GOOD["brief.md"] + "- B-3: báo cáo\n"})
app_gate("S6 task thường, không có App Mode -> như cũ", DONE, OK, stage=S6, product=False)


# ---- S6: "Cập nhật KB: YES" phải có file KB đổi thật so với nhánh gốc ----
def kb_gate(desc, files, exp, task=DONE, base="develop", commit=False):
    """files: {đường dẫn: nội dung} ghi trên branch agent/k1 (commit=True thì commit luôn)."""
    global fail, total
    d = tempfile.mkdtemp()
    sh(d, "git", "init", "-q", "-b", "develop")
    sh(d, "git", "config", "user.email", "t@t")
    sh(d, "git", "config", "user.name", "t")
    for rel, text in {".claude/agent-team.config": f'BASE_BRANCH={base}\nBE_PATHS="app"\n',
                      "docs/business-rules.md": "# BR\n", "docs/LESSONS.md": "# L\n", "app/a.rb": "x\n"}.items():
        os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
        open(os.path.join(d, rel), "w").write(text)
    sh(d, "git", "add", ".")
    sh(d, "git", "commit", "-qm", "init")
    sh(d, "git", "switch", "-qc", "agent/k1")
    for rel, text in {"app/a.rb": "y\n", **files}.items():
        os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
        open(os.path.join(d, rel), "w").write(text)
    if commit:
        sh(d, "git", "add", ".")
        sh(d, "git", "commit", "-qm", "k1")
    os.makedirs(os.path.join(d, "docs/agent-tasks/K1"), exist_ok=True)
    open(os.path.join(d, "docs/agent-tasks/K1/TASK.md"), "w").write(task)
    got = run("Bash", S6, None, d)
    fail += got != exp
    total += 1
    print(f"{'PASS' if got == exp else 'FAIL'}  kb gate: {desc}  (expect {exp}, got {got})")


kb_gate("KB YES nhưng chỉ đổi code", {}, B)
kb_gate("KB YES nhưng chỉ thêm test case", {"docs/testing/cases/K1.md": "x"}, B)
kb_gate("KB YES nhưng chỉ ghi bài học", {"docs/LESSONS.md": "# L\n| x |\n"}, B)
kb_gate("KB YES nhưng chỉ sinh lại SPEC", {"docs/product/SPEC.md": "x"}, B)
kb_gate("KB YES, sửa business-rules (chưa commit)", {"docs/business-rules.md": "# BR\n| BR-1 |\n"}, OK)
kb_gate("KB YES, thêm api/endpoints.md (đã commit)", {"docs/api/endpoints.md": "x"}, OK, commit=True)
kb_gate("KB YES, sửa docs/product/requirements.md", {"docs/product/requirements.md": "x"}, OK)
kb_gate("KB KHÔNG CẦN, chỉ đổi code", {}, OK, task=DONE.replace("Cập nhật KB: YES", "Cập nhật KB: KHÔNG CẦN"))
kb_gate("không tìm thấy nhánh gốc -> bỏ qua kiểm", {}, OK, base="khong-co")

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
