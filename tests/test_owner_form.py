#!/usr/bin/env python3
"""Test owner-form.py: python3 tests/test_owner_form.py"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "plugins", "agent-team", "scripts", "owner-form.py")
GAP = os.path.join(HERE, "..", "plugins", "agent-team", "scripts", "gap-check.py")
spec = importlib.util.spec_from_file_location("owner_form", SCRIPT)
of = importlib.util.module_from_spec(spec)
spec.loader.exec_module(of)
fail = total = 0


def check(desc, got, exp):
    global fail, total
    total += 1
    fail += got != exp
    print(f"{'PASS' if got == exp else 'FAIL'}  {desc}  (expect {exp!r}, got {got!r})")


def run(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


QH = "| Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái | Trả lời | Nhóm | Màn |\n|---|---|---|---|---|---|---|---|---|---|\n"
DH = "| D | Mục | Đề xuất mặc định | Owner chọn | Ghi chú |\n|---|---|---|---|---|\n"
QUESTIONS = QH + (
    "| Q-1 | Khách muốn huỷ lịch thì sao? | Cho huỷ trước 2 giờ | Giữ chỗ cho khách khác | THẤP | OWNER | MỞ | | 3. F-1 Đặt lịch | S-1 |\n"
    "| Q-2 | Khách không đến (no-show)? | Quá 3 lần thì phải đặt cọc | Khách bỏ lịch làm thợ ngồi không | CAO | OWNER | MỞ | | 3. F-1 Đặt lịch | S-1 |\n"
    "| Q-3 | Hosting ở đâu? | VPS | | THẤP | DEV | MỞ | | | |\n"
    "| Q-4 | Khách chọn thợ? | Được chọn thợ | | CAO | OWNER | ĐÃ TRẢ LỜI | Owner OK | 2. Vai trò | |\n"
    "| Q-5 | Ai dùng app? | Chủ salon + khách | Biết ai cần màn nào | THẤP | OWNER | MỞ | | 1. Tổng quan | |\n")
SCREENS = "| S | Màn | Vai trò | Flow | Mockup |\n|---|---|---|---|---|\n| S-1 | Đặt lịch | Khách | F-1 | mockup-dat-lich.html |\n"
FLOWS = "## F-1: Khách đặt lịch\n"
DEFAULTS = DH + (
    "| D-1 | Khách vãng lai? | Lễ tân tạo lịch tại quầy | CHƯA | |\n"
    "| D-2 | Lưu lịch sử khách? | Ghi chú từng lần làm | CHƯA | |\n"
    "| D-3 | Dùng trên điện thoại? | Co giãn | GIỮ | |\n")


def project(questions=QUESTIONS, defaults=DEFAULTS, app="# Salon Tóc Mây\n- Debate: DONE\n- Challenger: DONE\n"):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, ".claude"))
    open(os.path.join(root, ".claude", "agent-team.config"), "w").write("")
    pd = os.path.join(root, "docs", "product")
    os.makedirs(os.path.join(pd, "design"))
    for name, text in {"APP.md": app, "questions.md": "# Sổ\n\n" + questions, "defaults.md": "# Mặc định\n\n" + defaults,
                       "screens.md": SCREENS, "flows.md": FLOWS, "design/mockup-dat-lich.html": "<title>Đặt lịch</title>"}.items():
        open(os.path.join(pd, name), "w", encoding="utf-8").write(text)
    return root


def doc(root, name):
    return open(os.path.join(root, "docs", "product", name), encoding="utf-8").read()


def row_of(text, rid):
    return next(ln for ln in text.splitlines() if ln.startswith(f"| {rid} "))


def section(rows, name):
    """Các dòng dữ liệu của mục name (A. Owner / B. Dev)."""
    k = next(i for i, r in enumerate(rows) if (r.get("A") or "").startswith(name))
    out = []
    for r in rows[k + 2:]:
        if (r.get("A") or "")[:2] in ("A.", "B."):
            break
        if (r.get("F") or "").startswith(("Q-", "D-")):
            out.append(r)
    return out


def excel_like(path, rows):
    """Ghi lại file như Excel lưu: chữ nằm trong sharedStrings (t="s")."""
    strings, cells_xml = [], []
    for r, row in enumerate(rows, 1):
        cells = []
        for col, val in sorted(row.items()):
            if val == "":
                continue
            strings.append(val)
            cells.append(f'<c r="{col}{r}" t="s"><v>{len(strings) - 1}</v></c>')
        cells_xml.append(f'<row r="{r}">{"".join(cells)}</row>')
    m = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet {m}><sheetData>{"".join(cells_xml)}</sheetData></worksheet>')
        z.writestr("xl/sharedStrings.xml", f'<sst {m}>' + "".join(f"<si><t>{escape(s)}</t></si>" for s in strings) + "</sst>")


# ---- build ----
root = project()
code, out = run("build", root)
xlsx = os.path.join(root, "docs", "product", "owner-form-1.xlsx")
check("build thành công", code, 0)
check("có file owner-form-1.xlsx", os.path.isfile(xlsx), True)
rows = of.read_xlsx(xlsx)
check("dòng 1 = tên app", rows[0].get("A"), "Salon Tóc Mây")
check("dòng 3 = mục A. Owner", rows[1].get("A"), "A. Owner: nghiệp vụ")
check("tiêu đề mục A = 5 cột + mã", [rows[2].get(c) for c in "ABCDEF"], ["#", "Câu hỏi", "Màn / mockup", "Đề xuất của team", "Owner duyệt / góp ý", "Mã"])
data = section(rows, "A. Owner")
dev = section(rows, "B. Dev")
hdev = rows[rows.index(dev[0]) - 2]
check("mục B. Dev có tiêu đề riêng", [hdev.get(c) for c in "ABCDEF"], ["#", "Câu hỏi", "Màn / mockup", "Đề xuất của team", "Dev duyệt / góp ý", "Mã"])
check("mục B chỉ có câu DEV", [r.get("F") for r in dev], ["Q-3"])
check("mục B đánh số lại từ 1", dev[0].get("A"), "1")
check("xếp theo hành trình: nhóm 1 → 3 → mặc định, giữ thứ tự trong nhóm", [r.get("F") for r in data], ["Q-5", "Q-1", "Q-2", "D-1", "D-2"])
k0 = next(i for i, r in enumerate(rows) if r.get("A") == "A. Owner: nghiệp vụ")
check("mỗi nhóm có 1 dòng tiêu đề", [r.get("B") for r in rows[k0:] if not r.get("A") and r.get("B")][:3], ["1. Tổng quan", "3. F-1 Đặt lịch", "Mặc định"])
check("cột Màn = tên màn + file mockup", data[1].get("C"), "S-1 Đặt lịch\ndesign/mockup-dat-lich.html")
check("đề xuất kèm giải thích", data[1].get("D"), "Đề xuất: Cho huỷ trước 2 giờ\nGiải thích: Giữ chỗ cho khách khác")
check("cột owner để trống", [r.get("E", "") for r in data], ["", "", "", "", ""])
check("số thứ tự", [r.get("A") for r in data], ["1", "2", "3", "4", "5"])
with zipfile.ZipFile(xlsx) as z:
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
check("cột F (mã) bị ẩn với owner", 'min="6" max="6" width="8" customWidth="1" hidden="1"' in sheet, True)
check("có đủ file OOXML", sorted(zipfile.ZipFile(xlsx).namelist()) == sorted(
    ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/worksheets/sheet1.xml"]), True)
q = doc(root, "questions.md")
check("Q-1, Q-2 chuyển CHỜ OWNER", ("CHỜ OWNER" in row_of(q, "Q-1"), "CHỜ OWNER" in row_of(q, "Q-2")), (True, True))
check("câu DEV chuyển CHỜ DEV", "| CHỜ DEV |" in row_of(q, "Q-3"), True)
d = doc(root, "defaults.md")
check("D-1, D-2 chuyển CHỜ OWNER, D-3 giữ GIỮ", ("CHỜ OWNER" in row_of(d, "D-1"), "CHỜ OWNER" in row_of(d, "D-2"), "GIỮ" in row_of(d, "D-3")), (True, True, True))

# ---- import từ file Excel đã lưu (sharedStrings) ----
filled = [dict(r) for r in rows]
answers = {"Q-2": "Cọc 50k cho lịch cuối tuần | trừ khách quen", "Q-1": "Ok.", "D-1": "không cần", "D-2": "", "Q-3": "Ubuntu nội bộ"}
for r in filled:
    if r.get("F") in answers:
        r["E"] = answers[r["F"]]
back = os.path.join(root, "tra-loi.xlsx")
excel_like(back, filled)
code, out = run("import", back, root)
check("import thành công", code, 0)
check("báo số liệu", "1 OK, 2 góp ý, 1 không đồng ý / không cần, 2 để trống" in out, True)
check("báo dòng owner bỏ trống", "D-2" in out.split("Chưa trả lời")[-1], True)
q = doc(root, "questions.md")
check("Q-1 OK → ĐÃ TRẢ LỜI + chép đề xuất", ("ĐÃ TRẢ LỜI" in row_of(q, "Q-1"), "Owner OK: Cho huỷ trước 2 giờ" in row_of(q, "Q-1")), (True, True))
check("Q-2 góp ý → ĐÃ TRẢ LỜI nguyên văn owner (| đổi thành /)", "Owner: Cọc 50k cho lịch cuối tuần / trừ khách quen" in row_of(q, "Q-2"), True)
check("Q-3 dev trả lời → ĐÃ TRẢ LỜI ghi 'Dev:'", ("ĐÃ TRẢ LỜI" in row_of(q, "Q-3"), "Dev: Ubuntu nội bộ" in row_of(q, "Q-3")), (True, True))
check("dòng tiêu đề mục không bị đếm", "Mã" not in out, True)
check("bảng không vỡ cột sau khi ghi", row_of(q, "Q-2").count("|"), 11)
d = doc(root, "defaults.md")
check("D-1 'không cần' → BỎ", "| BỎ |" in row_of(d, "D-1"), True)
check("D-2 để trống → vẫn CHỜ OWNER", "CHỜ OWNER" in row_of(d, "D-2"), True)

# ---- lượt 2: chỉ còn câu chưa xong ----
root2 = project()
run("build", root2)
csvp = os.path.join(root2, "tra-loi.csv")
open(csvp, "w", encoding="utf-8-sig").write(
    "Salon Tóc Mây\n#,Câu hỏi,Đề xuất của team,Owner duyệt / góp ý,Mã\n"
    "1,Khách không đến (no-show)?,Quá 3 lần thì phải đặt cọc,không đồng ý,Q-2\n"
    "2,Khách muốn huỷ lịch thì sao?,Cho huỷ trước 2 giờ,đồng ý,Q-1\n"
    "3,Khách vãng lai?,Lễ tân tạo lịch tại quầy,Cho khách tự đặt bằng QR tại quầy,D-1\n"
    "4,Lưu lịch sử khách?,Ghi chú từng lần làm,OK,D-2\n")
code, out = run("import", csvp, root2)
check("import CSV (Google Sheet tải về)", code, 0)
check("báo câu phải đề xuất lại", "Đề xuất lại (lượt sau): Q-2" in out, True)
check("owner không đồng ý → ghi BA đề xuất lại", "BA đề xuất lại" in row_of(doc(root2, "questions.md"), "Q-2"), True)
q, d = doc(root2, "questions.md"), doc(root2, "defaults.md")
check("Q-2 không đồng ý → MỞ", "| MỞ |" in row_of(q, "Q-2"), True)
check("D-1 góp ý → KHÁC + ghi chú", ("KHÁC" in row_of(d, "D-1"), "QR tại quầy" in row_of(d, "D-1")), (True, True))
code, out = run("build", root2)
rows2 = of.read_xlsx(os.path.join(root2, "docs", "product", "owner-form-2.xlsx"))
check("lượt 2: mục A chỉ Q-2 + Q-5 chưa trả lời, mục B vẫn Q-3", ([r.get("F") for r in section(rows2, "A. Owner")], [r.get("F") for r in section(rows2, "B. Dev")]), (["Q-5", "Q-2"], ["Q-3"]))

# ---- mất cột mã: tìm theo câu hỏi ----
root3 = project()
run("build", root3)
csv3 = os.path.join(root3, "a.csv")
open(csv3, "w", encoding="utf-8").write("#,Câu hỏi,Đề xuất của team,Owner duyệt / góp ý\n1,Khách muốn huỷ lịch thì sao?,x,OK\n")
run("import", csv3, root3)
check("không có cột mã → khớp theo câu hỏi", "ĐÃ TRẢ LỜI" in row_of(doc(root3, "questions.md"), "Q-1"), True)

# ---- lỗi dữ liệu ----
bad = project(questions=QH + "| Q-1 | Có cọc không? | | | CAO | OWNER | MỞ | | 3. F-1 | S-1 |\n")
code, out = run("build", bad)
check("câu OWNER thiếu đề xuất → không sinh form", (code, "chưa có Đề xuất" in out, os.path.isfile(os.path.join(bad, "docs/product/owner-form-1.xlsx"))), (1, True, False))
nowhy = project(questions=QH + "| Q-1 | Khách muốn huỷ lịch thì sao? | Cho huỷ trước 2 giờ | | CAO | OWNER | MỞ | | 3. F-1 | S-1 |\n")
code, out = run("build", nowhy)
check("câu OWNER thiếu giải thích → không sinh form", (code, "chưa có Vì sao" in out), (1, True))
for desc, text in (("mã nội bộ", "Theo R-3 khách huỷ thì sao?"), ("từ kỹ thuật", "Khách huỷ thì đổi status lịch?")):
    jr = project(questions=QH + f"| Q-1 | {text} | Cho huỷ trước 2 giờ | Giữ chỗ | CAO | OWNER | MỞ | | 3. F-1 | S-1 |\n")
    code, out = run("build", jr)
    check(f"câu OWNER có {desc} → không sinh form", (code, "owner không hiểu" in out), (1, True))
LONGQ = ("Anh Nam phòng Kế toán đã hoàn thành 6 trong 10 mục tiêu năm 2027, tài liệu nói cây lên cấp khi đi xong lộ trình "
         "nghề nghiệp nhưng lộ trình để giai đoạn 2, vậy cây của anh Nam có lên cấp không?")
lq = project(questions=QH + f"| Q-1 | {LONGQ} | Lên cấp theo số mục tiêu | Lộ trình chưa có | CAO | OWNER | MỞ | | 3. F-1 | S-1 |\n")
code, out = run("build", lq)
check("câu OWNER quá dài (kể chuyện) → không sinh form", (code, "quá dài" in out and "Câu hỏi" in out), (1, True))
dev_tech = project(questions=QH + "| Q-1 | API dùng REST? | REST + JSON | | THẤP | DEV | MỞ | | | |\n| Q-2 | Luồng đặt lịch đúng chưa? | Đúng | | THẤP | OWNER | ĐÃ TRẢ LỜI | OK | 3. F-1 | S-1 |\n", defaults=DH)
check("câu DEV được dùng từ kỹ thuật", run("build", dev_tech)[0], 0)
old = project(questions="| Q | Câu hỏi | Mức | Trạng thái | Trả lời |\n|---|---|---|---|---|\n| Q-1 | x | CAO | MỞ | |\n")
dv = project(questions=QH + "| Q-1 | SMTP? | | | THẤP | DEV | MỞ | |\n")
check("câu DEV thiếu đề xuất → không sinh form", run("build", dv)[0], 1)
only = project(questions=QH + "| Q-1 | SMTP? | Có | | THẤP | DEV | MỞ | | | |\n| Q-2 | Luồng đặt lịch đúng chưa? | Đúng | | THẤP | OWNER | ĐÃ TRẢ LỜI | OK | 3. F-1 | S-1 |\n", defaults=DH)
rows_o = of.read_xlsx(os.path.join(only, "docs/product/owner-form-1.xlsx")) if run("build", only)[0] == 0 else []
check("chỉ có câu DEV → bỏ mục A", ([r.get("A") for r in rows_o if (r.get("A") or "")[:2] in ("A.", "B.")]), ["B. Dev: kỹ thuật"])
check("questions.md bản cũ → báo copy template", "bản cũ" in run("build", old)[1], True)
none = project(questions=QH + "| Q-1 | Luồng đặt lịch? | Đúng | | THẤP | OWNER | ĐÃ TRẢ LỜI | OK | 3. F-1 | S-1 |\n", defaults=DH)
check("không có câu nào → báo, không sinh file", (run("build", none)[0], os.path.isfile(os.path.join(none, "docs/product/owner-form-1.xlsx"))), (0, False))
def refused(root, msg):
    code, out = run("build", root)
    return code, msg in out, os.path.isfile(os.path.join(root, "docs/product/owner-form-1.xlsx"))


check("Debate chưa DONE → không sinh form", refused(project(app="# S\n- Challenger: DONE\n"), "Debate chưa DONE"), (1, True, False))
check("Challenger chưa DONE → không sinh form", refused(project(app="# S\n- Debate: DONE\n"), "Challenger chưa DONE"), (1, True, False))
nomk = project()
os.remove(os.path.join(nomk, "docs/product/design/mockup-dat-lich.html"))
check("chưa có mockup → không sinh form", refused(nomk, "chưa có mockup"), (1, True, False))
check("câu OWNER thiếu Nhóm → không sinh form", refused(project(questions=QUESTIONS + "| Q-9 | X? | Y | | THẤP | OWNER | MỞ | | | |\n"), "Q-9 chưa có Nhóm"), (1, True, False))
check("câu trong luồng thiếu Màn → không sinh form", refused(project(questions=QUESTIONS + "| Q-9 | X? | Y | | THẤP | OWNER | MỞ | | 3. F-1 | |\n"), "Q-9 thuộc luồng nhưng chưa có Màn"), (1, True, False))
check("Màn trỏ tới màn không có mockup", refused(project(questions=QUESTIONS + "| Q-9 | X? | Y | | THẤP | OWNER | MỞ | | 3. F-1 | S-7 |\n"), "màn chưa có mockup: S-7"), (1, True, False))
nof = project()
open(os.path.join(nof, "docs/product/flows.md"), "a").write("## F-2: Chủ xem lịch\n")
check("luồng F-2 chưa có câu nào → không sinh form", refused(nof, "luồng F-2 chưa có câu"), (1, True, False))
check("chưa có docs/product → exit 2", run("build", tempfile.mkdtemp())[0], 2)

# ---- đọc chữ owner ----
for txt, exp in [("OK", "ok"), ("ok.", "ok"), ("Đồng ý", "ok"), ("duyệt", "ok"), ("Không", "no"), ("không cần", "no"), ("bỏ", "no"), ("Cọc 30%", "own")]:
    check(f"đọc '{txt}'", of.verdict(txt), exp)

# ---- gap-check với sổ câu hỏi mới ----
def gap(root):
    return subprocess.run([sys.executable, GAP, root], capture_output=True, text=True).stdout


g = gap(project(questions=QH + "| Q-1 | Cọc? | | | THẤP | OWNER | MỞ | | | |\n"))
check("gap-check: câu OWNER thiếu đề xuất", "Q-1 gửi owner nhưng chưa có Đề xuất" in g, True)
g = gap(project(questions=QH + "| Q-1 | Cọc? | Có | | CAO | OWNER | CHỜ OWNER | | | |\n"))
check("gap-check: câu CAO đang chờ owner", "Q-1 mức CAO đang chờ owner" in g, True)
g = gap(project(questions=QH + "| Q-1 | Cọc? | Có | | THẤP | OWNER | CHỜ OWNER | | | |\n"))
g = gap(project(questions=QH + "| Q-1 | SMTP? | Có | | THẤP | DEV | CHỜ DEV | | | |\n"))
check("gap-check: CHỜ DEV hợp lệ", "trạng thái 'CHỜ DEV'" in g, False)
g = gap(project(questions=QH + "| Q-1 | SMTP? | | | THẤP | DEV | MỞ | | | |\n"))
check("gap-check: câu DEV thiếu đề xuất", "Q-1 gửi dev nhưng chưa có Đề xuất" in g, True)
check("gap-check: CHỜ OWNER là trạng thái hợp lệ", "trạng thái 'CHỜ OWNER'" in g, False)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
