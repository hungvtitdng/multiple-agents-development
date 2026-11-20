#!/usr/bin/env python3
"""kb-check - KB còn khung rỗng, sai nguồn, cũ so với code, hay trỏ mã không có thật. Chỉ đọc.

Dùng: kb-check.py [--json] [--index] [--functions] [thư mục project]
Exit 0 = đủ, 1 = còn thiếu. Kiểm:
  - file bắt buộc có `verified-at: <commit>` và đủ số nguồn `file.ext:dòng`
  - nguồn `file:dòng` có thật (file tồn tại trong REPOS, đủ dòng); code đổi sau verified-at → CŨ
  - mỗi dòng BR- có nhãn + nguồn; ma trận quyền không ô trống, vai trò / C- có thật
  - mã BR- / P- / C- / F- mà page, luồng, ma trận trỏ tới phải có trong KB tổng
  - module trong danh sách có README; route trong bảng tra có file KB
  - chỉ mục hàm docs/functions/*.md (khi có FUNCTION_INDEX_PATHS): so với graph Graphify,
    hàm public trong phạm vi mà chưa có dòng → thiếu; dòng trỏ hàm không còn trong code → thừa
--index: in bảng tra ngược mã → page / luồng dùng nó.
--functions: in đầy đủ hàm thiếu / thừa trong chỉ mục (kèm file:dòng) để điền.
"""
import glob
import json
import os
import re
import subprocess
import sys

REQUIRED = {
    "docs/project-overview.md": 0,
    "docs/architecture.md": 0,
    "docs/tech-stack.md": 0,
    "docs/domain-model.md": 1,
    "docs/business-rules.md": 3,
    "docs/roles-and-permissions.md": 1,
    "docs/permission-matrix.md": 1,
    "docs/flows/README.md": 0,
    "docs/glossary.md": 0,
    "docs/api/endpoints.md": 1,
    "docs/database/schema.md": 1,
    "docs/testing/test-strategy.md": 0,
    "docs/engineering/coding-standards.md": 1,
    "docs/engineering/backend.md": 0,  # bỏ qua khi config không có BE_PATHS; kiểm từng dòng BE- (check_rules)
    "docs/engineering/frontend.md": 0,  # bỏ qua khi config không có FE_PATHS; kiểm từng dòng FE-
    "docs/database/migration-rules.md": 0,
    "docs/testing/automation-guide.md": 0,
    "docs/security/review-patterns.md": 0,
}
VERIFIED_RE = re.compile(r"verified-at:\s*`?([0-9a-f]{7,40})\b")
CITE_RE = re.compile(r"(?<![\w/:.@-])([\w.@-]+(?:/[\w.@-]+)*\.\w{1,5}):(\d+)")
TASK_RE = re.compile(r"\b\d{8}-[\w-]+")
LABELS = ("verified", "unverified", "observed", "assumption", "planned", "deprecated", "confirmed")
REF_RE = {
    "BR": re.compile(r"\bBR-[\w-]*?\d+\b"),
    "P": re.compile(r"\bP-[a-z][\w-]*(?:\.[\w-]+)+"),
    "C": re.compile(r"\bC-[a-z][\w-]*"),
    "F": re.compile(r"\bF-\d+\b"),
}


def find_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def read(root, rel):
    p = os.path.join(root, rel)
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else None


def repos(root):
    text = read(root, ".claude/agent-team.config") or ""
    m = re.search(r"(?m)^\s*REPOS=(.*)$", text)
    names = (m.group(1).strip().strip("\"'").split() if m else []) or ["."]
    return [os.path.normpath(os.path.join(root, n)) for n in names]


def rows_of(text, first):
    """Dòng bảng có ô đầu bắt đầu bằng `first` (vd 'BR-'): [ô...]."""
    out = []
    for ln in (text or "").splitlines():
        cells = [c.strip().strip("`") for c in ln.strip().strip("|").split("|")] if ln.strip().startswith("|") else []
        if cells and cells[0].startswith(first):
            out.append(cells)
    return out


def table(text, *need):
    """Bảng đầu tiên có đủ cột (so đầu chuỗi, chữ thường): (header, rows)."""
    block = []
    for ln in (text or "").splitlines() + [""]:
        if ln.strip().startswith("|"):
            block.append([c.strip() for c in ln.strip().strip("|").split("|")])
            continue
        if len(block) >= 2:
            head = [h.lower() for h in block[0]]
            if all(any(h.startswith(n) for h in head) for n in need):
                return head, [r + [""] * (len(head) - len(r)) for r in block[2:]]
        block = []
    return None, []


def col(head, name):
    return next(k for k, h in enumerate(head) if h.startswith(name))


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def cite_problems(root, text, repo_dirs):
    """(lỗi nguồn, {repo: [file]} các file được trích)."""
    bad, used = [], {}
    for path, line in sorted(set(CITE_RE.findall(text))):
        hit = next((r for r in repo_dirs if os.path.isfile(os.path.join(r, path))), None)
        if hit is None:
            bad.append(f"{path}:{line} không có file (ghi đường dẫn từ gốc repo)")
            continue
        with open(os.path.join(hit, path), encoding="utf-8", errors="ignore") as f:
            n = sum(1 for _ in f)
        if int(line) > n:
            bad.append(f"{path}:{line} vượt cuối file ({n} dòng)")
        used.setdefault(hit, set()).add(path)
    return bad, used


def stale(sha, used):
    changed = []
    for repo, files in used.items():
        if git(repo, "cat-file", "-e", f"{sha}^{{commit}}") is None:
            continue
        out = git(repo, "diff", "--name-only", sha, "HEAD", "--", *sorted(files)) or ""
        changed += out.split()
    return changed


def kb_files(root):
    rels = [r for r in required(root) if os.path.isfile(os.path.join(root, r))]
    extra = glob.glob(os.path.join(root, "docs", "modules", "**", "*.md"), recursive=True)
    extra += glob.glob(os.path.join(root, "docs", "flows", "*.md"))
    extra += func_files(root)
    rels += [os.path.relpath(p, root) for p in extra if os.path.relpath(p, root) not in rels]
    return [r for r in rels if r != "docs/modules/README.md"]


def defined(root):
    br_src = [read(root, "docs/business-rules.md")] + [
        open(p, encoding="utf-8", errors="ignore").read() for p in glob.glob(os.path.join(root, "docs", "modules", "*", "README.md"))]
    flows = "\n".join(open(p, encoding="utf-8", errors="ignore").read() for p in glob.glob(os.path.join(root, "docs", "flows", "*.md")))
    return {
        "BR": {c[0] for t in br_src for c in rows_of(t, "BR-")},
        "P": {c[0] for c in rows_of(read(root, "docs/permission-matrix.md"), "P-")},
        "C": {c[0] for c in rows_of(read(root, "docs/roles-and-permissions.md"), "C-")},
        "F": set(re.findall(r"(?m)^##\s+(F-\d+)\b", flows)),
    }


def refs(text, kinds):
    return {k: set(REF_RE[k].findall(text or "")) for k in kinds}


def check_br(text):
    why = []
    for cells in rows_of(text, "BR-"):
        low = " ".join(cells).lower()
        if not any(lb in low for lb in LABELS):
            why.append(f"{cells[0]} thiếu nhãn")
        if not (CITE_RE.search(" ".join(cells)) or TASK_RE.search(" ".join(cells))):
            why.append(f"{cells[0]} thiếu nguồn file:dòng / task-id")
    return why


RULE_FILES = {"docs/engineering/backend.md": "BE-", "docs/engineering/frontend.md": "FE-"}


def check_rules(text, prefix):
    """Quy chuẩn BE- / FE-: có ít nhất 1 dòng, không trùng mã, đủ nhãn + nguồn, không còn dòng mẫu Example."""
    rows = rows_of(text, prefix)
    rows = [r for r in rows if re.match(rf"{prefix}\d+$", r[0])]
    if not rows:
        return [f"chưa có quy tắc {prefix}n nào"]
    why, seen = [], set()
    for r in rows:
        if r[0] in seen:
            why.append(f"{r[0]} trùng mã")
        seen.add(r[0])
        low = r[-1].lower()  # cột cuối = Nhãn
        if "example" in low:
            why.append(f"{r[0]} còn là dòng mẫu Example")
            continue
        if not any(lb in low for lb in LABELS):
            why.append(f"{r[0]} thiếu nhãn")
        if "planned" not in low and not (CITE_RE.search(" ".join(r)) or TASK_RE.search(" ".join(r))):
            why.append(f"{r[0]} thiếu nguồn file:dòng / task-id")
    return why


def check_matrix(root, ids):
    text = read(root, "docs/permission-matrix.md")
    head, rows = table(text, "p", "hành động", "page")
    if head is None:
        return ["chưa có bảng P | Hành động | <vai trò...> | Page / API"]
    roles = [h for h in head[col(head, "hành động") + 1:col(head, "page")]]
    vh, vrows = table(read(root, "docs/roles-and-permissions.md"), "vai trò")
    known = {r[col(vh, "vai trò")].lower() for r in vrows} if vh else set()
    why = [f"cột '{r}' không có trong roles-and-permissions.md (Vai trò)" for r in roles if not r.startswith("<") and r not in known]
    p_rows = [r for r in rows if r[0].startswith("P-")]
    if not p_rows:
        why.append("chưa có dòng P- nào")
    for r in p_rows:
        cells = r[col(head, "hành động") + 1:col(head, "page")]
        empty = [roles[k] for k, c in enumerate(cells) if not ("✅" in c or "❌" in c)]
        if empty:
            why.append(f"{r[0]} ô trống / không rõ ✅ ❌: {', '.join(empty)}")
        line = " ".join(r)
        if not (CITE_RE.search(line) or TASK_RE.search(line)):
            why.append(f"{r[0]} thiếu nguồn policy file:dòng")
        for k, found in refs(line, ("C", "BR")).items():
            for x in sorted(found - ids[k]):
                why.append(f"{r[0]} trỏ tới {x} không có trong KB")
    return why


def check_modules(root):
    text = read(root, "docs/modules/README.md")
    why = []
    head, rows = table(text, "module", "code")
    for r in rows if head else []:
        name = r[col(head, "module")].strip("` ")
        if name and not os.path.isfile(os.path.join(root, "docs", "modules", name, "README.md")):
            why.append(f"module '{name}' chưa có modules/{name}/README.md")
    head, rows = table(text, "route", "module", "file kb")
    for r in rows if head else []:
        kb = r[col(head, "file kb")].strip("` ")
        if not kb:
            why.append(f"route {r[col(head, 'route')]} chưa có file KB")
            continue
        p = next((os.path.join(root, b, kb) for b in ("docs/modules", "docs", ".") if os.path.isfile(os.path.join(root, b, kb))), None)
        if p is None:
            why.append(f"route {r[col(head, 'route')]}: {kb} không có")
        elif not VERIFIED_RE.search(open(p, encoding="utf-8", errors="ignore").read()):
            why.append(f"{kb} thiếu verified-at")
    return why


# ---------- chỉ mục hàm docs/functions/ so với graph (Graphify) ----------

FUNC_DIR = "docs/functions"
PRIVATE_KW = re.compile(r"\b(private|protected|internal|fileprivate)\b")


def cfg(root, key):
    m = re.search(rf"(?m)^\s*{key}=(.*)$", read(root, ".claude/agent-team.config") or "")
    return m.group(1).split("#")[0].strip().strip("\"'") if m else ""


def func_files(root):
    return sorted(p for p in glob.glob(os.path.join(root, FUNC_DIR, "*.md")) if os.path.basename(p) != "README.md")


def norm_fn(s):
    """`OrderService#cancel()` / `Order::cancel` → OrderService.cancel"""
    s = s.strip().strip("`").split("(")[0].strip()
    return re.sub(r"#|::|->", ".", s)


def indexed(root):
    """{tên hàm: file index} từ cột đầu bảng có cột 'Hàm' trong docs/functions/*.md (bỏ dòng tham chiếu →)."""
    out = {}
    for p in func_files(root):
        text = open(p, encoding="utf-8", errors="ignore").read()
        head, rows, block = None, [], []
        for ln in text.splitlines() + [""]:
            if ln.strip().startswith("|"):
                block.append([c.strip() for c in ln.strip().strip("|").split("|")])
                continue
            if len(block) >= 2 and block[0] and block[0][0].lower().startswith("hàm"):
                for r in block[2:]:
                    if r and r[0] and not r[0].startswith("<") and not any(c.startswith("→") for c in r[1:2]):
                        out[norm_fn(r[0])] = os.path.relpath(p, root)
            block = []
    return out


def in_scope(sf, scopes):
    sf = sf.replace("\\", "/").lstrip("./")
    for p in scopes:
        p = os.path.normpath(p).replace("\\", "/")
        cands = {p.lstrip("./")}
        if p.startswith("../"):  # repo khác: graph có thể ghi đường dẫn từ gốc repo đó
            tail = re.sub(r"^(\.\./)+", "", p)
            cands |= {tail, tail.split("/", 1)[1] if "/" in tail else ""}
        if any(c and (sf == c or sf.startswith(c.rstrip("/") + "/")) for c in cands):
            return True
    return False


def ruby_private(lines, i, name, indent):
    if re.match(r"\s*(private|protected)\s+def\b", lines[i]):
        return True
    if any(re.match(rf"\s*(private|protected)\s+.*:{re.escape(name)}\b", l) for l in lines):
        return True
    for l in reversed(lines[:i]):
        ind = len(l) - len(l.lstrip())
        if re.match(r"\s*(class|module)\s", l) and ind < indent:
            return False
        if re.match(r"\s*(private|protected)\s*$", l) and ind <= indent:
            return True
        if re.match(r"\s*public\s*$", l) and ind <= indent:
            return False
    return False


def is_public(path, line_no, name, top_level):
    """Đoán hàm public theo cú pháp ngôn ngữ (graph không ghi visibility)."""
    try:
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        return True
    i = min(max(line_no - 1, 0), len(lines) - 1) if lines else 0
    line = lines[i] if lines else ""
    ext = os.path.splitext(path)[1].lower()
    if name.startswith("_") or name.startswith("#"):
        return False
    if ext == ".go":
        return name[:1].isupper()
    if ext == ".rb":
        return not ruby_private(lines, i, name, len(line) - len(line.lstrip()))
    if ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue"):
        if PRIVATE_KW.search(line):
            return False
        if top_level:
            whole = "\n".join(lines)
            return "export" in line or re.search(rf"export\s*\{{[^}}]*\b{re.escape(name)}\b", whole) is not None \
                or re.search(rf"module\.exports[^\n]*\b{re.escape(name)}\b", whole) is not None
        return True
    return not PRIVATE_KW.search(line)


def graph_functions(root):
    """(graph path, built_at_commit, {tên: (file, dòng)} mọi hàm, set tên trong phạm vi + public). None nếu chưa có graph."""
    gp = next((os.path.join(root, "graphify-out", f) for f in ("merged-graph.json", "graph.json")
               if os.path.isfile(os.path.join(root, "graphify-out", f))), None)
    if not gp:
        return None
    g = json.load(open(gp, encoding="utf-8"))
    nodes = g.get("nodes", [])
    classes = {n["id"]: n["label"] for n in nodes if n.get("_callable_class")}
    scopes = cfg(root, "FUNCTION_INDEX_PATHS").split()
    every, public = {}, set()
    repo_dirs = repos(root)
    for n in nodes:
        if not n.get("_callable") or n.get("_callable_class"):
            continue
        label = n.get("label", "").lstrip(".").split("(")[0]
        owner = max((cid for cid in classes if n["id"].startswith(cid + "_")), key=len, default=None)
        full = f"{classes[owner]}.{label}" if owner else label
        sf = n.get("source_file", "")
        line = int((re.findall(r"\d+", n.get("source_location", "")) or ["0"])[0])
        every[full] = (sf, line)
        if scopes and in_scope(sf, scopes):
            path = next((os.path.join(r, sf) for r in [root] + repo_dirs if os.path.isfile(os.path.join(r, sf))), sf)
            if is_public(path, line, label, owner is None):
                public.add(full)
    return gp, g.get("built_at_commit"), every, public


def check_functions(root):
    """Hàng kết quả so chỉ mục hàm với graph. [] khi không bật FUNCTION_INDEX_PATHS."""
    if not cfg(root, "FUNCTION_INDEX_PATHS"):
        return []
    rel = f"{FUNC_DIR}/ (so với graph)"
    idx = indexed(root)
    if not func_files(root):
        return [{"file": rel, "ok": False, "why": "chưa có file chỉ mục nào (docs/functions/<model>.md)"}]
    gf = graph_functions(root)
    if gf is None:
        off = cfg(root, "USE_CODE_GRAPH") == "0"
        return [{"file": rel, "ok": off, "why": "USE_CODE_GRAPH=0: không so với graph" if off else
                 "chưa có graphify-out/graph.json, chạy `graphify update .` để so chỉ mục với code"}]
    _, built, every, public = gf
    missing = sorted(public - set(idx))
    extra = sorted(k for k in idx if k not in every)
    why = []
    if missing:
        why.append(f"thiếu {len(missing)} hàm public chưa có trong chỉ mục: {', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}")
    if extra:
        why.append(f"{len(extra)} hàm trong chỉ mục không còn trong code: {', '.join(extra[:8])}")
    head = (git(root, "rev-parse", "HEAD") or "").strip()
    if built and head and not head.startswith(built) and not built.startswith(head[:7]):
        why.append(f"graph build ở commit {built[:7]}, HEAD là {head[:7]}: chạy `graphify update .` rồi kiểm lại")
    return [{"file": rel, "ok": not (missing or extra), "why": "; ".join(why), "indexed": len(idx), "public": len(public)}]


def functions_report(root):
    """--functions: danh sách đầy đủ để Scout / dev điền chỉ mục."""
    gf = graph_functions(root)
    if gf is None:
        return "chưa có graphify-out/graph.json"
    _, _, every, public = gf
    idx = indexed(root)
    out = [f"Hàm public trong FUNCTION_INDEX_PATHS: {len(public)} · đã có trong chỉ mục: {len(public & set(idx))}", "", "## Thiếu (file:dòng  tên)"]
    out += [f"{every[k][0]}:{every[k][1]}\t{k}" for k in sorted(public - set(idx), key=lambda k: every[k])] or ["(không)"]
    out += ["", "## Thừa (có trong chỉ mục, không còn trong code)"]
    out += [f"{idx[k]}\t{k}" for k in sorted(idx) if k not in every] or ["(không)"]
    return "\n".join(out)


def required(root):
    """REQUIRED, bỏ quy chuẩn BE / FE khi dự án không có BE_PATHS / FE_PATHS."""
    skip = {f"docs/engineering/{k}.md" for k, key in (("backend", "BE_PATHS"), ("frontend", "FE_PATHS")) if not cfg(root, key)}
    return {k: v for k, v in REQUIRED.items() if k not in skip}


def check(root):
    rows, repo_dirs, ids = [], repos(root), defined(root)
    for rel, min_cite in required(root).items():
        if not os.path.isfile(os.path.join(root, rel)):
            rows.append({"file": rel, "ok": False, "why": "chưa có file"})
    for rel in kb_files(root):
        text = read(root, rel)
        why = []
        m = VERIFIED_RE.search(text)
        if not m:
            why.append("thiếu dòng `verified-at: <commit>` (còn là khung)")
        cites = len(CITE_RE.findall(text))
        if cites < REQUIRED.get(rel, 0):
            why.append(f"mới {cites}/{REQUIRED[rel]} nguồn file:dòng")
        bad, used = cite_problems(root, text, repo_dirs)
        why += bad[:5]
        if m and (old := stale(m.group(1), used)):
            why.append(f"CŨ: code đổi sau verified-at {m.group(1)}: {', '.join(sorted(set(old))[:5])}")
        if rel == "docs/business-rules.md" or re.match(r"docs/modules/[^/]+/README\.md$", rel):
            why += check_br(text)[:5]
        if rel in RULE_FILES:
            why += check_rules(text, RULE_FILES[rel])[:5]
        if rel.startswith(("docs/modules/", "docs/flows/")):
            for k, found in refs(text, ("BR", "P", "C", "F")).items():
                why += [f"trỏ tới {x} không có trong KB tổng" for x in sorted(found - ids[k])][:5]
        if rel == "docs/permission-matrix.md" and m:
            why += check_matrix(root, ids)[:8]
        rows.append({"file": rel, "ok": not why, "why": "; ".join(why), "cites": cites})
    mods = glob.glob(os.path.join(root, "docs", "modules", "*", "README.md"))
    if not mods:
        rows.append({"file": "docs/modules/<tên>/README.md", "ok": False, "why": "chưa có module nào"})
    why = check_modules(root)
    if why:
        rows.append({"file": "docs/modules/README.md", "ok": False, "why": "; ".join(why[:8])})
    return rows + check_functions(root)


def index(root):
    """{mã: [file dùng mã]} từ page, action, luồng."""
    out = {}
    files = glob.glob(os.path.join(root, "docs", "modules", "*", "*", "*.md")) + glob.glob(os.path.join(root, "docs", "flows", "*.md"))
    for p in sorted(files):
        text = open(p, encoding="utf-8", errors="ignore").read()
        for found in refs(text, ("BR", "P", "C", "F")).values():
            for x in found:
                out.setdefault(x, []).append(os.path.relpath(p, os.path.join(root, "docs")))
    return dict(sorted(out.items()))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = find_root(args[0] if args else os.getcwd())
    if not root:
        sys.stderr.write("kb-check: không thấy .claude/agent-team.config (chạy /agent-team:init trước)\n")
        sys.exit(2)
    if "--functions" in sys.argv:
        print(functions_report(root))
        sys.exit(0)
    if "--index" in sys.argv:
        for k, v in index(root).items():
            print(f"{k}\t{', '.join(v)}")
        sys.exit(0)
    rows = check(root)
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{'OK  ' if r['ok'] else 'THIEU'}  {r['file']}" + (f"  - {r['why']}" if r["why"] else ""))
        n = sum(not r["ok"] for r in rows)
        print(f"\n{len(rows) - n}/{len(rows)} đạt" + (f", còn {n} mục thiếu" if n else ""))
    sys.exit(1 if any(not r["ok"] for r in rows) else 0)


if __name__ == "__main__":
    main()
