#!/usr/bin/env python3
"""Test kb-check.py: python3 tests/test_kb_check.py"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "scripts", "kb-check.py")
TPL = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "templates", "kb")
fail = total = 0


def run(root, *flags):
    r = subprocess.run([sys.executable, SCRIPT, "--json", *flags, root], capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else [])


def check(desc, got, exp):
    global fail, total
    total += 1
    fail += got != exp
    print(f"{'PASS' if got == exp else 'FAIL'}  {desc}  (expect {exp}, got {got})")


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


def why(rows, rel):
    return next((r["why"] for r in rows if r["file"] == rel), "")


def git(root, *args):
    subprocess.run(["git", "-C", root, *args], capture_output=True, check=True)


proj = tempfile.mkdtemp()
write(proj, ".claude/agent-team.config", 'BE_PATHS="app"\n')
code, rows = run(proj)
check("không có docs -> thiếu", code, 1)

for dp, _, fs in os.walk(TPL):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), TPL)
        write(proj, os.path.join("docs", rel), open(os.path.join(dp, f), encoding="utf-8").read())
code, rows = run(proj)
check("khung template chưa điền -> thiếu", code, 1)
check("khung template: mọi file bắt buộc đều THIẾU", sum(not r["ok"] for r in rows) >= 16, True)

for name in ("a", "b", "c", "policy"):
    write(proj, f"app/{name}.rb", "x\n" * 40)
git(proj, "init", "-q")
git(proj, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
git(proj, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
SHA = subprocess.run(["git", "-C", proj, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

FILLED = (f"verified-at: {SHA}\n| BR-1 | x | y | z | Assumption | app/a.rb:10 |\n"
          "| BR-2 | x | y | z | Observed | app/b.rb:20 |\n| BR-3 | x | y | z | Assumption | app/c.rb:30 |\n")
ROLES = (f"# R\nverified-at: {SHA}\n| Vai trò | Mô tả | Gán bởi | Kế thừa | Nhãn | Nguồn |\n|---|---|---|---|---|---|\n"
         "| Chủ | | | | Observed | app/policy.rb:1 |\n| Khách | | | | Observed | app/policy.rb:2 |\n\n"
         "| C | Điều kiện | Kiểm ở đâu | Nhãn | Nguồn |\n|---|---|---|---|---|\n| C-own | của mình | query | Observed | app/policy.rb:3 |\n")
MATRIX = (f"# M\nverified-at: {SHA}\n| P | Hành động | Chủ | Khách | Page / API | Nhãn | Nguồn |\n|---|---|---|---|---|---|---|\n"
          "| P-booking.cancel | Huỷ | ✅ | ✅ C-own + BR-2 | S-4 | Observed | app/policy.rb:5 |\n")
FLOWS = f"# F\nverified-at: {SHA}\n## F-1: Đặt lịch\n| Bước | Ai | Page | Hành động | P | BR | Nếu lỗi | Nguồn |\n|---|---|---|---|---|---|---|---|\n| 1 | Khách | S-1 | huỷ | P-booking.cancel | BR-1 | - | app/a.rb:1 |\n"
for rel in ("project-overview", "architecture", "tech-stack", "domain-model", "business-rules", "glossary", "api/endpoints",
            "database/schema", "testing/test-strategy", "engineering/coding-standards", "database/migration-rules",
            "testing/automation-guide", "security/review-patterns"):
    write(proj, f"docs/{rel}.md", "# t\n" + FILLED)
write(proj, "docs/roles-and-permissions.md", ROLES)
write(proj, "docs/permission-matrix.md", MATRIX)
write(proj, "docs/flows/README.md", FLOWS)
code, rows = run(proj)
check("điền đủ nhưng chưa có module -> thiếu", code, 1)
write(proj, "docs/modules/trip/README.md", f"# trip\nverified-at: {SHA}\n")
SCREEN = f"# Huỷ\n- Route: /b/:id\n- File: app/a.rb:1\n- Quyền: P-booking.cancel\n- Quy tắc: BR-2\n- Luồng: F-1 bước 1\n- verified-at: {SHA}\n"
write(proj, "docs/modules/trip/screens/huy.md", SCREEN)
code, rows = run(proj)
check("điền đủ + 1 module + 1 page -> đạt", (code, [r["why"] for r in rows if not r["ok"]]), (0, []))


def case(desc, rel, text, expect_in, target=None):
    old = open(os.path.join(proj, rel), encoding="utf-8").read()
    write(proj, rel, text)
    code, rows = run(proj)
    check(desc, (code, expect_in in why(rows, target or rel)), (1 if expect_in else 0, True))
    write(proj, rel, old)


case("business-rules chỉ 1/3 nguồn -> thiếu", "docs/business-rules.md", f"# t\nverified-at: {SHA}\n| BR-1 | x | y | z | Observed | app/a.rb:10 |\n", "1/3 nguồn")
case("verified-at còn placeholder <commit> -> thiếu", "docs/glossary.md", "# t\nverified-at: <commit>\n", "verified-at")
case("nguồn trỏ file không có -> thiếu", "docs/glossary.md", f"# t\nverified-at: {SHA}\napp/zzz.rb:3\n", "app/zzz.rb:3 không có file")
case("nguồn vượt cuối file -> thiếu", "docs/glossary.md", f"# t\nverified-at: {SHA}\napp/a.rb:999\n", "vượt cuối file")
case("URL có cổng không bị coi là nguồn", "docs/glossary.md", f"# t\nverified-at: {SHA}\nhttp://example.com:8080/x\n", "", None)
case("BR thiếu nhãn -> thiếu", "docs/business-rules.md", FILLED + "| BR-9 | x | y | z | | app/a.rb:1 |\n", "BR-9 thiếu nhãn")
case("BR thiếu nguồn -> thiếu", "docs/business-rules.md", FILLED + "| BR-9 | x | y | z | Observed | |\n", "BR-9 thiếu nguồn")
case("BR nguồn là task-id -> đạt", "docs/business-rules.md", FILLED + "| BR-9 | x | y | z | Verified | 20261120-huy-lich |\n", "", None)
case("ma trận ô trống -> thiếu", "docs/permission-matrix.md", MATRIX.replace("| ✅ | ✅ C-own", "|  | ✅ C-own"), "ô trống")
case("ma trận cột vai trò lạ -> thiếu", "docs/permission-matrix.md", MATRIX.replace("| Chủ | Khách |", "| Chủ | Thợ |"), "cột 'thợ'")
case("ma trận trỏ C- không có -> thiếu", "docs/permission-matrix.md", MATRIX.replace("C-own", "C-branch"), "C-branch không có")
case("ma trận thiếu nguồn policy -> thiếu", "docs/permission-matrix.md", MATRIX.replace("app/policy.rb:5", ""), "thiếu nguồn policy")
case("page trỏ BR không có -> thiếu", "docs/modules/trip/screens/huy.md", SCREEN.replace("BR-2", "BR-77"), "BR-77 không có trong KB tổng")
case("page trỏ P- không có -> thiếu", "docs/modules/trip/screens/huy.md", SCREEN.replace("P-booking.cancel", "P-booking.delete"), "P-booking.delete")
case("page trỏ F- không có -> thiếu", "docs/modules/trip/screens/huy.md", SCREEN.replace("F-1", "F-9"), "F-9")
case("page thiếu verified-at -> thiếu", "docs/modules/trip/screens/huy.md", SCREEN.replace(f"- verified-at: {SHA}\n", ""), "verified-at")
case("module trong danh sách chưa có README", "docs/modules/README.md", "| Module | Code |\n|---|---|\n| order | app/order |\n", "order", "docs/modules/README.md")
case("route trỏ file KB không có", "docs/modules/README.md", "| Route | Module | File KB | File code |\n|---|---|---|---|\n| /x | trip | trip/screens/khong.md | |\n", "không có", "docs/modules/README.md")

write(proj, "docs/modules/README.md", "| Route | Module | File KB | File code |\n|---|---|---|---|\n| /b/:id | trip | trip/screens/huy.md | app/a.rb |\n")
check("route trỏ file KB có thật -> đạt", run(proj)[0], 0)

write(proj, "app/a.rb", "y\n" * 40)
git(proj, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "đổi code")
code, rows = run(proj)
check("code đổi sau verified-at -> CŨ", (code, "CŨ" in why(rows, "docs/business-rules.md") and "app/a.rb" in why(rows, "docs/business-rules.md")), (1, True))
check("file không trích app/a.rb thì không CŨ", "CŨ" in why(rows, "docs/permission-matrix.md"), False)

r = subprocess.run([sys.executable, SCRIPT, "--index", proj], capture_output=True, text=True)
idx = dict(ln.split("\t") for ln in r.stdout.splitlines())
check("--index: BR-2 → page huỷ", idx.get("BR-2"), "modules/trip/screens/huy.md")
check("--index: P-booking.cancel → luồng + page", sorted(idx.get("P-booking.cancel", "").split(", ")), ["flows/README.md", "modules/trip/screens/huy.md"])

nocfg = tempfile.mkdtemp()
r = subprocess.run([sys.executable, SCRIPT, nocfg], capture_output=True, text=True)
check("không có config -> exit 2", r.returncode, 2)

# ---- chỉ mục hàm docs/functions/ so với graph ----
fp = tempfile.mkdtemp()
write(fp, ".claude/agent-team.config", 'FUNCTION_INDEX_PATHS="app/services"\nUSE_CODE_GRAPH=1\n')
write(fp, "app/services/order_service.rb", "class OrderService\n  def list_active(u)\n  end\n\n  def cancel(id)\n  end\n\n  private\n\n  def restock(o)\n  end\nend\n")
write(fp, "app/services/cart.ts", "export function addItem(c) { return c }\nfunction helper() { return 1 }\n")
for c in (("init", "-q"), ("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"), ("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i")):
    git(fp, *c)
FSHA = subprocess.run(["git", "-C", fp, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def node(i, label, f, line, cls=False):
    return {"id": i, "label": label, "_callable": True, "_callable_class": cls, "source_file": f, "source_location": f"L{line}"}


GRAPH = {"built_at_commit": FSHA, "nodes": [
    node("svc_order", "OrderService", "app/services/order_service.rb", 1, True),
    node("svc_order_list_active", ".list_active()", "app/services/order_service.rb", 2),
    node("svc_order_cancel", ".cancel()", "app/services/order_service.rb", 5),
    node("svc_order_restock", ".restock()", "app/services/order_service.rb", 10),
    node("svc_cart_additem", "addItem()", "app/services/cart.ts", 1),
    node("svc_cart_helper", "helper()", "app/services/cart.ts", 2)], "links": []}
write(fp, "graphify-out/graph.json", json.dumps(GRAPH))
FROW = "docs/functions/ (so với graph)"
IDX = (f"# Order\nverified-at: {FSHA[:7]}\n| Hàm | Ý nghĩa | Tham số chính | Trả về | Nguồn |\n|---|---|---|---|---|\n"
       "| `OrderService.list_active` | đơn chưa huỷ | u | ds | app/services/order_service.rb:2 |\n")
code, rows = run(fp)
check("FUNCTION_INDEX_PATHS có, chưa có file chỉ mục -> thiếu", "chưa có file chỉ mục" in why(rows, FROW), True)
write(fp, "docs/functions/order.md", IDX)
code, rows = run(fp)
w = why(rows, FROW)
check("thiếu hàm public: cancel + addItem", ("OrderService.cancel" in w, "addItem" in w), (True, True))
check("không đòi hàm private (Ruby private) / không export (TS)", ("restock" in w, "helper" in w), (False, False))
write(fp, "docs/functions/order.md", IDX + "| `OrderService.cancel` | huỷ + hoàn kho | id | đơn | app/services/order_service.rb:5 |\n"
      "| `OrderService#old` | đã xoá | | | app/services/order_service.rb:1 |\n")
write(fp, "docs/functions/_shared.md", f"# Dùng chung\nverified-at: {FSHA[:7]}\n| Hàm | Ý nghĩa | Tham số chính | Trả về | Nguồn |\n|---|---|---|---|---|\n"
      "| `addItem()` | thêm vào giỏ | c | giỏ | app/services/cart.ts:1 |\n| `Order.x` | → xem order.md | | | |\n")
code, rows = run(fp)
w = why(rows, FROW)
check("hàm trong chỉ mục không còn trong code -> thừa (OrderService#old)", "OrderService.old" in w and "thiếu" not in w, True)
check("dòng tham chiếu → không bị coi là thừa", "Order.x" in w, False)
write(fp, "docs/functions/order.md", IDX + "| `OrderService.cancel` | huỷ + hoàn kho | id | đơn | app/services/order_service.rb:5 |\n")
code, rows = run(fp)
check("chỉ mục khớp graph -> dòng so khớp đạt", next(r["ok"] for r in rows if r["file"] == FROW), True)
check("file chỉ mục được kiểm nguồn file:dòng như KB", "docs/functions/order.md" in [r["file"] for r in rows], True)
r = subprocess.run([sys.executable, SCRIPT, "--functions", fp], capture_output=True, text=True)
check("--functions in danh sách đã đủ", "đã có trong chỉ mục: 3" in r.stdout and "(không)" in r.stdout, True)
os.remove(os.path.join(fp, "graphify-out/graph.json"))
code, rows = run(fp)
check("chưa có graph -> báo chạy graphify update", "graphify update" in why(rows, FROW), True)
write(fp, ".claude/agent-team.config", "")
code, rows = run(fp)
check("không có FUNCTION_INDEX_PATHS -> không kiểm chỉ mục", FROW in [r["file"] for r in rows], False)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
