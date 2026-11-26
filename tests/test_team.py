#!/usr/bin/env python3
"""Test pool.py phần team: handoff, claimable, claim, sync (remote = bare repo tạm). python3 tests/test_team.py"""
import os
import subprocess
import sys
import tempfile

POOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "pool.py")
ENV = {k: v for k, v in os.environ.items() if k != "AGENT_TEAM_BOARD_DB"}
fail = total = 0


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout


def run(cwd, *args):
    r = subprocess.run([sys.executable, POOL, *args], capture_output=True, text=True, cwd=cwd, env=ENV)
    return r.returncode, r.stdout + r.stderr


def w(cwd, rel, text):
    p = os.path.join(cwd, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


tmp = os.path.realpath(tempfile.mkdtemp())
origin = os.path.join(tmp, "origin.git")
sh(tmp, "git", "init", "-q", "--bare", "-b", "develop", origin)

A = os.path.join(tmp, "A")
sh(tmp, "git", "clone", "-q", origin, A)
sh(A, "git", "config", "user.email", "a@t"), sh(A, "git", "config", "user.name", "a")
sh(A, "git", "switch", "-qc", "develop")
APP = """# Cà phê
| M | Module | Gồm R | Phụ thuộc | Loại | Tag | Task-id | Người chạy | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| M-0 | Khung | R-1 | | VỪA | | m0 | | DONE |
| M-1 | Auth | R-2 | M-0 | NẶNG | | | | TODO |
| M-2 | Hồ sơ | R-3 | M-1 | VỪA | | | | TODO |
| M-3 | Báo cáo | R-4 | M-1 | NHẸ | | | | TODO |
| M-E2E | E2E | tất cả | mọi module | VỪA | | | | TODO |

## Lý do phụ thuộc
- M-1 → M-0 (code): dùng khung project
- M-2 → M-1 (code): dùng bảng users
- M-3 → M-1 (contract): chỉ gọi PermissionService
"""
w(A, "docs/product/APP.md", APP)
w(A, ".claude/agent-team.config", 'BASE_BRANCH=develop\nPUSH=1\nBE_PATHS="app"\n')
w(A, ".gitignore", ".agent-team/\n.claude/agent-team.local.config\n")
w(A, "app/config.php", "<?php return ['db' => env('DB_HOST'), 'key' => env('APP_KEY'), 'mail' => env('MAIL_HOST'), 'port' => env('MAIL_PORT', 587)];\n")
w(A, ".env.example", "DB_HOST=\nAPP_KEY=\n")
w(A, "docs/agent-tasks/m0/TASK.md", "- Kết quả test: PASS\n- E2E: PASS\n")
w(A, "docs/business-rules.md", "BR-1: a\n")
sh(A, "git", "add", "."), sh(A, "git", "commit", "-qm", "plan"), sh(A, "git", "push", "-q", "-u", "origin", "develop")

code, out = run(A, "handoff")
check("handoff thiếu: contract M-1, .env.example thiếu MAIL_HOST, SEED_CMD, README → exit 1",
      code == 1 and "❌ contract module NẶNG" in out and "MAIL_HOST" in out and "❌ SEED_CMD" in out and "❌ README" in out)
check("handoff: phụ thuộc có lý do, M-0 PASS", "✅ mỗi phụ thuộc có lý do" in out and "✅ M-0 DONE" in out)
check("key có giá trị mặc định trong code (env('MAIL_PORT', 587)) không bắt buộc", "MAIL_PORT" not in out)
w(A, "docs/product/contracts/M-1.md", "PermissionService::can(user, action)\n")
w(A, ".env.example", "DB_HOST=\nAPP_KEY=\nMAIL_HOST=\n")
w(A, "README.md", "# App\n## Chạy dự án lần đầu\n1. cp .env.example .env\n")
with open(os.path.join(A, ".claude/agent-team.config"), "a") as f:
    f.write('SEED_CMD="php artisan migrate:fresh --seed"\n')
code, out = run(A, "handoff")
check("handoff: các mục đã sửa thành ✅ (gap-check chưa cài vẫn ❌ → exit 1)",
      code == 1 and "✅ contract module NẶNG" in out and "✅ .env.example" in out and "✅ SEED_CMD" in out and "✅ README" in out and "❌ gap-check" in out)
check("handoff: báo module nhận được ngay = M-1, M-3 (M-3 chỉ cần contract M-1)", "Nhận được ngay sau bàn giao: M-1, M-3" in out)
sh(A, "git", "add", "."), sh(A, "git", "commit", "-qm", "handoff"), sh(A, "git", "push", "-q")


def clone(name, dev):
    d = os.path.join(tmp, name)
    sh(tmp, "git", "clone", "-q", "-b", "develop", origin, d)
    sh(d, "git", "config", "user.email", f"{dev}@t"), sh(d, "git", "config", "user.name", dev)
    w(d, ".claude/agent-team.local.config", f"DEV_ID={dev}\n")
    return d


B, C = clone("B", "hv"), clone("C", "nam")
code, out = run(B, "claimable")
check("claimable: 🟢 M-1, M-3 · ⏳ M-2 chờ M-1 · E2E chờ tất cả", "🟢 M-1" in out and "🟢 M-3" in out and "⏳ M-2" in out and "⏳ M-E2E" in out)
w(B, ".claude/agent-team.local.config", "DEV_ID=\n")
check("claim khi chưa có DEV_ID bị từ chối", run(B, "claim", "M-1")[0] == 1)
w(B, ".claude/agent-team.local.config", "DEV_ID=hv\n")
check("claim M-2 khi M-1 chưa xong bị từ chối", "chờ M-1" in run(B, "claim", "M-2")[1])
code, out = run(B, "claim", "M-1")
br = sh(B, "git", "rev-parse", "--abbrev-ref", "HEAD").strip()
check("claim M-1: branch task/YYYYMMDD-hv-m1 từ origin/develop + push", code == 0 and br.endswith("-hv-m1") and br in sh(B, "git", "branch", "-r"))
row = [l for l in open(os.path.join(B, "docs/product/APP.md"), encoding="utf-8") if l.startswith("| M-1 ")][0]
check("dòng M-1: Người chạy hv, DESIGN, Task-id; dòng khác giữ nguyên", "| hv | DESIGN |" in row and br.split("/")[1] in row
      and "| M-2 | Hồ sơ | R-3 | M-1 | VỪA |" in open(os.path.join(B, "docs/product/APP.md"), encoding="utf-8").read())
code, out = run(C, "claim", "M-1")
check("người khác claim M-1 (branch hv đã trên remote) bị từ chối", code == 1 and "đã có người nhận" in out)
code, out = run(C, "claimable")
check("claimable của nam: M-1 👤 hv, M-3 vẫn 🟢", "👤 M-1" in out and "hv-m1" in out and "🟢 M-3" in out)
code, out = run(C, "claim", "M-3")
check("nam nhận M-3 song song (chỉ cần contract M-1)", code == 0 and "-nam-m3" in sh(C, "git", "rev-parse", "--abbrev-ref", "HEAD"))

# sync: develop có commit mới (A sửa quy tắc nghiệp vụ)
w(A, "docs/business-rules.md", "BR-1: a\nBR-2: khoá sau 5 lần sai\n")
sh(A, "git", "commit", "-qam", "rule"), sh(A, "git", "push", "-q")
code, out = run(B, "wait", "--interval", "1", "--max", "2")
check("wait: develop có commit mới → CÓ VIỆC, bảo sync", code == 0 and "pool.py sync" in out)
code, out = run(B, "sync")
check("sync: merge develop, báo đọc lại business-rules.md + cảnh báo quy tắc đổi",
      code == 0 and "docs/business-rules.md" in out and "⚠" in out and "BR-2" in open(os.path.join(B, "docs/business-rules.md")).read())
check("sync lần 2: đã mới nhất", "Đã mới nhất" in run(B, "sync")[1])
w(B, "docs/business-rules.md", "BR-1: a\nBR-2: khoá sau 3 lần sai\n")
sh(B, "git", "commit", "-qam", "hv rule")
w(A, "docs/business-rules.md", "BR-1: a\nBR-2: khoá sau 10 lần sai\n")
sh(A, "git", "commit", "-qam", "a rule"), sh(A, "git", "push", "-q")
code, out = run(B, "sync")
check("sync conflict: --abort, báo file, không tự gộp", code == 2 and "CONFLICT" in out and "business-rules.md" in out
      and sh(B, "git", "status", "--porcelain", "--untracked-files=no") == "")

# máy còn task chưa merge thì không nhận module mới
run(B, "module", "M-1", "--state", "SPLIT")
run(B, "add", "M-1/T-1", "--task-id", "20261124-hv-m1-t1", "--title", "API")
check("còn task chưa merge thì không claim module khác", "còn 1 task chưa merge" in run(B, "claim", "M-3")[1])

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
