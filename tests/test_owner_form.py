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


QH = "| Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái | Trả lời |\n|---|---|---|---|---|---|---|---|\n"
DH = "| D | Mục | Đề xuất mặc định | Owner chọn | Ghi chú |\n|---|---|---|---|---|\n"
QUESTIONS = QH + (
    "| Q-1 | Khách muốn huỷ lịch thì sao? | Cho huỷ trước 2 giờ | Giữ chỗ cho khách khác | THẤP | OWNER | MỞ | |\n"
    "| Q-2 | Khách không đến (no-show)? | Quá 3 lần thì phải đặt cọc | | CAO | OWNER | MỞ | |\n"
    "| Q-3 | Hosting ở đâu? | VPS | | THẤP | DEV | MỞ | |\n"
    "| Q-4 | Khách chọn thợ? | Được chọn thợ | | CAO | OWNER | ĐÃ TRẢ LỜI | Owner OK |\n")
DEFAULTS = DH + (
    "| D-1 | Khách vãng lai? | Lễ tân tạo lịch tại quầy | CHƯA | |\n"
    "| D-2 | Lưu lịch sử khách? | Ghi chú từng lần làm | CHƯA | |\n"
    "| D-3 | Dùng trên điện thoại? | Co giãn | GIỮ | |\n")


def project(questions=QUESTIONS, defaults=DEFAULTS):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, ".claude"))
    open(os.path.join(root, ".claude", "agent-team.config"), "w").write("")
    pd = os.path.join(root, "docs", "product")
    os.makedirs(pd)
    for name, text in {"APP.md": "# Salon Tóc Mây\n", "questions.md": "# Sổ\n\n" + questions,
                       "defaults.md": "# Mặc định\n\n" + defaults}.items():
        open(os.path.join(pd, name), "w", encoding="utf-8").write(text)
    return root


def doc(root, name):
    return open(os.path.join(root, "docs", "product", name), encoding="utf-8").read()


def row_of(text, rid):
    return next(ln for ln in text.splitlines() if ln.startswith(f"| {rid} "))


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
check("dòng 2 = 4 cột + mã", [rows[1].get(c) for c in "ABCDE"], ["#", "Câu hỏi", "Đề xuất của team", "Owner duyệt / góp ý", "Mã"])
data = rows[2:]
check("chỉ câu OWNER chưa trả lời + mặc định CHƯA (4 dòng)", [r.get("E") for r in data], ["Q-2", "Q-1", "D-1", "D-2"])
check("câu CAO lên đầu", data[0].get("E"), "Q-2")
check("đề xuất kèm vì sao", data[1].get("C"), "Cho huỷ trước 2 giờ\nGiữ chỗ cho khách khác")
check("cột owner để trống", [r.get("D", "") for r in data], ["", "", "", ""])
check("số thứ tự", [r.get("A") for r in data], ["1", "2", "3", "4"])
with zipfile.ZipFile(xlsx) as z:
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
check("cột E (mã) bị ẩn với owner", 'min="5" max="5" width="8" customWidth="1" hidden="1"' in sheet, True)
check("có đủ file OOXML", sorted(zipfile.ZipFile(xlsx).namelist()) == sorted(
    ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/worksheets/sheet1.xml"]), True)
q = doc(root, "questions.md")
check("Q-1, Q-2 chuyển CHỜ OWNER", ("CHỜ OWNER" in row_of(q, "Q-1"), "CHỜ OWNER" in row_of(q, "Q-2")), (True, True))
check("câu DEV giữ nguyên MỞ", "| MỞ |" in row_of(q, "Q-3"), True)
d = doc(root, "defaults.md")
check("D-1, D-2 chuyển CHỜ OWNER, D-3 giữ GIỮ", ("CHỜ OWNER" in row_of(d, "D-1"), "CHỜ OWNER" in row_of(d, "D-2"), "GIỮ" in row_of(d, "D-3")), (True, True, True))

# ---- import từ file Excel đã lưu (sharedStrings) ----
filled = [dict(r) for r in rows]
answers = {"Q-2": "Cọc 50k cho lịch cuối tuần | trừ khách quen", "Q-1": "Ok.", "D-1": "không cần", "D-2": ""}
for r in filled:
    if r.get("E") in answers:
        r["D"] = answers[r["E"]]
back = os.path.join(root, "tra-loi.xlsx")
excel_like(back, filled)
code, out = run("import", back, root)
check("import thành công", code, 0)
check("báo số liệu", "1 OK, 1 góp ý, 1 không đồng ý / không cần, 1 để trống" in out, True)
check("báo dòng owner bỏ trống", "D-2" in out.split("chưa trả lời")[-1], True)
q = doc(root, "questions.md")
check("Q-1 OK → ĐÃ TRẢ LỜI + chép đề xuất", ("ĐÃ TRẢ LỜI" in row_of(q, "Q-1"), "Owner OK: Cho huỷ trước 2 giờ" in row_of(q, "Q-1")), (True, True))
check("Q-2 góp ý → ĐÃ TRẢ LỜI nguyên văn owner (| đổi thành /)", "Owner: Cọc 50k cho lịch cuối tuần / trừ khách quen" in row_of(q, "Q-2"), True)
check("bảng không vỡ cột sau khi ghi", row_of(q, "Q-2").count("|"), 9)
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
check("báo câu BA phải đề xuất lại", "BA đề xuất lại (lượt sau): Q-2" in out, True)
q, d = doc(root2, "questions.md"), doc(root2, "defaults.md")
check("Q-2 không đồng ý → MỞ", "| MỞ |" in row_of(q, "Q-2"), True)
check("D-1 góp ý → KHÁC + ghi chú", ("KHÁC" in row_of(d, "D-1"), "QR tại quầy" in row_of(d, "D-1")), (True, True))
code, out = run("build", root2)
rows2 = of.read_xlsx(os.path.join(root2, "docs", "product", "owner-form-2.xlsx"))
check("lượt 2 chỉ gửi Q-2 (sau khi BA sửa đề xuất)", [r.get("E") for r in rows2[2:]], ["Q-2"])

# ---- mất cột mã: tìm theo câu hỏi ----
root3 = project()
run("build", root3)
csv3 = os.path.join(root3, "a.csv")
open(csv3, "w", encoding="utf-8").write("#,Câu hỏi,Đề xuất của team,Owner duyệt / góp ý\n1,Khách muốn huỷ lịch thì sao?,x,OK\n")
run("import", csv3, root3)
check("không có cột mã → khớp theo câu hỏi", "ĐÃ TRẢ LỜI" in row_of(doc(root3, "questions.md"), "Q-1"), True)

# ---- lỗi dữ liệu ----
bad = project(questions=QH + "| Q-1 | Có cọc không? | | | CAO | OWNER | MỞ | |\n")
code, out = run("build", bad)
check("câu OWNER thiếu đề xuất → không sinh form", (code, "chưa có Đề xuất" in out, os.path.isfile(os.path.join(bad, "docs/product/owner-form-1.xlsx"))), (1, True, False))
old = project(questions="| Q | Câu hỏi | Mức | Trạng thái | Trả lời |\n|---|---|---|---|---|\n| Q-1 | x | CAO | MỞ | |\n")
check("questions.md bản cũ → báo copy template", "bản cũ" in run("build", old)[1], True)
none = project(questions=QH, defaults=DH)
check("không có câu nào → báo, không sinh file", (run("build", none)[0], os.path.isfile(os.path.join(none, "docs/product/owner-form-1.xlsx"))), (0, False))
check("chưa có docs/product → exit 2", run("build", tempfile.mkdtemp())[0], 2)

# ---- đọc chữ owner ----
for txt, exp in [("OK", "ok"), ("ok.", "ok"), ("Đồng ý", "ok"), ("duyệt", "ok"), ("Không", "no"), ("không cần", "no"), ("bỏ", "no"), ("Cọc 30%", "own")]:
    check(f"đọc '{txt}'", of.verdict(txt), exp)

# ---- gap-check với sổ câu hỏi mới ----
def gap(root):
    return subprocess.run([sys.executable, GAP, root], capture_output=True, text=True).stdout


g = gap(project(questions=QH + "| Q-1 | Cọc? | | | THẤP | OWNER | MỞ | |\n"))
check("gap-check: câu OWNER thiếu đề xuất", "Q-1 gửi owner nhưng chưa có Đề xuất" in g, True)
g = gap(project(questions=QH + "| Q-1 | Cọc? | Có | | CAO | OWNER | CHỜ OWNER | |\n"))
check("gap-check: câu CAO đang chờ owner", "Q-1 mức CAO đang chờ owner" in g, True)
g = gap(project(questions=QH + "| Q-1 | Cọc? | Có | | THẤP | OWNER | CHỜ OWNER | |\n"))
check("gap-check: CHỜ OWNER là trạng thái hợp lệ", "trạng thái 'CHỜ OWNER'" in g, False)

print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
