#!/usr/bin/env python3
"""owner-form - form hỏi owner + dev (App Mode). Không cần thư viện ngoài.

Dùng (Lead chạy, trong project):
  owner-form.py build  [thư mục project]          → docs/product/QnA-v<n>.xlsx
  owner-form.py import <file .xlsx|.csv> [project] → ghi câu trả lời vào questions.md, defaults.md
  --dir=<thư mục>: module mới trong app đang chạy (vd --dir=docs/product/modules/thanh-toan), cổng đọc ở MODULE.md

Form: tên app + 2 mục, mỗi mục 1 bảng: # · Câu hỏi · Màn / mockup · Đề xuất của team · <người> duyệt / góp ý (ô trống).
  A. Owner: nghiệp vụ (câu OWNER + mặc định)   B. Dev: kỹ thuật (câu DEV)
Dòng xếp theo cột Nhóm (hành trình: "1. Tổng quan", "3. F-1 Đặt lịch"...), mỗi nhóm 1 dòng tiêu đề.
Chỉ build khi APP.md có Debate: DONE + Challenger: DONE, có mockup, mọi luồng F-n có câu trong Nhóm.
Ghi "OK" (duyệt), "không" (không đồng ý / không cần), hoặc góp ý. Mã câu nằm ở cột F (ẩn).
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
INTERNAL_CODE_RE = re.compile(r"\b(?:AC|BR|[RFSQDPCGB])-\d+\b")
TECH_WORD_RE = re.compile(r"(?i)\b(api|endpoint|database|db|token|cache|role|status|record|crud|backend|frontend|server|json|query|id|bug|deploy)\b")
SECTIONS = [("OWNER", "A. Owner: nghiệp vụ", "Owner duyệt / góp ý"), ("DEV", "B. Dev: kỹ thuật", "Dev duyệt / góp ý")]
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
    t = gc.read_raw(os.path.join(root, P, gc.status_name(root))) or ""
    name = next((ln[2:].strip() for ln in t.splitlines() if ln.startswith("# ")), "")
    return "App" if not name or name.startswith("<") else name


def group_key(g):
    m = re.match(r"\s*(\d+)", g)
    return int(m.group(1)) if m else 99


def screen_map(root):
    """{S-n: "S-n Tên\ndesign/mockup.html"} của màn có file mockup thật."""
    m, rows = gc.table(gc.read(root, "screens.md") or "", "s", "màn", "mockup")
    out = {}
    for r in rows if m else []:
        s, mk = gc.clean(r[m["s"]]), gc.clean(r[m["mockup"]])
        if not s or gc.empty(mk):
            continue
        rel = mk if mk.startswith("design/") else f"design/{mk}"
        if os.path.isfile(os.path.join(root, P, rel)):
            out[s] = f"{s} {gc.clean(r[m['màn']])}\n{rel}"
    return out


def gates(root, qrows, screens):
    app = gc.fields(gc.read_raw(os.path.join(root, P, gc.status_name(root))) or "")
    errs = [f"{gc.status_name(root)} {k} chưa DONE ({why})" for k, why in
            (("Debate", "team chưa debate xong"), ("Challenger", "chưa săn gap trên nháp + mockup"))
            if gc.first_word(app.get(k, "")) != "DONE"]
    if not screens:
        errs.append("chưa có mockup (screens.md + design/mockup-*.html): vẽ A3b trước khi hỏi")
    groups = " ".join(gc.col(r, "nhóm") for r in qrows)
    flows = re.findall(r"(?m)^##\s+(F-\d+)\b", gc.read(root, "flows.md") or "")
    errs += [f"luồng {f} chưa có câu nào trong Nhóm (thêm câu xác nhận luồng)" for f in flows if f not in gc.ids(groups, "F")]
    return errs


def owner_jargon(text):
    """Mã nội bộ (R-1, AC-2...) và từ kỹ thuật mà owner không hiểu."""
    found = INTERNAL_CODE_RE.findall(text) + [w.lower() for w in TECH_WORD_RE.findall(text)]
    return sorted(set(found))


def form_rows(root):
    """({OWNER: [...], DEV: [...]} câu hỏi, mặc định chưa chốt, lỗi). Xếp theo Nhóm (hành trình), giữ thứ tự trong file."""
    errs, qs, ds = [], {"OWNER": [], "DEV": []}, []
    screens = screen_map(root)
    qm, qrows = gc.table(gc.read(root, "questions.md") or "", "q", "câu hỏi", "đề xuất", "vì sao", "mức", "ai trả lời", "trạng thái")
    if not qm:
        errs.append("questions.md thiếu cột: Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái | Trả lời | Nhóm | Màn (bản cũ: copy lại templates/product/questions.md)")
    errs += gates(root, qrows, screens)
    for r in qrows if qm else []:
        q = gc.clean(r[qm["q"]])
        who = gc.first_word(r[qm["ai trả lời"]])
        if not q or who not in qs:
            continue
        if gc.clean(r[qm["trạng thái"]]).upper() not in ("MỞ", "CHỜ OWNER", "CHỜ DEV"):
            continue
        if gc.empty(r[qm["đề xuất"]]):
            errs.append(f"{q} chưa có Đề xuất của team")
            continue
        group = gc.clean(gc.col(r, "nhóm"))
        man = gc.ids(gc.col(r, "màn"), "S")
        if who == "OWNER" and gc.empty(group):
            errs.append(f"{q} chưa có Nhóm (bước nào trong hành trình)")
            continue
        if who == "OWNER" and gc.ids(group, "F") and not man:
            errs.append(f"{q} thuộc luồng nhưng chưa có Màn (S-n)")
            continue
        if man - screens.keys():
            errs.append(f"{q} trỏ tới màn chưa có mockup: {', '.join(sorted(man - screens.keys()))}")
            continue
        why = gc.clean(r[qm["vì sao"]])
        if who == "OWNER":
            if gc.empty(why):
                errs.append(f"{q} chưa có Vì sao (giải thích cho owner: vì sao cần quyết, chọn khác thì sao)")
                continue
            long = [f"{name} {n} từ (tối đa {mx})" for name, txt, mx in (("Câu hỏi", r[qm["câu hỏi"]], 25), ("Đề xuất", r[qm["đề xuất"]], 40), ("Vì sao", why, 30))
                    if (n := len(gc.clean(txt).split())) > mx]
            if long:
                errs.append(f"{q} quá dài: {', '.join(long)}. Viết lại ngắn, hỏi thẳng quy tắc cần quyết, không kể chuyện (app.md mục 0b)")
                continue
            jargon = owner_jargon(" ".join((gc.clean(r[qm["câu hỏi"]]), gc.clean(r[qm["đề xuất"]]), why)))
            if jargon:
                errs.append(f"{q} có từ owner không hiểu: {', '.join(jargon)} (viết lại bằng lời thường)")
                continue
            sug = f"Đề xuất: {gc.clean(r[qm['đề xuất']])}\nGiải thích: {why}"
        else:
            sug = gc.clean(r[qm["đề xuất"]]) + (f"\n{why}" if why and not gc.empty(why) else "")
        qs[who].append((q, gc.clean(r[qm["câu hỏi"]]), "\n".join(screens[s] for s in sorted(man)), sug, group or "Kỹ thuật"))
    dm, drows = gc.table(gc.read(root, "defaults.md") or "", "d", "mục", "đề xuất", "owner chọn")
    for r in drows if dm else []:
        d = gc.clean(r[dm["d"]])
        if d and gc.clean(r[dm["owner chọn"]]).upper() in ("", "CHƯA", "CHỜ OWNER", "TODO"):
            if gc.empty(r[dm["đề xuất"]]):
                errs.append(f"{d} chưa có Đề xuất mặc định")
                continue
            ds.append((d, gc.clean(r[dm["mục"]]), "", gc.clean(r[dm["đề xuất"]]), gc.clean(gc.col(r, "nhóm")) or "Mặc định"))
    return qs, ds, errs


def by_group(rows):
    return sorted(rows, key=lambda x: group_key(x[4]))


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
WIDTHS = [5, 45, 30, 50, 40, 8]
COLS = "ABCDEF"


def _c(ref, val, style):
    if isinstance(val, int):
        return f'<c r="{ref}" s="{style}"><v>{val}</v></c>'
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(val)}</t></is></c>'


def _height(cells):
    """Ước chiều cao dòng (Excel không tự giãn dòng có chữ xuống dòng khi mở file)."""
    lines = max(sum(max(1, -(-len(p) * 11 // (w * 10))) for p in str(v).split("\n")) for v, w in zip(cells, WIDTHS))
    return max(30, 16 * lines)


def write_xlsx(path, title, sections):
    """sections: [(tên mục, tiêu đề cột trả lời, rows)]. Mục rỗng thì bỏ."""
    xml, r = [_row_xml(1, [_c("A1", title, 1)], 24)], 1
    for name, answer, rows in sections:
        if not rows:
            continue
        r += 2  # chừa 1 dòng trống
        xml.append(_row_xml(r, [_c(f"A{r}", name, 1)], 22))
        r += 1
        head = ["#", "Câu hỏi", "Màn / mockup", "Đề xuất của team", answer, "Mã"]
        xml.append(_row_xml(r, [_c(f"{COLS[k]}{r}", h, 2) for k, h in enumerate(head)], 20))
        group = None
        for n, (rid, q, man, sug, g) in enumerate(rows, 1):
            if g != group:
                group, r = g, r + 1
                xml.append(_row_xml(r, [_c(f"B{r}", g, 2)], 20))
            r += 1
            vals = [n, q, man, sug, "", rid]
            xml.append(_row_xml(r, [_c(f"{COLS[k]}{r}", v, 4 if k == 4 else 3) for k, v in enumerate(vals)], _height(vals)))
    hidden = ' hidden="1"'  # cột F (mã câu) ẩn với owner
    cols = "".join(f'<col min="{k + 1}" max="{k + 1}" width="{w}" customWidth="1"{hidden if k == 5 else ""}/>'
                   for k, w in enumerate(WIDTHS))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
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
        f'xmlns:r="{ns}/officeDocument/2006/relationships"><sheets><sheet name="Form" sheetId="1" r:id="rId1"/></sheets></workbook>',
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
        return [{COLS[k]: (v or "").strip() for k, v in enumerate(r[:6])} for r in csv.reader(f)]


# ---------- lệnh ----------

def verdict(text):
    t = re.sub(r"[.!\s]+$", "", text.strip().lower())
    return "ok" if t in OK_WORDS else "no" if t in NO_WORDS else "own"


def cmd_build(root):
    qs, ds, errs = form_rows(root)
    if errs:
        sys.stderr.write("owner-form: chưa gửi được, sửa trước:\n" + "\n".join(f"  - {e}" for e in errs) + "\n")
        return 1
    own, dev = by_group(qs["OWNER"] + ds), by_group(qs["DEV"])
    if not own and not dev:
        print("Không có câu nào cần trả lời (OWNER / DEV đang MỞ, mặc định CHƯA).")
        return 0
    # QnA-v<n>.xlsx; tiếp số sau bản cũ (QnA-v<n> hoặc owner-form-<n> của bản trước)
    nums = [int(m.group(1)) for f in os.listdir(os.path.join(root, P)) if (m := re.match(r"(?:QnA-v|owner-form-)(\d+)\.xlsx$", f))]
    n = 1 + max(nums, default=0)
    out = os.path.join(root, P, f"QnA-v{n}.xlsx")
    write_xlsx(out, app_name(root), [(SECTIONS[0][1], SECTIONS[0][2], own), (SECTIONS[1][1], SECTIONS[1][2], dev)])
    qp, dp = os.path.join(root, P, "questions.md"), os.path.join(root, P, "defaults.md")
    upd = {q[0]: {"trạng thái": f"CHỜ {who}"} for who, v in qs.items() for q in v}
    if upd:
        patch(qp, "q", ["q", "trạng thái"], upd)
    if ds:
        patch(dp, "d", ["d", "owner chọn"], {d[0]: {"owner chọn": "CHỜ OWNER"} for d in ds})
    print(f"{os.path.relpath(out, root)}: A. Owner {len(qs['OWNER'])} câu + {len(ds)} mặc định · "
          f"B. Dev {len(dev)} câu. Gửi file + thư mục {P}/design/ (mockup) cho owner (mục A) và dev (mục B).")
    return 0


def cmd_import(root, path):
    rows = read_xlsx(path) if path.lower().endswith(".xlsx") else read_csv(path)
    hdr = next((k for k, r in enumerate(rows) if gc.clean(r.get("B", "")).lower().startswith("câu hỏi")), None)
    if hdr is None:
        sys.stderr.write("owner-form: không thấy dòng tiêu đề 'Câu hỏi' trong file\n")
        return 1
    head = {gc.clean(v).lower(): c for c, v in rows[hdr].items()}
    a_col = next((c for h, c in head.items() if "duyệt" in h), "D")
    id_col = head.get("mã", "")
    qp, dp = os.path.join(root, P, "questions.md"), os.path.join(root, P, "defaults.md")
    qm, qrows = gc.table(gc.read(root, "questions.md") or "", "q", "câu hỏi", "đề xuất", "ai trả lời")
    dm, drows = gc.table(gc.read(root, "defaults.md") or "", "d", "mục", "đề xuất")
    by_text = {gc.clean(r[qm["câu hỏi"]]): gc.clean(r[qm["q"]]) for r in qrows} if qm else {}
    by_text.update({gc.clean(r[dm["mục"]]): gc.clean(r[dm["d"]]) for r in drows} if dm else {})
    sug = {gc.clean(r[qm["q"]]): gc.clean(r[qm["đề xuất"]]) for r in qrows} if qm else {}
    who = {gc.clean(r[qm["q"]]): gc.first_word(r[qm["ai trả lời"]]).capitalize() or "Owner" for r in qrows} if qm else {}
    qu, du, stat, blank, again = {}, {}, {"ok": 0, "no": 0, "own": 0}, [], []
    for r in rows[hdr + 1:]:
        rid = gc.clean(r.get(id_col, "")) or by_text.get(gc.clean(r.get("B", "")), "")
        ans = r.get(a_col, "").strip()
        if not re.match(r"[QD]-", rid):  # dòng tên mục / tiêu đề
            continue
        if not ans:
            blank.append(rid)
            continue
        v = verdict(ans)
        stat[v] += 1
        if rid.startswith("Q-"):
            w = who.get(rid, "Owner")
            redo = "BA" if w == "Owner" else "Architect"
            qu[rid] = {"ok": {"trạng thái": "ĐÃ TRẢ LỜI", "trả lời": f"{w} OK: {sug.get(rid, '')}"},
                       "no": {"trạng thái": "MỞ", "trả lời": f"{w} không đồng ý đề xuất, {redo} đề xuất lại"},
                       "own": {"trạng thái": "ĐÃ TRẢ LỜI", "trả lời": f"{w}: {ans}"}}[v]
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
        print(f"Đề xuất lại (lượt sau): {', '.join(again)}")
    if blank:
        print(f"Chưa trả lời (vẫn CHỜ OWNER / CHỜ DEV): {', '.join(blank)}")
    return 0


def main():
    global P
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    gc.set_dir(sys.argv[1:])
    P = gc.P
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
