#!/usr/bin/env python3
"""Test code-graph.py: python3 tests/test_code_graph.py"""
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "scripts", "code-graph.py"))
fail = total = 0


def sh(*cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def cg(*args, cwd):
    return sh(sys.executable, SCRIPT, *args, cwd=cwd)


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


d = os.path.realpath(tempfile.mkdtemp())
files = {
    "app/models/user.rb": "class User\n  def admin?; true; end\nend\n",
    "app/models/order.rb": "class Order\n  belongs_to :user\n  def owner; User.find(1); end\nend\n",
    "app/controllers/orders_controller.rb": "class OrdersController\n  def show; Order.find(1); end\nend\n",
    "lib/helper.rb": "require_relative '../app/models/user'\nmodule Helper; end\n",
    "frontend/src/api.ts": "export class ApiClient {}\n",
    "frontend/src/page.ts": "import { ApiClient } from './api'\nexport class Page { c = new ApiClient() }\n",
    "node_modules/x/index.js": "class Ignored {}\n",
}
for rel, body in files.items():
    os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
    open(os.path.join(d, rel), "w").write(body)
sh("git", "init", "-q", "-b", "main", cwd=d)
sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-f", ".", cwd=d)
sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init", cwd=d)

r = cg("who-uses", "User", cwd=d)
check("chưa build thì exit 3", r.returncode == 3)
r = cg("build", cwd=d)
check("build thành công", r.returncode == 0 and os.path.isfile(os.path.join(d, "code-graph-out/GRAPH_REPORT.md")))
r = cg("who-uses", "User", cwd=d)
check("who-uses User: Order (INFERRED) + helper (EXTRACTED)",
      "[INFERRED] app/models/order.rb" in r.stdout and "[EXTRACTED] lib/helper.rb" in r.stdout)
r = cg("who-uses", "Order", cwd=d)
check("who-uses Order: controller", "app/controllers/orders_controller.rb" in r.stdout)
r = cg("uses", "app/models/order.rb", cwd=d)
check("uses order.rb: user.rb", "app/models/user.rb" in r.stdout)
r = cg("who-uses", "frontend/src/api.ts", cwd=d)
check("import TS tường minh: page.ts [EXTRACTED]", "[EXTRACTED] frontend/src/page.ts" in r.stdout)
r = cg("who-uses", "Ignored", cwd=d)
check("bỏ qua node_modules, exit 4", r.returncode == 4)
r = cg("explain", "User", cwd=d)
check("explain có định nghĩa + được dùng bởi", "định nghĩa" in r.stdout and "Được dùng bởi" in r.stdout)
open(os.path.join(d, "app/models/user.rb"), "a").write("# sửa\n")
sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "edit", cwd=d)
r = cg("who-uses", "User", cwd=d)
check("graph cũ thì cảnh báo", "CẢNH BÁO" in r.stderr)
check("lệnh sai exit 2", cg("bogus", cwd=d).returncode == 2)

# Nhiều repo con: root không phải repo, REPOS="be fe"
m = os.path.realpath(tempfile.mkdtemp())
for repo, rel, body in [
    ("be", "app/models/order.rb", "class Order\nend\n"),
    ("fe", "src/order.ts", "export class OrderView { o = 'Order' }\n"),
]:
    os.makedirs(os.path.dirname(os.path.join(m, repo, rel)), exist_ok=True)
    open(os.path.join(m, repo, rel), "w").write(body)
    sh("git", "init", "-q", "-b", "main", cwd=os.path.join(m, repo))
    sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "add", ".", cwd=os.path.join(m, repo))
    sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i", cwd=os.path.join(m, repo))
os.makedirs(os.path.join(m, ".claude"))
open(os.path.join(m, ".claude/agent-team.config"), "w").write('REPOS="be fe"\n')
r = cg("build", cwd=m)
check("multi-repo build ở root không phải repo", r.returncode == 0 and "2 file" in r.stdout)
r = cg("who-uses", "Order", cwd=os.path.join(m, "fe"))
check("multi-repo: query từ trong fe/ thấy cạnh fe -> be", "fe/src/order.ts" in r.stdout)
open(os.path.join(m, "be/app/models/order.rb"), "a").write("# x\n")
sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "e", cwd=os.path.join(m, "be"))
r = cg("who-uses", "Order", cwd=m)
check("multi-repo: graph cũ ở be thì cảnh báo", "CẢNH BÁO" in r.stderr and "be@" in r.stderr)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
