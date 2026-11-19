#!/usr/bin/env python3
"""owner-form - form gửi owner chốt logic (App Mode). Không cần thư viện ngoài.

Dùng (Lead chạy, trong project):
  owner-form.py build  [thư mục project]          → docs/product/owner-form-<n>.xlsx
  owner-form.py import <file .xlsx|.csv> [project] → ghi câu trả lời vào questions.md, defaults.md

Form: tên app + 1 bảng 4 cột: # · Câu hỏi · Đề xuất của team · Owner duyệt / góp ý (ô trống).
Owner ghi "OK" (duyệt), "không" (không đồng ý / không cần), hoặc góp ý. Mã câu nằm ở cột E (ẩn).
Mở được bằng Excel, Numbers, Google Sheet (tải lên). Exit 0 = xong, 1 = lỗi dữ liệu, 2 = chưa có docs/product.
"""
import csv
import importlib.util
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("gap_check", os.path.join(HERE, "gap-check.py"))
gc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gc)

P = "docs/product"
HEAD = ["#", "Câu hỏi", "Đề xuất của team", "Owner duyệt / góp ý", "Mã"]
OK_WORDS = {"ok", "oke", "okay", "đồng ý", "duyệt", "được", "đúng", "yes", "y", "✓", "v"}
NO_WORDS = {"không", "ko", "k", "no", "không đồng ý", "không duyệt", "không cần", "bỏ", "x"}


# ---------- đọc / sửa bảng markdown ----------

def md_cell(v):
    return (v or "").replace("|", "/").replace("\r", "").replace("\n", "<br>").strip()


def update_table(text, id_prefix, need, updates):
    """Sửa ô trong bảng đầu tiên có đủ cột `need`. updates: {mã: {tiền tố cột: giá trị}}."""
    lines, out, i = text.split("\n"), [], 0
    done = False
    while i < len(lines):
        ln = lines[i]
        if not done and ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [gc.clean(h).lower() for h in ln.strip().strip("|").split("|")]
            idx = {p: next((k for k, h in enumerate(head) if h.startswith(p)), None) for p in need}
            if None not in idx.values():
                done = True
                out += [ln, lines[i + 1]]
                i += 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                    cells += [""] * (len(head) - len(cells))
                    rid = gc.clean(cells[idx[id_prefix]])
                    for col, val in updates.get(rid, {}).items():
                        cells[idx[col]] = md_cell(val)
                    out.append("| " + " | ".join(cells) + " |")
                    i += 1
                continue
        out.append(ln)
        i += 1
    return "\n".join(out)


def patch(path, id_prefix, need, updates):
    """Đọc xong rồi mới ghi (open 'w' trước sẽ xoá trắng file)."""
    text = update_table(gc.read_raw(path) or "", id_prefix, need, updates)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def app_name(root):
    t = gc.read_raw(os.path.join(root, P, "APP.md")) or ""
    name = next((ln[2:].strip() for ln in t.splitlines() if ln.startswith("# ")), "")
    return "App" if not name or name.startswith("<") else name


def owner_rows(root):
    """(câu hỏi cho owner, mặc định chưa chốt, lỗi). Câu CAO lên trước."""
    errs, qs, ds = [], [], []
    qm, qrows = gc.table(gc.read(root, "questions.md") or "", "q", "câu hỏi", "đề xuất", "vì sao", "mức", "ai trả lời", "trạng thái")
    if not qm:
        errs.append("questions.md thiếu cột: Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái (bản cũ: copy lại templates/product/questions.md)")
    for r in qrows if qm else []:
        q = gc.clean(r[qm["q"]])
        if not q or gc.first_word(r[qm["ai trả lời"]]) != "OWNER":
            continue
        if gc.clean(r[qm["trạng thái"]]).upper() not in ("MỞ", "CHỜ OWNER"):
            continue
        if gc.empty(r[qm["đề xuất"]]):
            errs.append(f"{q} chưa có Đề xuất của team")
            continue
        why = gc.clean(r[qm["vì sao"]])
        sug = gc.clean(r[qm["đề xuất"]]) + (f"\n{why}" if why and not gc.empty(why) else "")
        qs.append((q, gc.clean(r[qm["câu hỏi"]]), sug, gc.clean(r[qm["mức"]]).upper() == "CAO"))
    qs.sort(key=lambda x: not x[3])
    dm, drows = gc.table(gc.read(root, "defaults.md") or "", "d", "mục", "đề xuất", "owner chọn")
    for r in drows if dm else []:
        d = gc.clean(r[dm["d"]])
        if d and gc.clean(r[dm["owner chọn"]]).upper() in ("", "CHƯA", "CHỜ OWNER", "TODO"):
            if gc.empty(r[dm["đề xuất"]]):
                errs.append(f"{d} chưa có Đề xuất mặc định")
                continue
            ds.append((d, gc.clean(r[dm["mục"]]), gc.clean(r[dm["đề xuất"]]), False))
    return qs, ds, errs


# ---------- ghi / đọc .xlsx (OOXML tối thiểu) ----------

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="14"/><name val="Calibri"/></font></fonts>
<fills count="4"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFFBE6"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>
<border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="5"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="0" fillId="3" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1" applyProtection="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs>
</styleSheet>"""
WIDTHS = [5, 45, 55, 40, 8]


def _c(ref, val, style):
    if isinstance(val, int):
        return f'<c r="{ref}" s="{style}"><v>{val}</v></c>'
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(val)}</t></is></c>'


def _height(cells):
    """Ước chiều cao dòng (Excel không tự giãn dòng có chữ xuống dòng khi mở file)."""
    lines = max(sum(max(1, -(-len(p) * 11 // (w * 10))) for p in str(v).split("\n")) for v, w in zip(cells, WIDTHS))
    return max(30, 16 * lines)


def write_xlsx(path, title, rows):
    xml = [_row_xml(1, [_c("A1", title, 1)], 24)]
    xml.append(_row_xml(2, [_c(f"{'ABCDE'[k]}2", h, 2) for k, h in enumerate(HEAD)], 20))
    for n, (rid, q, sug, _cao) in enumerate(rows, 1):
        r = n + 2
        vals = [n, q, sug, "", rid]
        xml.append(_row_xml(r, [_c(f"{'ABCDE'[k]}{r}", v, 4 if k == 3 else 3) for k, v in enumerate(vals)], _height(vals)))
    hidden = ' hidden="1"'  # cột E (mã câu) ẩn với owner
    cols = "".join(f'<col min="{k + 1}" max="{k + 1}" width="{w}" customWidth="1"{hidden if k == 4 else ""}/>'
                   for k, w in enumerate(WIDTHS))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetViews><sheetView workbookViewId="0"><pane ySplit="2" topLeftCell="A3" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
             f'<cols>{cols}</cols><sheetData>{"".join(xml)}</sheetData></worksheet>')
    ns = "http://schemas.openxmlformats.org"
    files = {
        "[Content_Types].xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="{ns}/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>',
        "_rels/.rels": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{ns}/spreadsheetml/2006/main" '
        f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets><sheet name="Owner" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        f'<Relationship Id="rId2" Type="{ns}/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
        "xl/styles.xml": STYLES,
        "xl/worksheets/sheet1.xml": sheet,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def _row_xml(r, cells, ht):
    return f'<row r="{r}" ht="{ht}" customHeight="1">{"".join(cells)}</row>'


def read_xlsx(path):
    """[{cột: giá trị}] của sheet đầu tiên (hiểu cả sharedStrings của Excel / Google Sheet)."""
    m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{m}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{m}t")))
        sheet = sorted(n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n))[0]
        rows = []
        for row in ET.fromstring(z.read(sheet)).iter(f"{m}row"):
            cur = {}
            for c in row.iter(f"{m}c"):
                col = re.match(r"[A-Z]+", c.get("r", "")).group(0)
                t, v = c.get("t"), c.find(f"{m}v")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(f"{m}t"))
                else:
                    val = v.text if v is not None else ""
                cur[col] = (val or "").strip()
            rows.append(cur)
    return rows


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{"ABCDE"[k]: (v or "").strip() for k, v in enumerate(r[:5])} for r in csv.reader(f)]


# ---------- lệnh ----------

def verdict(text):
    t = re.sub(r"[.!\s]+$", "", text.strip().lower())
    return "ok" if t in OK_WORDS else "no" if t in NO_WORDS else "own"


def cmd_build(root):
    qs, ds, errs = owner_rows(root)
    if errs:
        sys.stderr.write("owner-form: chưa gửi được, sửa trước:\n" + "\n".join(f"  - {e}" for e in errs) + "\n")
        return 1
    rows = qs + ds
    if not rows:
        print("Không có câu nào cần owner trả lời (OWNER + MỞ / CHỜ OWNER, mặc định CHƯA).")
        return 0
    n = 1 + len([f for f in os.listdir(os.path.join(root, P)) if re.match(r"owner-form-\d+\.xlsx$", f)])
    out = os.path.join(root, P, f"owner-form-{n}.xlsx")
    write_xlsx(out, app_name(root), rows)
    qp, dp = os.path.join(root, P, "questions.md"), os.path.join(root, P, "defaults.md")
    if qs:
        patch(qp, "q", ["q", "trạng thái"], {q[0]: {"trạng thái": "CHỜ OWNER"} for q in qs})
    if ds:
        patch(dp, "d", ["d", "owner chọn"], {d[0]: {"owner chọn": "CHỜ OWNER"} for d in ds})
    print(f"{os.path.relpath(out, root)}: {len(qs)} câu hỏi ({sum(q[3] for q in qs)} mức CAO) + {len(ds)} mặc định. Gửi file cho owner.")
    return 0


def cmd_import(root, path):
    rows = read_xlsx(path) if path.lower().endswith(".xlsx") else read_csv(path)
    hdr = next((k for k, r in enumerate(rows) if gc.clean(r.get("B", "")).lower().startswith("câu hỏi")), None)
    if hdr is None:
        sys.stderr.write("owner-form: không thấy dòng tiêu đề 'Câu hỏi' trong file\n")
        return 1
    qp, dp = os.path.join(root, P, "questions.md"), os.path.join(root, P, "defaults.md")
    qm, qrows = gc.table(gc.read(root, "questions.md") or "", "q", "câu hỏi", "đề xuất")
    dm, drows = gc.table(gc.read(root, "defaults.md") or "", "d", "mục", "đề xuất")
    by_text = {gc.clean(r[qm["câu hỏi"]]): gc.clean(r[qm["q"]]) for r in qrows} if qm else {}
    by_text.update({gc.clean(r[dm["mục"]]): gc.clean(r[dm["d"]]) for r in drows} if dm else {})
    sug = {gc.clean(r[qm["q"]]): gc.clean(r[qm["đề xuất"]]) for r in qrows} if qm else {}
    qu, du, stat, blank, again = {}, {}, {"ok": 0, "no": 0, "own": 0}, [], []
    for r in rows[hdr + 1:]:
        rid = gc.clean(r.get("E", "")) or by_text.get(gc.clean(r.get("B", "")), "")
        ans = r.get("D", "").strip()
        if not rid:
            continue
        if not ans:
            blank.append(rid)
            continue
        v = verdict(ans)
        stat[v] += 1
        if rid.startswith("Q-"):
            qu[rid] = {"ok": {"trạng thái": "ĐÃ TRẢ LỜI", "trả lời": f"Owner OK: {sug.get(rid, '')}"},
                       "no": {"trạng thái": "MỞ", "trả lời": "Owner không đồng ý đề xuất, BA đề xuất lại"},
                       "own": {"trạng thái": "ĐÃ TRẢ LỜI", "trả lời": f"Owner: {ans}"}}[v]
            if v == "no":
                again.append(rid)
        elif rid.startswith("D-"):
            du[rid] = {"ok": {"owner chọn": "GIỮ"}, "no": {"owner chọn": "BỎ"},
                       "own": {"owner chọn": "KHÁC", "ghi chú": ans}}[v]
    if qu:
        patch(qp, "q", ["q", "trạng thái", "trả lời"], qu)
    if du:
        patch(dp, "d", ["d", "owner chọn", "ghi chú"], du)
    print(f"Đã nhập: {stat['ok']} OK, {stat['own']} góp ý, {stat['no']} không đồng ý / không cần, {len(blank)} để trống.")
    if again:
        print(f"BA đề xuất lại (lượt sau): {', '.join(again)}")
    if blank:
        print(f"Owner chưa trả lời (vẫn CHỜ OWNER): {', '.join(blank)}")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in ("build", "import") or (args[0] == "import" and len(args) < 2):
        sys.stderr.write(__doc__)
        return 2
    root = gc.find_root(args[2] if args[0] == "import" and len(args) > 2 else (args[1] if args[0] == "build" and len(args) > 1 else os.getcwd()))
    if not root or not os.path.isdir(os.path.join(root, P)):
        sys.stderr.write(f"owner-form: không thấy .claude/agent-team.config hoặc {P}/\n")
        return 2
    return cmd_build(root) if args[0] == "build" else cmd_import(root, args[1])


if __name__ == "__main__":
    sys.exit(main())
