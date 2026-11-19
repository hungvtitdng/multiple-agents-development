#!/usr/bin/env python3
"""Test gap-check.py: python3 tests/test_gap_check.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "plugins", "agent-team", "scripts", "gap-check.py")
TPL = os.path.join(HERE, "..", "plugins", "agent-team", "templates", "product")
sys.path.insert(0, HERE)
fail = total = 0


def run(root, *flags):
    r = subprocess.run([sys.executable, SCRIPT, "--json", *flags, root], capture_output=True, text=True)
    rows = json.loads(r.stdout) if r.stdout.strip() else []
    return r.returncode, {x["item"]: x for x in rows}


def check(desc, got, exp):
    global fail, total
    total += 1
    fail += got != exp
    print(f"{'PASS' if got == exp else 'FAIL'}  {desc}  (expect {exp}, got {got})")


def bad(rows, prefix):
    """Mục có tên bắt đầu bằng prefix có đang THIEU không."""
    return any(not r["ok"] for k, r in rows.items() if k.startswith(prefix))


from product_fixture import GOOD, write_product  # noqa: E402


def fresh(overrides=None, drop=()):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, ".claude"))
    open(os.path.join(root, ".claude", "agent-team.config"), "w").write('BE_PATHS="app"\n')
    write_product(root, overrides, drop)
    return root


# không có config / docs/product
nocfg = tempfile.mkdtemp()
check("không có config -> exit 2", run(nocfg)[0], 2)
noprod = tempfile.mkdtemp()
os.makedirs(os.path.join(noprod, ".claude"))
open(os.path.join(noprod, ".claude", "agent-team.config"), "w").write("")
check("chưa có docs/product -> exit 2", run(noprod)[0], 2)

# khung template chưa điền -> mọi mục thiếu
tpl = tempfile.mkdtemp()
os.makedirs(os.path.join(tpl, ".claude"))
open(os.path.join(tpl, ".claude", "agent-team.config"), "w").write("")
shutil.copytree(TPL, os.path.join(tpl, "docs", "product"))
code, rows = run(tpl)
check("khung template -> thiếu", code, 1)
check("khung template: ≥ 9 mục THIEU", sum(not r["ok"] for r in rows.values()) >= 9, True)

# bộ tài liệu đủ -> đạt
code, rows = run(fresh())
check("tài liệu đủ -> đạt", code, 0)
check("tài liệu đủ + --gate (owner đã duyệt) -> đạt", run(fresh(), "--gate")[0], 0)

# từng lỗ hổng
cases = [
    ("intake còn TODO", {"intake.md": GOOD["intake.md"] + "- Database: TODO\n"}, "intake"),
    ("ý owner B-3 chưa có yêu cầu", {"brief.md": GOOD["brief.md"] + "- B-3: báo cáo doanh thu\n"}, "truy vết"),
    ("câu hỏi CAO còn MỞ", {"questions.md": GOOD["questions.md"] + "| Q-3 | Cọc bao nhiêu? | CAO | MỞ | |\n"}, "questions"),
    ("câu hỏi CAO chỉ GIẢ ĐỊNH", {"questions.md": GOOD["questions.md"] + "| Q-3 | Cọc? | CAO | GIẢ ĐỊNH | 0đ |\n"}, "questions"),
    ("thiếu góc nhìn 12", {"coverage.md": GOOD["coverage.md"].rsplit("| 12 ", 1)[0]}, "coverage"),
    ("góc LOẠI không lý do", {"coverage.md": GOOD["coverage.md"].replace("app nhỏ, không cần", "")}, "coverage"),
    ("góc CHƯA BIẾT không trỏ Q-n", {"coverage.md": GOOD["coverage.md"].replace("| CHƯA BIẾT | Q-2 |", "| CHƯA BIẾT | hỏi sau |")}, "coverage"),
    ("default owner chưa chọn", {"defaults.md": GOOD["defaults.md"] + "| D-3 | Cọc | 30% | CHƯA | |\n"}, "defaults"),
    ("default GIỮ chưa có R-n", {"defaults.md": GOOD["defaults.md"] + "| D-3 | Cọc | 30% | GIỮ | |\n"}, "defaults"),
    ("default KHÁC không ghi cách", {"defaults.md": GOOD["defaults.md"].replace("| BỎ | |", "| KHÁC | |")}, "defaults"),
    ("yêu cầu không có nguồn", {"requirements.md": GOOD["requirements.md"] + "| R-4 | Thêm chat | | Khách | N/A | x |\n"}, "requirements"),
    ("yêu cầu trỏ màn không có", {"requirements.md": GOOD["requirements.md"].replace("| S-2 |", "| S-9 |")}, "requirements"),
    ("yêu cầu thiếu AC", {"requirements.md": GOOD["requirements.md"].replace("| job gửi SMS |", "| |")}, "requirements"),
    ("flow thiếu nhánh lỗi", {"flows.md": GOOD["flows.md"].replace("Không có: chỉ đọc", "")}, "flows"),
    ("màn mồ côi", {"screens.md": GOOD["screens.md"] + "| S-3 | Cài đặt | Chủ | F-2 | mockup-dat-lich.html |\n"}, "screens"),
    ("màn chưa có file mockup", {"screens.md": GOOD["screens.md"].replace("mockup-lich-ngay", "mockup-khong-co")}, "screens"),
    ("vai trò không có trên màn", {"requirements.md": GOOD["requirements.md"].replace("| Chủ | S-2 |", "| Chủ, Lễ tân | S-2 |")}, "vai trò"),
    ("CRUD còn ô trống", {"data.md": GOOD["data.md"].replace("| KHÔNG: chỉ huỷ |", "| |")}, "data"),
    ("trạng thái trỏ tới trạng thái không có", {"data.md": GOOD["data.md"].replace("Đã huỷ, Hoàn thành", "Đã huỷ, Đang làm")}, "data"),
]
for desc, ov, item in cases:
    code, rows = run(fresh(ov))
    check(f"{desc} -> thiếu", (code, bad(rows, item)), (1, True))

code, rows = run(fresh(drop=("screens.md",)))
check("không có screens.md -> thiếu", (code, bad(rows, "screens")), (1, True))
code, rows = run(fresh({"APP.md": GOOD["APP.md"].replace("APPROVED", "TODO")}), "--gate")
check("--gate: owner chưa duyệt -> thiếu", (code, bad(rows, "APP.md")), (1, True))
check("không --gate: bỏ qua APP.md", run(fresh({"APP.md": "- Owner duyệt: TODO\n"}))[0], 0)

# ---- responsive: wireframe có tab Mobile ----
MOB = '<button data-s="mobile">Mobile</button>'
RESP = {"intake.md": GOOD["intake.md"] + "- Responsive: CÓ (375 768 1280)\n"}
code, rows = run(fresh(RESP))
check("responsive CÓ, wireframe thiếu tab Mobile -> thiếu", (code, bad(rows, "responsive")), (1, True))
code, rows = run(fresh({**RESP, "design/mockup-dat-lich.html": MOB, "design/mockup-lich-ngay.html": MOB}))
check("responsive CÓ, mọi wireframe có tab Mobile -> đạt", code, 0)
code, rows = run(fresh({**RESP, "design/mockup-dat-lich.html": MOB}))
check("responsive CÓ, 1 màn thiếu tab Mobile -> thiếu", (code, bad(rows, "responsive")), (1, True))
code, rows = run(fresh({"intake.md": GOOD["intake.md"] + "- Responsive: KHÔNG (chỉ máy tính)\n"}))
check("responsive KHÔNG -> không đòi tab Mobile", (code, "responsive: wireframe có tab Mobile" in rows), (0, False))
vp = fresh()
open(os.path.join(vp, ".claude", "agent-team.config"), "a").write('VIEWPORTS="375 1280"\n')
code, rows = run(vp)
check("config VIEWPORTS có 375 -> đòi tab Mobile", (code, bad(rows, "responsive")), (1, True))

# ---- SPEC.md ----
root = fresh({"APP.md": "# Tiệm tóc\n" + GOOD["APP.md"] + "\n## Module\n| M | Module |\n|---|---|\n| M-0 | Khung |\n"})
spec = os.path.join(root, "docs", "product", "SPEC.md")
code, rows = run(root, "--spec-check")
check("--spec-check khi chưa có SPEC -> thiếu", (code, bad(rows, "SPEC")), (1, True))
code, rows = run(root, "--spec", "--spec-check")
check("--spec sinh SPEC, --spec-check đạt", (code, os.path.isfile(spec)), (0, True))
text = open(spec, encoding="utf-8").read()
check("SPEC có tên app", text.startswith("# SPEC: Tiệm tóc"), True)
check("SPEC có truy vết B-1 → R-1 → S-1", "| B-1: khách đặt lịch online | R-1 | S-1 |" in text, True)
check("SPEC có link wireframe", "[mockup-dat-lich.html](design/mockup-dat-lich.html)" in text, True)
check("SPEC bỏ dòng hướng dẫn >", "\n>" not in text.split("\n", 3)[3], True)
check("SPEC có bảng module", "| M-0 | Khung |" in text, True)
write_product(root, {"requirements.md": GOOD["requirements.md"].replace("Khách đặt lịch", "Khách đặt lịch nhanh")})
code, rows = run(root, "--spec-check")
check("sửa tài liệu sau khi sinh SPEC -> SPEC cũ", (code, bad(rows, "SPEC")), (1, True))
check("chạy lại --spec -> đạt", run(root, "--spec", "--spec-check")[0], 0)
root2 = fresh({"brief.md": GOOD["brief.md"] + "- B-3: báo cáo doanh thu\n"})
run(root2, "--spec")
check("SPEC đánh dấu ý owner chưa có yêu cầu", "| B-3: báo cáo doanh thu | **CHƯA CÓ** |" in open(
    os.path.join(root2, "docs", "product", "SPEC.md"), encoding="utf-8").read(), True)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
