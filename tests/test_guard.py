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
    ("đọc .env (v0.21.1: được xem)", "Read", {"file_path": "/p/.env"}, None, None, OK),
    ("đọc .env.production", "Read", {"file_path": "/p/.env.production"}, None, None, OK),
    ("đọc .env.example", "Read", {"file_path": "/p/.env.example"}, None, None, OK),
    ("đọc master.key", "Read", {"file_path": "/p/config/master.key"}, None, None, B),
    ("cat .env", "Bash", {"command": "cat .env"}, None, None, OK),
    ("printenv", "Bash", {"command": "printenv"}, None, None, B),
    ("docker inspect", "Bash", {"command": "docker inspect db"}, None, None, B),
    ("migrate DB thật", "Bash", {"command": "docker compose exec app bin/rails db:migrate"}, "backend-dev", None, B),
    ("migrate DB thật trong sh -c", "Bash", {"command": "docker compose exec app sh -c \"bin/rails db:migrate\""}, "backend-dev", None, B),
    ("migrate qua clone", "Bash", {"command": ".claude/agent-team/agent-db-clone.sh migrate T1"}, "backend-dev", None, OK),
    ("grep -r cả repo bị chặn (quét mù)", "Bash", {"command": "grep -rn \"db:migrate\" ."}, "code-reviewer", None, B),
    ("grep -r trong thư mục cụ thể", "Bash", {"command": "grep -rn \"db:migrate\" db/"}, "code-reviewer", None, OK),
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
cases.append(("agent tự commit bị chặn (v0.25: chỉ Lead commit)", "Bash", {"command": "git commit -m x"}, "backend-dev", repo, B))
cases.append(("Lead commit trên agent/*", "Bash", {"command": "git commit -m x"}, None, repo, OK))

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
    ("kb: BA ghi permission-matrix", "docs/permission-matrix.md", "business-analyst", OK),
    ("kb: BA ghi flows/", "docs/flows/README.md", "business-analyst", OK),
    ("kb: BE dev ghi permission-matrix bị chặn", "docs/permission-matrix.md", "backend-dev", B),
    ("kb: Security ghi permission-matrix bị chặn", "docs/permission-matrix.md", "security", B),
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
gate("S5 đủ", "- Kết quả test: PASS\n- Lint/format: N/A\n- Gap còn mở: 0\n- E2E: N/A\n", "Bash", S5, None, OK)
S5OK = "- Kết quả test: PASS\n- Lint/format: N/A\n- Gap còn mở: 0\n"
gate("S5 chưa điền E2E", S5OK + "- E2E: TODO\n", "Bash", S5, None, B)
gate("S5 task có UI mà E2E N/A", S5OK + "- UI mockup: YES\n- E2E: N/A\n", "Bash", S5, None, B)
gate("S5 E2E PASS nhưng chưa có ảnh", S5OK + "- E2E: PASS\n", "Bash", S5, None, B)
ev = os.path.join(gp, "docs/testing/evidence/T1")
os.makedirs(ev, exist_ok=True)
open(os.path.join(gp, ".claude/agent-team.config"), "a").write('VIEWPORTS="375 1280"\n')
open(os.path.join(ev, "TC-1-normal-375.png"), "w").write("x")
gate("S5 E2E PASS, thiếu ảnh 1280", S5OK + "- UI mockup: YES\n- E2E: PASS\n", "Bash", S5, None, B)
open(os.path.join(ev, "TC-1-normal-1280.png"), "w").write("x")
gate("S5 E2E PASS, đủ ảnh mọi chiều rộng", S5OK + "- UI mockup: YES\n- E2E: PASS\n", "Bash", S5, None, OK)
gate("test-executor chạy e2e qua clone", S5OK, "Bash", {"command": ".claude/agent-team/agent-db-clone.sh e2e T1"}, "test-executor", OK)
gate("test-designer (chỉ đọc) chạy e2e", S5OK, "Bash", {"command": ".claude/agent-team/agent-db-clone.sh e2e T1"}, "test-designer", OK)
gate("S5 còn gap mở", "- Kết quả test: PASS\n- Lint/format: PASS\n- Gap còn mở: 2\n", "Bash", S5, None, B)
gate("S5 chưa điền gap", "- Kết quả test: PASS\n- Lint/format: PASS\n- Gap còn mở: TODO\n", "Bash", S5, None, B)
DONE = "- Code review: APPROVED\n- Security review: APPROVED\n- Cập nhật KB: YES\n- Bài học: YES\n"
gate("S6 thiếu Security review", DONE.replace("- Security review: APPROVED\n", ""), "Bash", S6, None, B)
gate("S6 thiếu KB", DONE.replace("YES\n- Bài học", "TODO\n- Bài học"), "Bash", S6, None, B)
gate("S6 thiếu bài học", DONE.replace("- Bài học: YES", "- Bài học: TODO"), "Bash", S6, None, B)
gate("S6 đủ", DONE, "Bash", S6, None, OK)
gate("S6 KB không cần + không có bài học", "- Code review: APPROVED\n- Security review: APPROVED\n- Cập nhật KB: KHÔNG CẦN\n- Bài học: KHÔNG CÓ\n", "Bash", S6, None, OK)
MOCKS = os.path.join(gp, "docs/agent-tasks/T1/MOCKS.md")
MOCK_HEAD = "| Mã | File mock | Thay cho | Contract | Chờ task | Trạng thái |\n|---|---|---|---|---|---|\n"
open(MOCKS, "w").write(MOCK_HEAD + "| MK-1 | `src/mocks/a.ts` | GET /a | c | T1 | OPEN |\n")
gate("S6 còn mock OPEN bị chặn", DONE, "Bash", S6, None, B)
open(MOCKS, "w").write(MOCK_HEAD + "| MK-1 | src/mocks/a.ts | GET /a | c | T1 | VERIFIED |\n")
gate("S6 mock VERIFIED, file đã xoá", DONE, "Bash", S6, None, OK)
os.makedirs(os.path.join(gp, "src/mocks"), exist_ok=True)
open(os.path.join(gp, "src/mocks/a.ts"), "w").write("x")
gate("S6 mock VERIFIED nhưng file còn bị chặn", DONE, "Bash", S6, None, B)
os.remove(MOCKS)
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

# ---- chỉ mục hàm docs/functions/ ----
fz = [
    ("backend-dev ghi chỉ mục hàm", "Write", {"file_path": "docs/functions/order.md"}, "backend-dev", gp, OK),
    ("frontend-dev ghi chỉ mục hàm", "Edit", {"file_path": "docs/functions/cart.md"}, "frontend-dev", gp, OK),
    ("Architect ghi chỉ mục hàm", "Edit", {"file_path": "docs/functions/README.md"}, "solution-architect", gp, OK),
    ("BA ghi chỉ mục hàm bị chặn", "Write", {"file_path": "docs/functions/order.md"}, "business-analyst", gp, B),
    ("test-executor ghi chỉ mục hàm bị chặn", "Write", {"file_path": "docs/functions/order.md"}, "test-executor", gp, B),
]
for c in fz:
    check(*c)
total += len(fz)

# ---- module mới (/agent-team:module): docs/product/modules/<tên>/, cổng MODULE.md ----
import shutil as _sh
mq = tempfile.mkdtemp()
os.makedirs(os.path.join(mq, ".claude"))
os.makedirs(os.path.join(mq, "docs/agent-tasks/M1"))
open(os.path.join(mq, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
mz = "docs/product/modules/thanh-toan/"
mo = [
    ("BA ghi requirements của module", "Write", {"file_path": mz + "requirements.md"}, "business-analyst", mq, OK),
    ("ui-designer ghi mockup của module", "Write", {"file_path": mz + "design/mockup-a.html"}, "ui-designer", mq, OK),
    ("BA ghi MODULE.md bị chặn (chỉ Lead)", "Write", {"file_path": mz + "MODULE.md"}, "business-analyst", mq, B),
    ("ui-designer ghi requirements của module bị chặn", "Write", {"file_path": mz + "requirements.md"}, "ui-designer", mq, B),
]
for c in mo:
    check(*c)
total += len(mo)
MDIR = os.path.join(mq, mz)


def mod_gate(desc, task, exp, status=None, stage=None, docs=True, broken=False):
    global fail, total
    _sh.rmtree(os.path.join(mq, "docs/product"), ignore_errors=True)
    if docs:
        for rel, text in GOOD.items():
            name = "MODULE.md" if rel == "APP.md" else rel
            os.makedirs(os.path.dirname(os.path.join(MDIR, name)), exist_ok=True)
            open(os.path.join(MDIR, name), "w", encoding="utf-8").write(status if (name == "MODULE.md" and status) else text)
        subprocess.run([sys.executable, GAP, "--spec", f"--dir={mz}", mq], capture_output=True)
        if broken:
            open(os.path.join(MDIR, "brief.md"), "a", encoding="utf-8").write("- B-3: báo cáo\n")
    open(os.path.join(mq, "docs/agent-tasks/M1/TASK.md"), "w").write(task)
    got = run("Bash", stage or S3, None, mq)
    fail += got != exp
    total += 1
    print(f"{'PASS' if got == exp else 'FAIL'}  module gate: {desc}  (expect {exp}, got {got})")


MOD_TASK = "- Loại: MODULE\n- Module: docs/product/modules/thanh-toan\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n"
CHILD = "- Loại: VỪA\n- Module: docs/product/modules/thanh-toan\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: N/A\n- UI mockup: N/A\n"
mod_gate("task MODULE không được sang S3 (chỉ tài liệu)", MOD_TASK, B)
mod_gate("task con khi owner đã duyệt -> S3", CHILD, OK)
mod_gate("task con khi owner chưa duyệt bị chặn", CHILD, B, status=GOOD["APP.md"].replace("APPROVED", "TODO"))
mod_gate("task con trỏ module chưa có MODULE.md bị chặn", CHILD, B, docs=False)
mod_gate("task Module: N/A -> như task thường", CHILD.replace("docs/product/modules/thanh-toan", "N/A"), OK, docs=False)
mod_gate("S6 task con: tài liệu module khớp", DONE + "- Module: docs/product/modules/thanh-toan\n", OK, stage=S6)
mod_gate("S6 task con: tài liệu module thiếu (ý owner chưa có yêu cầu)", DONE + "- Module: docs/product/modules/thanh-toan\n", B, stage=S6, broken=True)

TASKS = "\n| T | Task | Gồm R | Phụ thuộc | Loại | Task-id | Trạng thái |\n|---|---|---|---|---|---|---|\n| T-1 | FE | R-1 | | VỪA | M1 | DOING |\n| T-2 | BE | R-1 | | VỪA | M2 | TODO |\n"
MOD_MOCKS = MOCK_HEAD + "| MK-1 | src/mocks/b.ts | GET /b | c | {} | OPEN |\n"
CHILD6 = DONE + "- Module: docs/product/modules/thanh-toan\n"
GOOD_BASE = GOOD
for desc, wait, exp in (("S6 task con: mock chờ task BE sau (T-2) -> qua", "T-2", OK),
                        ("S6 task con: mock chờ chính task này (T-1) còn OPEN bị chặn", "T-1", B)):
    GOOD = dict(GOOD_BASE, **{"APP.md": GOOD_BASE["APP.md"] + TASKS, "MOCKS.md": MOD_MOCKS.format(wait)})
    mod_gate(desc, CHILD6, exp, stage=S6)
GOOD = GOOD_BASE

# ---- tìm code có mục tiêu: chặn quét mù cả repo ----
sr = make_repo()
os.makedirs(os.path.join(sr, ".claude"), exist_ok=True)
os.makedirs(os.path.join(sr, "app", "services"), exist_ok=True)
open(os.path.join(sr, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
sc = [
    ("dev Grep không có path (cả repo) bị chặn", "Grep", {"pattern": "cancel"}, "backend-dev", sr, B),
    ("dev Grep trong app/services", "Grep", {"pattern": "cancel", "path": "app/services"}, "backend-dev", sr, OK),
    ("dev Glob **/*.rb ở gốc bị chặn", "Glob", {"pattern": "**/*.rb"}, "backend-dev", sr, B),
    ("dev Glob app/**/*.rb", "Glob", {"pattern": "app/**/*.rb"}, "backend-dev", sr, OK),
    ("BA rg không path bị chặn", "Bash", {"command": "rg cancel"}, "business-analyst", sr, B),
    ("BA rg trong docs/", "Bash", {"command": "rg cancel docs/"}, "business-analyst", sr, OK),
    ("git diff | rg (dữ liệu từ pipe)", "Bash", {"command": "git diff | rg cancel"}, "code-reviewer", sr, OK),
    ("find . không giới hạn độ sâu bị chặn", "Bash", {"command": "find . -name '*.rb'"}, "backend-dev", sr, B),
    ("find . -maxdepth 2", "Bash", {"command": "find . -maxdepth 2 -name '*.rb'"}, "backend-dev", sr, OK),
    ("git grep không pathspec bị chặn", "Bash", {"command": "git grep cancel"}, "security", sr, B),
    ("git grep -- app/", "Bash", {"command": "git grep cancel -- app/"}, "security", sr, OK),
    ("ls -R . bị chặn", "Bash", {"command": "ls -R ."}, "frontend-dev", sr, B),
    ("Lead grep -r cả repo được", "Bash", {"command": "grep -rn cancel ."}, None, sr, OK),
    ("graphify explain được", "Bash", {"command": "graphify explain OrderService"}, "backend-dev", sr, OK),
    ("đọc đúng 1 file", "Read", {"file_path": os.path.join(sr, "app/services/x.rb")}, "backend-dev", sr, OK),
]
for c in sc:
    check(*c)
total += len(sc)
open(os.path.join(sr, ".agent-team"), "a").close() if False else os.makedirs(os.path.join(sr, ".agent-team"), exist_ok=True)
open(os.path.join(sr, ".agent-team/stage"), "w").write("S3\n")
check("Scout khi đang có task: grep -r cả repo bị chặn", "Bash", {"command": "grep -rn x ."}, "scout", sr, B)
os.remove(os.path.join(sr, ".agent-team/stage"))
check("Scout khi init / kb (chưa có stage): được quét", "Bash", {"command": "grep -rn x ."}, "scout", sr, OK)
total += 2

# ---- tóm tắt giai đoạn trước khi đổi giai đoạn ----
ss = tempfile.mkdtemp()
os.makedirs(os.path.join(ss, ".claude"))
os.makedirs(os.path.join(ss, ".agent-team"))
os.makedirs(os.path.join(ss, "docs/agent-tasks/T9/board"))
open(os.path.join(ss, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
open(os.path.join(ss, "docs/agent-tasks/T9/TASK.md"), "w").write(
    "- Loại: VỪA\n- Phương án chốt: A\n- Security duyệt solution: APPROVED\n- Workflow: N/A\n- UI mockup: N/A\n")
open(os.path.join(ss, ".agent-team/stage"), "w").write("S2\n")
check("S2 → S3 khi chưa có ## S2 trong SUMMARY.md bị chặn", "Bash", {"command": "echo S3 > .agent-team/stage"}, None, ss, B)
open(os.path.join(ss, "docs/agent-tasks/T9/board/SUMMARY.md"), "w").write("# T9\n## S2 Debate\n- Chốt A\n")
check("S2 → S3 khi đã có ## S2", "Bash", {"command": "echo S3 > .agent-team/stage"}, None, ss, OK)
total += 2

# ---- mockup dùng chung _wf.css / _wf.js ----
wz = "docs/agent-tasks/T1/design/"
wf = [
    ("ui-designer ghi _wf.css", "Write", {"file_path": wz + "_wf.css"}, "ui-designer", gp, OK),
    ("ui-designer ghi _wf.js", "Write", {"file_path": wz + "_wf.js"}, "ui-designer", gp, OK),
    ("ui-designer ghi index.html của task", "Write", {"file_path": wz + "index.html"}, "ui-designer", gp, OK),
    ("BA ghi _wf.js bị chặn", "Write", {"file_path": wz + "_wf.js"}, "business-analyst", gp, B),
    ("ui-designer ghi _wf.css sản phẩm", "Write", {"file_path": "docs/product/design/_wf.css"}, "ui-designer", gp, OK),
]
for c in wf:
    check(*c)
total += len(wf)

# ---- board done/progress + lệnh không tự dừng ----
fv = [
    ("role done bằng tên mình", "Bash", {"command": ".claude/agent-team/board.py done T1 --role business-analyst --body x"}, "business-analyst", None, OK),
    ("role done bằng tên người khác bị chặn", "Bash", {"command": ".claude/agent-team/board.py done T1 --role security --body x"}, "business-analyst", None, B),
    ("role wait bị chặn (chỉ Lead)", "Bash", {"command": ".claude/agent-team/board.py wait T1"}, "business-analyst", None, B),
    ("docker compose up không -d bị chặn", "Bash", {"command": "docker compose up app"}, "backend-dev", None, B),
    ("docker compose up -d được", "Bash", {"command": "docker compose up -d app"}, "backend-dev", None, OK),
    ("tail -f bị chặn", "Bash", {"command": "tail -f log/development.log"}, "backend-dev", None, B),
    ("npm run dev bị chặn", "Bash", {"command": "npm run dev"}, "frontend-dev", None, B),
    ("vitest watch bị chặn, vitest run được", "Bash", {"command": "npx vitest"}, "test-executor", None, B),
    ("vitest run được", "Bash", {"command": "npx vitest run"}, "test-executor", None, OK),
    ("bọc timeout thì được", "Bash", {"command": "timeout 60 npm run dev"}, "frontend-dev", None, OK),
    ("Lead cũng bị chặn lệnh chạy mãi", "Bash", {"command": "docker compose up"}, None, None, B),
]
for c in fv:
    check(*c)
total += len(fv)

# ---- v0.20.0: Lead gọi agent ở S3-S5 phải có danh sách bước ----
import sqlite3 as _sq
pp = tempfile.mkdtemp()
os.makedirs(os.path.join(pp, ".claude")); os.makedirs(os.path.join(pp, ".agent-team"))
os.makedirs(os.path.join(pp, "docs/agent-tasks/T-9"))
open(os.path.join(pp, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
open(os.path.join(pp, "docs/agent-tasks/T-9/TASK.md"), "w").write("# T-9\n")
def _stage(v):
    with open(os.path.join(pp, ".agent-team/stage"), "w") as f:
        f.write(v + "\n")
AG = {"subagent_type": "backend-dev", "prompt": "x"}
_stage("S2")
check("S2: gọi agent không cần danh sách bước", "Agent", AG, None, pp, OK)
total += 1
pc = []
_stage("S3")
pc.append(("S3: Lead gọi agent khi chưa có danh sách bước bị chặn", "Agent", AG, None, pp, B))
pc.append(("S3: tool tên Task cũng bị chặn", "Task", AG, None, pp, B))
for c in pc:
    check(*c)
total += len(pc)
_db = _sq.connect(os.path.join(pp, ".agent-team/board.db"))
_db.execute("CREATE TABLE plan_steps (task TEXT, n INTEGER, title TEXT, role TEXT, state TEXT, started_at INTEGER, ended_at INTEGER)")
_db.execute("INSERT INTO plan_steps VALUES('T-9', 1, 'Scaffold', 'backend-dev', 'todo', NULL, NULL)")
_db.commit(); _db.close()
check("S3: có danh sách bước thì gọi được", "Agent", AG, None, pp, OK)
total += 1

# ---- v0.21.0: S3 có FE_PATHS → BE ∥ FE hoặc ghi lý do; Lead gọi agent → tự ▶ bước ----
BOARD_PY = os.path.join(os.path.dirname(GUARD), "..", "scripts", "board.py")
pf = tempfile.mkdtemp()
os.makedirs(os.path.join(pf, ".claude")); os.makedirs(os.path.join(pf, ".agent-team"))
os.makedirs(os.path.join(pf, "docs/agent-tasks/T-5"))
open(os.path.join(pf, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nFE_PATHS="resources/js"\n')
with open(os.path.join(pf, ".agent-team/stage"), "w") as f:
    f.write("S3\n")
TM = os.path.join(pf, "docs/agent-tasks/T-5/TASK.md")
open(TM, "w").write("# T-5\n")
_bp = lambda *a: subprocess.run([sys.executable, BOARD_PY, *a], capture_output=True, text=True, cwd=pf,
                                env={k: v for k, v in os.environ.items() if k != "AGENT_TEAM_BOARD_DB"}).stdout
_bp("plan", "T-5", "--set", "API @backend-dev | Màn hình @frontend-dev")
BE = {"subagent_type": "agent-team:backend-dev", "prompt": "x"}
check("S3 FE_PATHS: BE rồi FE nối tiếp, không lý do → chặn", "Agent", BE, None, pf, B)
open(TM, "w").write("# T-5\n- Song song: KHÔNG - FE chờ API đăng nhập\n")
check("S3 FE_PATHS: có `Song song:` lý do → được", "Agent", BE, None, pf, OK)
check("gọi backend-dev → tự ▶ bước 1", "Agent", BE, None, pf, OK)
total += 3
_out = _bp("plan", "T-5")
ok = "▶  1. API" in _out and "○  2. Màn hình" in _out
fail += not ok; total += 1
print(f"{'PASS' if ok else 'FAIL'}  plan sau khi Lead gọi backend-dev: ▶ bước 1, bước 2 vẫn ○")
open(TM, "w").write("# T-5\n")
_bp("plan", "T-5", "--set", "API @backend-dev ∥ Màn hình @frontend-dev")
check("S3 FE_PATHS: BE ∥ FE cùng nhóm → được", "Agent", {"subagent_type": "frontend-dev"}, None, pf, OK)
total += 1

# ---- v0.21.1: .env* được xem / sửa, cấm commit / push ----
ev = [
    ("dev sửa .env", "Edit", {"file_path": "/p/.env"}, "backend-dev", None, OK),
    ("Lead ghi .env.local", "Write", {"file_path": "/p/.env.local"}, None, None, OK),
    ("sed -i sửa .env", "Bash", {"command": "sed -i 's/^APP_DEBUG=.*/APP_DEBUG=false/' .env"}, "backend-dev", None, OK),
    ("đọc master.key vẫn chặn", "Read", {"file_path": "/p/config/master.key"}, None, None, B),
    ("đọc .npmrc vẫn chặn", "Read", {"file_path": "/p/.npmrc"}, None, None, B),
    ("cat id_rsa vẫn chặn", "Bash", {"command": "cat ~/.ssh/id_rsa"}, None, None, B),
    ("đọc dump vẫn chặn", "Read", {"file_path": "/p/db.dump"}, None, None, B),
    ("printenv vẫn chặn", "Bash", {"command": "printenv"}, None, None, B),
]
for c in ev:
    check(*c)
total += len(ev)
er = make_repo()
sh(er, "git", "checkout", "-qb", "agent/env")
open(os.path.join(er, ".env"), "w").write("DB_PASSWORD=x\n")
sh(er, "git", "add", "-f", ".env")
check("commit khi đang stage .env → chặn", "Bash", {"command": "git commit -m x"}, "backend-dev", er, B)
sh(er, "git", "commit", "-qm", "leak env")
check("push commit có .env → chặn", "Bash", {"command": "git push -u origin agent/env"}, None, er, B)
total += 2

# ---- v0.25-0.27: chỉ Lead dùng git ghi; worktree theo đường dẫn; loại ĐÃ CHIA; pool ----
gw = [
    ("agent push bị chặn", "Bash", {"command": "git push -u origin agent/t1"}, "frontend-dev", repo, B),
    ("agent merge bị chặn", "Bash", {"command": "git merge agent/x"}, "backend-dev", repo, B),
    ("agent tạo worktree bị chặn", "Bash", {"command": "git worktree add .worktrees/x"}, "backend-dev", repo, B),
    ("agent git diff / status vẫn được", "Bash", {"command": "git diff --stat && git status"}, "backend-dev", repo, OK),
    ("agent chạy pool.py bị chặn", "Bash", {"command": "python3 .claude/agent-team/pool.py fill"}, "backend-dev", repo, B),
    ("Lead chạy pool.py được", "Bash", {"command": "python3 .claude/agent-team/pool.py status"}, None, repo, OK),
]
for c in gw:
    check(*c)
total += len(gw)

wm = tempfile.mkdtemp()
for p_ in (wm, os.path.join(wm, ".worktrees", "T2")):
    os.makedirs(os.path.join(p_, ".claude")); os.makedirs(os.path.join(p_, ".agent-team")); os.makedirs(os.path.join(p_, "app"))
    open(os.path.join(p_, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\nTEST_PATHS="spec"\n')
WT = os.path.join(wm, ".worktrees", "T2")
with open(os.path.join(wm, ".agent-team/stage"), "w") as f:
    f.write("S2\n")  # thư mục chính đang thiết kế module (chỉ tài liệu)
with open(os.path.join(WT, ".agent-team/stage"), "w") as f:
    f.write("S3\n")  # worktree của task đang code
wc = [
    ("worktree S3: dev sửa code trong worktree được (theo stage của worktree, không theo thư mục chính S2)",
     "Edit", {"file_path": os.path.join(WT, "app/x.rb")}, "backend-dev", wm, OK),
    ("thư mục chính S2: dev sửa code ở thư mục chính bị chặn", "Edit", {"file_path": os.path.join(wm, "app/x.rb")}, "backend-dev", wm, B),
    ("worktree: `cd <worktree> &&` rồi ghi stage dùng TASK của worktree", "Bash", {"command": f"cd {WT} && ls app"}, "backend-dev", wm, OK),
]
for c in wc:
    check(*c)
total += len(wc)

gd = tempfile.mkdtemp()
os.makedirs(os.path.join(gd, ".claude")); os.makedirs(os.path.join(gd, ".agent-team")); os.makedirs(os.path.join(gd, "docs/agent-tasks/T-8"))
open(os.path.join(gd, ".claude/agent-team.config"), "w").write('BE_PATHS="app"\n')
TD = os.path.join(gd, "docs/agent-tasks/T-8/TASK.md")
S3 = {"command": "echo S3 > .agent-team/stage"}
open(TD, "w").write("- Loại: ĐÃ CHIA (M-1/T-2)\n- Tiêu chí nghiệm thu: AC-1..3\n")
check("ĐÃ CHIA sang S3 thiếu Thiết kế module + Security → chặn", "Bash", S3, None, gd, B)
open(TD, "w").write("- Loại: ĐÃ CHIA (M-1/T-2)\n- Tiêu chí nghiệm thu: AC-1..3\n- Thiết kế module: docs/agent-tasks/m1/board/SUMMARY.md\n"
                    "- Security duyệt solution: APPROVED (module M-1)\n")
check("ĐÃ CHIA đủ AC + thiết kế module + Security → sang S3 không cần debate", "Bash", S3, None, gd, OK)
total += 2
with open(os.path.join(gd, ".agent-team/stage"), "w") as f:
    f.write("S3\n")
check("S3 không có plan, không điều phối → gọi agent bị chặn", "Agent", {"subagent_type": "backend-dev"}, None, gd, B)
import sqlite3
_c = sqlite3.connect(os.path.join(gd, ".agent-team/board.db"))
_c.execute("CREATE TABLE pool (label TEXT, state TEXT)"); _c.execute("INSERT INTO pool VALUES('M-1/T-2','RUNNING')"); _c.commit(); _c.close()
check("đang điều phối (pool) → không bắt plan ở thư mục chính", "Agent", {"subagent_type": "backend-dev"}, None, gd, OK)
total += 2

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
