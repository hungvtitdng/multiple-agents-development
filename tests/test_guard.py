#!/usr/bin/env python3
"""Test guard.py: python3 tests/test_guard.py"""
import json
import os
import subprocess
import sys
import tempfile

GUARD = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "hooks", "guard.py")


def run(tool, tool_input, role=None, cwd=None):
    data = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or os.getcwd()}
    if role:
        data["agent_type"] = f"agent-team:{role}"
    r = subprocess.run([sys.executable, GUARD], input=json.dumps(data), capture_output=True, text=True)
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

# Debate board + điểm chấm
proj = tempfile.mkdtemp()
board = os.path.join(proj, "docs/agent-tasks/T1/board")
os.makedirs(board)
open(os.path.join(board, "S2-R1-security-1.md"), "w").write("x")
os.makedirs(os.path.join(proj, ".agent-team/scores/T1"))
open(os.path.join(proj, ".agent-team/scores/T1/backend-dev.md"), "w").write("x")
bp = "docs/agent-tasks/T1/board/"
sp = ".agent-team/scores/T1/"
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
    ("ghi điểm của mình", "Write", {"file_path": sp + "security.md"}, "security", proj, OK),
    ("ghi điểm tên người khác", "Write", {"file_path": sp + "tester.md"}, "security", proj, B),
    ("sửa điểm đã chấm", "Write", {"file_path": sp + "backend-dev.md"}, "backend-dev", proj, B),
    ("đọc điểm người khác", "Read", {"file_path": sp + "backend-dev.md"}, "security", proj, B),
    ("grep thư mục điểm", "Grep", {"path": ".agent-team/scores"}, "tester", proj, B),
    ("cat điểm bằng Bash", "Bash", {"command": "cat .agent-team/scores/T1/*.md"}, "backend-dev", proj, B),
    ("Lead đọc điểm", "Read", {"file_path": sp + "backend-dev.md"}, None, proj, OK),
    ("ghi board bằng Bash", "Bash", {"command": "echo hi > docs/agent-tasks/T1/board/S2-R1-backend-dev-9.md"}, "backend-dev", proj, B),
    ("ls board bằng Bash", "Bash", {"command": "ls -tr docs/agent-tasks/T1/board"}, "code-reviewer", proj, OK),
    ("dev chạy script clone", "Bash", {"command": ".claude/agent-team/agent-db-clone.sh verify T1"}, "backend-dev", proj, OK),
]

for c in cases:
    check(*c)
total += len(cases)
print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
