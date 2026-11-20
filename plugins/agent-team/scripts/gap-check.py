#!/usr/bin/env python3
"""gap-check - tài liệu sản phẩm (docs/product/) còn thiếu ý nào. Chỉ đọc (trừ --spec).

Dùng: gap-check.py [--json] [--gate] [--spec | --spec-check] [--dir=<thư mục tài liệu>] [thư mục project]
  --dir         thư mục tài liệu, mặc định docs/product (module mới: --dir=docs/product/modules/<tên>, cổng ở MODULE.md).
  --gate        kiểm thêm cổng trong APP.md (Intake, Challenger, Owner duyệt). Guard dùng trước S3 / S6.
  --spec        sinh lại docs/product/SPEC.md (gộp toàn bộ tài liệu app thành 1 file) rồi kiểm như thường.
  --spec-check  SPEC.md phải khớp tài liệu hiện tại (quên chạy --spec sau khi sửa tài liệu = thiếu).
Exit 0 = đủ, 1 = còn thiếu, 2 = chưa init / chưa có docs/product, 3 = lỗi script.
"""
import json
import os
import re
import sys
import unicodedata

P = "docs/product"  # --dir= đổi được (module mới: docs/product/modules/<tên>)
ID_RE = re.compile(r"\b([BGDRSFQ])-(\d+)\b")
EMPTY = {"", "-", "—", "..."}
COVERAGE_OK = {"RÕ", "LOẠI", "CHƯA BIẾT"}
CHOICES = {"GIỮ", "BỎ", "KHÁC"}
Q_STATES = {"MỞ", "CHỜ OWNER", "CHỜ DEV", "ĐÃ TRẢ LỜI", "GIẢ ĐỊNH"}


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def clean(v):
    return re.sub(r"[`*_]", "", v or "").strip()


def empty(v):
    v = clean(v)
    return v in EMPTY or v.upper().startswith("TODO") or v.startswith("<")


def ids(v, kind=None):
    return {f"{k}-{n}" for k, n in ID_RE.findall(v or "") if kind is None or k in kind}


def read(root, rel):
    p = os.path.join(root, P, rel)
    if not os.path.isfile(p):
        return None
    # NFC + "xóa" = "xoá": gõ dấu kiểu nào cũng khớp tên cột
    return unicodedata.normalize("NFC", open(p, encoding="utf-8", errors="ignore").read()).replace("óa", "oá").replace("Óa", "Oá")


def tables(text):
    """[(headers, rows)] với headers viết thường, rows là list dict theo header."""
    out, block = [], []
    for line in (text or "").splitlines() + [""]:
        if line.strip().startswith("|"):
            block.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if len(block) >= 2:
            head = [clean(h).lower() for h in block[0]]
            rows = [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in block[2:]]
            out.append((head, rows))
        block = []
    return out


def table(text, *cols):
    """Bảng đầu tiên có đủ các cột (so khớp đầu chuỗi). Trả về (map cột -> tên thật, rows) hoặc (None, [])."""
    for head, rows in tables(text):
        m = {}
        for c in cols:
            hit = next((h for h in head if h.startswith(c)), None)
            if hit is None:
                break
            m[c] = hit
        if len(m) == len(cols):
            return m, rows
    return None, []


def fields(text):
    """Dòng `- Tên: giá trị` -> dict."""
    return {m.group(1).strip(): m.group(2) for m in re.finditer(r"(?m)^[\s>*-]*([^:\n|]{2,40}):\s*(.*)$", text or "")}


def col(row, prefix):
    """Giá trị cột đầu tiên có tên bắt đầu bằng prefix."""
    return next((v for h, v in row.items() if h.startswith(prefix)), "")


def first_word(v):
    return (clean(v).split() or [""])[0].upper()


def responsive(root):
    """Dự án cần chạy trên điện thoại: intake ghi Responsive: CÓ, hoặc config VIEWPORTS có chiều rộng < 768."""
    if first_word(fields(read(root, "intake.md") or "").get("Responsive", "")) == "CÓ":
        return True
    try:
        cfg = open(os.path.join(root, ".claude", "agent-team.config"), encoding="utf-8", errors="ignore").read()
    except OSError:
        return False
    m = re.search(r"(?m)^\s*VIEWPORTS=['\"]?([\d ]+)", cfg)
    return bool(m) and any(int(w) < 768 for w in m.group(1).split())


def status_name(root):
    """File cổng: MODULE.md (module mới) hoặc APP.md (cả app)."""
    return "MODULE.md" if os.path.isfile(os.path.join(root, P, "MODULE.md")) else "APP.md"


def set_dir(argv):
    global P
    d = next((a.split("=", 1)[1] for a in argv if a.startswith("--dir=")), None)
    if d:
        P = d.strip().strip("/")


def check(root, gate=False):
    rows = []
    def add(item, why):
        more = f"; ... (+{len(why) - 6})" if len(why) > 6 else ""
        rows.append({"item": item, "ok": not why, "why": "; ".join(why[:6]) + more})

    # 1. intake
    t = read(root, "intake.md")
    if t is None:
        add("intake.md", ["chưa có file"])
    else:
        add("intake.md", [f"'{k}' còn trống" for k, v in fields(t).items() if empty(v)][:8])

    # 2. brief -> B-n
    t = read(root, "brief.md") or ""
    brief = {m.group(1): m.group(2) for m in re.finditer(r"(?m)^\s*-\s*(B-\d+)\s*:\s*(.*)$", t)}
    brief = {k for k, v in brief.items() if not empty(v)}
    add("brief.md: ý owner B-n", [] if brief else ["chưa tách ý owner thành B-n"])

    # 3. problem -> G-n
    t = read(root, "problem.md") or ""
    goals = {m.group(1) for m in re.finditer(r"(?m)^\s*-\s*(G-\d+)\s*:\s*(.*)$", t) if not empty(m.group(2).split("|")[0])}
    add("problem.md: mục tiêu G-n", [] if goals else ["chưa có mục tiêu G-n"])

    # 4. questions
    t = read(root, "questions.md") or ""
    m, qrows = table(t, "q", "mức", "trạng thái", "trả lời")
    qids, why = set(), []
    for r in qrows:
        q = clean(r[m["q"]])
        if not q:
            continue
        qids.add(q)
        lvl, st = clean(r[m["mức"]]).upper(), clean(r[m["trạng thái"]]).upper()
        who = first_word(col(r, "ai trả lời"))
        if who in ("OWNER", "DEV") and empty(col(r, "đề xuất")):
            why.append(f"{q} gửi {who.lower()} nhưng chưa có Đề xuất của team")
        if st not in Q_STATES:
            why.append(f"{q} trạng thái '{st or 'trống'}'")
        elif st == "GIẢ ĐỊNH" and lvl == "CAO":
            why.append(f"{q} mức CAO không được GIẢ ĐỊNH, phải hỏi owner")
        elif lvl == "CAO" and st in ("CHỜ OWNER", "CHỜ DEV"):
            why.append(f"{q} mức CAO đang chờ {st[4:].lower()} trả lời form")
        elif lvl == "CAO" and st != "ĐÃ TRẢ LỜI":
            why.append(f"{q} mức CAO chưa được owner trả lời")
        elif st not in ("MỞ", "CHỜ OWNER", "CHỜ DEV") and empty(r[m["trả lời"]]):
            why.append(f"{q} thiếu câu trả lời")
    add("questions.md: sổ câu hỏi", why if m else ["thiếu bảng Q | Mức | Trạng thái | Trả lời"])

    # 5. coverage 12 góc nhìn
    t = read(root, "coverage.md") or ""
    m, crow = table(t, "#", "góc nhìn", "kết luận", "ghi chú")
    why, seen = [], set()
    for r in crow:
        n = clean(r[m["#"]])
        seen.add(n)
        kl, note = clean(r[m["kết luận"]]).upper(), r[m["ghi chú"]]
        if kl not in COVERAGE_OK:
            why.append(f"góc {n} chưa kết luận")
        elif kl == "LOẠI" and empty(note):
            why.append(f"góc {n} LOẠI nhưng không có lý do")
        elif kl == "CHƯA BIẾT" and not (ids(note, "Q") & qids):
            why.append(f"góc {n} CHƯA BIẾT nhưng không trỏ tới Q-n có trong sổ câu hỏi")
    missing = [str(i) for i in range(1, 13) if str(i) not in seen]
    if missing:
        why.insert(0, f"thiếu góc {', '.join(missing)}")
    add("coverage.md: 12 góc nhìn", why if m else ["thiếu bảng # | Góc nhìn | Kết luận | Ghi chú"])

    # 6. screens
    t = read(root, "screens.md") or ""
    m, srows = table(t, "s", "màn", "vai trò", "flow", "mockup")
    screens = {}
    for r in (srows if m else []):
        s = clean(r[m["s"]])
        if s:
            screens[s] = r

    # 7. flows
    t = read(root, "flows.md") or ""
    parts = re.split(r"(?m)^##\s+(F-\d+)\b.*$", t)
    flows, why = {}, []
    for i in range(1, len(parts) - 1, 2):
        f, body = parts[i], parts[i + 1]
        flows[f] = body
        fm, frows = table(body, "bước", "hành động", "nếu lỗi")
        if not fm or not frows:
            why.append(f"{f} thiếu bảng Bước | Hành động | Nếu lỗi")
            continue
        bad = [clean(r[fm["bước"]]) or "?" for r in frows if empty(r[fm["hành động"]]) or empty(r[fm["nếu lỗi"]])]
        if bad:
            why.append(f"{f} bước {', '.join(bad[:5])} thiếu hành động hoặc nhánh lỗi")
    if not flows:
        why.append("chưa có luồng ## F-n")
    add("flows.md: luồng + nhánh lỗi", why)

    # 8. requirements + truy vết
    t = read(root, "requirements.md") or ""
    m, rrows = table(t, "r", "yêu cầu", "nguồn", "vai trò", "màn", "ac")
    reqs, why, used_src, used_s = {}, [], set(), set()
    t_def = read(root, "defaults.md") or ""
    dm, drows = table(t_def, "d", "mục", "owner chọn")
    dids = {clean(r[dm["d"]]) for r in drows if clean(r[dm["d"]])} if dm else set()
    for r in (rrows if m else []):
        rid = clean(r[m["r"]])
        if not rid:
            continue
        reqs[rid] = r
        src = ids(r[m["nguồn"]], "BGD")
        used_src |= src
        if empty(r[m["yêu cầu"]]):
            why.append(f"{rid} trống yêu cầu")
        if not src:
            why.append(f"{rid} không có nguồn B/G/D (tự bịa?)")
        ghost = src - brief - goals - dids
        if ghost:
            why.append(f"{rid} trỏ tới {', '.join(sorted(ghost))} không tồn tại")
        if empty(r[m["vai trò"]]):
            why.append(f"{rid} thiếu vai trò")
        if empty(r[m["ac"]]):
            why.append(f"{rid} thiếu AC")
        man = clean(r[m["màn"]])
        if man.upper() != "N/A":
            ss = ids(man, "S")
            if not ss:
                why.append(f"{rid} thiếu màn (S-n hoặc N/A)")
            for s in ss - set(screens):
                why.append(f"{rid} trỏ tới màn {s} chưa có trong screens.md")
            used_s |= ss
    if m and not reqs:
        why.append("chưa có yêu cầu nào")
    add("requirements.md: yêu cầu R-n", why if m else ["thiếu bảng R | Yêu cầu | Nguồn | Vai trò | Màn | AC"])
    lost = sorted(brief - used_src, key=lambda x: int(x.split("-")[1]))
    add("truy vết: ý owner B-n → R-n", [f"{', '.join(lost)} chưa có yêu cầu nào"] if lost else [])

    # 9. defaults
    why = []
    for r in (drows if dm else []):
        d = clean(r[dm["d"]])
        if not d:
            continue
        ch = first_word(r[dm["owner chọn"]])
        note = col(r, "ghi chú")
        if ch not in CHOICES:
            why.append(f"{d} owner chưa chọn" + (" (đang chờ form)" if clean(r[dm["owner chọn"]]).upper() == "CHỜ OWNER" else ""))
        elif ch == "KHÁC" and empty(note):
            why.append(f"{d} KHÁC nhưng không ghi cách khác")
        elif ch in ("GIỮ", "KHÁC") and d not in used_src:
            why.append(f"{d} owner GIỮ nhưng chưa có R-n")
    if dm and not dids:
        why.append("chưa chép mục mặc định từ catalog")
    add("defaults.md: owner chọn mặc định", why if dm else ["thiếu bảng D | Mục | Owner chọn"])

    # 10. screens: vai trò, flow, mockup, màn mồ côi
    why = []
    for s, r in screens.items():
        if empty(col(r, "vai trò")):
            why.append(f"{s} thiếu vai trò")
        fl = ids(col(r, "flow"), "F")
        if not fl:
            why.append(f"{s} thiếu flow F-n")
        for f in fl - set(flows):
            why.append(f"{s} trỏ tới {f} không có trong flows.md")
        mk = clean(col(r, "mockup"))
        if empty(mk) or not os.path.isfile(os.path.join(root, P, "design", os.path.basename(mk))):
            why.append(f"{s} chưa có file mockup trong {P}/design/")
        if s not in used_s:
            why.append(f"{s} không có R-n nào dùng (màn mồ côi)")
    if not screens:
        why.append("chưa có màn S-n")
    add("screens.md: màn + mockup", why)

    # 10b. responsive: mọi wireframe có tab Mobile
    if responsive(root):
        why = []
        for s, r in screens.items():
            mk = os.path.join(root, P, "design", os.path.basename(clean(col(r, "mockup"))))
            if os.path.isfile(mk) and 'data-s="mobile"' not in (read_raw(mk) or ""):
                why.append(f"{s} thiếu tab Mobile")
        add("responsive: wireframe có tab Mobile", why)

    # 11. vai trò × màn
    why = []
    split = lambda v: {x.strip().lower() for x in re.split(r"[,·/;]", clean(v)) if x.strip()}
    for rid, r in (reqs.items() if m else []):
        roles = split(r[m["vai trò"]]) - {"hệ thống"}
        for s in ids(r[m["màn"]], "S") & set(screens):
            have = split(col(screens[s], "vai trò"))
            lack = roles - have
            if lack:
                why.append(f"{rid}: vai trò {', '.join(sorted(lack))} không có trên {s}")
    add("vai trò × màn", why[:8])

    # 12. dữ liệu × CRUD + trạng thái
    t = read(root, "data.md") or ""
    cm, crows = table(t, "dữ liệu", "tạo", "xem", "sửa", "xoá")
    why = []
    for r in (crows if cm else []):
        name = clean(r[cm["dữ liệu"]]) or "?"
        bad = [k for k in ("tạo", "xem", "sửa", "xoá") if empty(r[cm[k]])]
        if bad:
            why.append(f"{name}: trống {', '.join(bad)}")
    if not cm or not crows:
        why.append("chưa có bảng Dữ liệu × CRUD")
    sm, strows = table(t, "dữ liệu", "trạng thái", "vào từ", "ra tới")
    states = {}
    for r in (strows if sm else []):
        states.setdefault(clean(r[sm["dữ liệu"]]).lower(), set()).add(clean(r[sm["trạng thái"]]).lower())
    for r in (strows if sm else []):
        ent, st = clean(r[sm["dữ liệu"]]).lower(), clean(r[sm["trạng thái"]])
        for key, end in (("vào từ", "bắt đầu"), ("ra tới", "kết thúc")):
            vals = {x.strip().lower() for x in re.split(r"[,·/;]", clean(r[sm[key]])) if x.strip()}
            if not vals:
                why.append(f"{ent}/{st}: trống '{key}'")
            for v in vals - states.get(ent, set()) - {end}:
                why.append(f"{ent}/{st}: '{key}' = '{v}' không phải trạng thái có thật")
    add("data.md: CRUD + trạng thái", why[:8])

    # cổng owner
    if gate:
        f = fields(read(root, status_name(root)) or "")
        why = []
        for k, ok in (("Intake", "YES"), ("Challenger", "DONE"), ("Owner duyệt", "APPROVED")):
            if first_word(f.get(k, "")) != ok:
                why.append(f"{k}: {ok}")
        add(f"{status_name(root)}: cổng", why)
    return rows


# ---------- SPEC.md: gộp tài liệu app thành 1 file (sinh tự động, không sửa tay) ----------

SPEC_PARTS = [
    ("brief.md", "Ý tưởng & ý của owner"), ("problem.md", "Vấn đề & mục tiêu"), ("intake.md", "Phạm vi & stack"),
    ("requirements.md", "Yêu cầu"), ("flows.md", "Luồng nghiệp vụ"), ("screens.md", "Màn hình"),
    ("data.md", "Dữ liệu"), ("defaults.md", "Mặc định owner đã chọn"), ("questions.md", "Câu hỏi đã hỏi owner"),
    ("coverage.md", "12 góc nhìn"),
]
SPEC_KB = ["tech-stack.md", "architecture.md", "roles-and-permissions.md", "domain-model.md", "business-rules.md", "glossary.md"]


def read_raw(path):
    return open(path, encoding="utf-8", errors="ignore").read() if os.path.isfile(path) else None


def body(text):
    """Bỏ tiêu đề cấp 1 và dòng hướng dẫn `>`, hạ cấp heading để lồng vào SPEC."""
    out = []
    for ln in text.splitlines():
        if ln.startswith("# ") or ln.startswith(">"):
            continue
        out.append("#" + ln if ln.startswith("#") else ln)
    return "\n".join(out).strip()


def build_spec(root):
    pdir = os.path.join(root, P)
    app = read_raw(os.path.join(pdir, status_name(root))) or ""
    name = next((ln[2:].strip() for ln in app.splitlines() if ln.startswith("# ")), "App")
    parts = [(rel, title) for rel, title in SPEC_PARTS if read_raw(os.path.join(pdir, rel))]
    out = [f"# SPEC: {name}", "",
           "> Sinh tự động bằng `.claude/agent-team/gap-check.py --spec` từ `docs/product/` + KB. "
           "**Không sửa tay**: sửa file nguồn rồi chạy lại.", "", "## Mục lục"]
    toc = [t for _, t in parts] + ["Truy vết ý owner → yêu cầu → màn", "Kiến trúc & quyết định", "Module & trạng thái"]
    out += [f"{i}. {t}" for i, t in enumerate(toc, 1)] + [""]
    for i, (rel, title) in enumerate(parts, 1):
        text = body(read_raw(os.path.join(pdir, rel)))
        if rel == "screens.md":  # wireframe bấm được từ SPEC
            text = re.sub(r"(?<![\[/])\b(mockup-[\w.-]+\.html)", r"[\1](design/\1)", text)
        out += [f"## {i}. {title}", f"_Nguồn: `{rel}`_", "", text, ""]
    n = len(parts)

    # truy vết B → R → S, dựng từ requirements.md
    brief = re.findall(r"(?m)^\s*-\s*(B-\d+)\s*:\s*(.*)$", read_raw(os.path.join(pdir, "brief.md")) or "")
    m, rrows = table(read(root, "requirements.md") or "", "r", "nguồn", "màn")
    out += [f"## {n + 1}. Truy vết ý owner → yêu cầu → màn", "", "| Ý owner | Yêu cầu | Màn |", "|---|---|---|"]
    for b, text in brief:
        rs = [r for r in rrows if m and b in ids(r[m["nguồn"]], "B")]
        ss = sorted({s for r in rs for s in ids(r[m["màn"]], "S")}, key=lambda x: int(x.split("-")[1]))
        out.append(f"| {b}: {clean(text)} | {', '.join(clean(r[m['r']]) for r in rs) or '**CHƯA CÓ**'} | {', '.join(ss) or 'N/A'} |")
    out.append("")

    # KB + quyết định: chỉ liên kết, nội dung nằm ở KB
    out += [f"## {n + 2}. Kiến trúc & quyết định", ""]
    for f in SPEC_KB:
        if os.path.isfile(os.path.join(root, "docs", f)):
            out.append(f"- [`docs/{f}`](../{f})")
    ddir = os.path.join(root, "docs", "decisions")
    for f in sorted(os.listdir(ddir)) if os.path.isdir(ddir) else []:
        if f.endswith(".md") and f != "README.md":
            title = next((ln[2:].strip() for ln in (read_raw(os.path.join(ddir, f)) or "").splitlines() if ln.startswith("# ")), f)
            out.append(f"- Quyết định: [{title}](../decisions/{f})")
    out += ["", f"## {n + 3}. Module & trạng thái", "", body(app.split(sec, 1)[1]) if (sec := next((h for h in ("## Module", "## Task") if h in app), None)) else "Chưa chia module.", ""]
    return "\n".join(out).rstrip() + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    set_dir(sys.argv[1:])
    root = find_root(args[0] if args else os.getcwd())
    if not root or not os.path.isdir(os.path.join(root, P)):
        sys.stderr.write(f"gap-check: không thấy .claude/agent-team.config hoặc {P}/ (chạy /agent-team:app trước)\n")
        sys.exit(2)
    spec_path = os.path.join(root, P, "SPEC.md")
    if "--spec" in sys.argv:
        open(spec_path, "w", encoding="utf-8").write(build_spec(root))
    rows = check(root, gate="--gate" in sys.argv)
    if "--spec-check" in sys.argv:
        cur = read_raw(spec_path)
        why = ["chưa có SPEC.md, chạy gap-check.py --spec"] if cur is None else (
            [] if cur == build_spec(root) else ["SPEC.md cũ hơn tài liệu, chạy gap-check.py --spec"])
        rows.append({"item": "SPEC.md: khớp tài liệu", "ok": not why, "why": "; ".join(why)})
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{'OK  ' if r['ok'] else 'THIEU'}  {r['item']}" + (f"  - {r['why']}" if r["why"] else ""))
        n = sum(not r["ok"] for r in rows)
        print(f"\n{len(rows) - n}/{len(rows)} đạt" + (f", còn {n} mục thiếu" if n else ""))
    sys.exit(1 if any(not r["ok"] for r in rows) else 0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # lỗi script: exit 3, guard vẫn chặn
        sys.stderr.write(f"gap-check: lỗi {e}\n")
        sys.exit(3)
