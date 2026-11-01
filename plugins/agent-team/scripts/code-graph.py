#!/usr/bin/env python3
"""code-graph: đồ thị phụ thuộc giữa file, không cần cài gói ngoài.

  code-graph.py build              (Lead) quét git ls-files, ghi code-graph-out/
  code-graph.py who-uses <tên|file>   file nào dùng tên/file này
  code-graph.py uses <file>           file này dùng những file nào
  code-graph.py explain <tên|file>    tóm tắt: định nghĩa, ai dùng, dùng ai

Cạnh EXTRACTED = import/require tường minh. Cạnh INFERRED = tên class/module xuất hiện trong file khác.
Exit: 0 có kết quả, 3 thiếu graph, 4 không khớp.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

OUT = "code-graph-out"
EXTS = {".rb", ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".php", ".vue"}
SKIP_RE = re.compile(r"(^|/)(node_modules|vendor|dist|build|coverage|\.git|db/migrate|public/assets)/|\.min\.|\.lock$")
MAX_BYTES = 300_000
MAX_DEFINERS = 3  # tên định nghĩa ở quá nhiều file thì bỏ qua (mơ hồ)

DEF_RES = [
    re.compile(r"^\s*(?:abstract\s+|final\s+|export\s+(?:default\s+)?)*(?:class|module|interface|trait|enum)\s+([A-Z]\w*)", re.M),
    re.compile(r"^\s*export\s+(?:default\s+)?(?:function|const|type)\s+([A-Z]\w*)", re.M),
    re.compile(r"^type\s+([A-Z]\w*)\s+(?:struct|interface)", re.M),
]
RUBY_REQ = re.compile(r"^\s*require_relative\s+['\"]([^'\"]+)['\"]", re.M)
JS_IMP = re.compile(r"(?:from\s+|require\(\s*|import\s+)['\"](\.{1,2}/[^'\"]+)['\"]")
PY_IMP = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
IDENT = re.compile(r"\b[A-Z][A-Za-z0-9_]{2,}\b")


def sh(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def repo_root():
    code, top = sh("git", "rev-parse", "--show-toplevel")
    return top if code == 0 else os.getcwd()


def resolve_relative(src, target, files):
    base = os.path.normpath(os.path.join(os.path.dirname(src), target))
    for cand in [base, *(base + e for e in EXTS), *(os.path.join(base, "index" + e) for e in EXTS)]:
        if cand in files:
            return cand
    return None


def resolve_py(mod, files):
    p = mod.replace(".", "/")
    for cand in (p + ".py", p + "/__init__.py"):
        if cand in files:
            return cand
    return None


def build(root):
    _, listing = sh("git", "-C", root, "ls-files")
    files = {f for f in listing.splitlines() if os.path.splitext(f)[1] in EXTS and not SKIP_RE.search(f)}
    text, defs = {}, defaultdict(set)
    for f in files:
        try:
            if os.path.getsize(os.path.join(root, f)) > MAX_BYTES:
                continue
            text[f] = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
    file_defs = {}
    for f, t in text.items():
        names = {m for r in DEF_RES for m in r.findall(t)}
        file_defs[f] = sorted(names)
        for n in names:
            defs[n].add(f)
    edges = {}
    for f, t in text.items():
        explicit = []
        explicit += [resolve_relative(f, m, files) for m in RUBY_REQ.findall(t)]
        explicit += [resolve_relative(f, m, files) for m in JS_IMP.findall(t)]
        if f.endswith(".py"):
            explicit += [resolve_py(a or b, files) for a, b in PY_IMP.findall(t)]
        for to in filter(None, explicit):
            if to != f:
                edges[(f, to)] = "EXTRACTED"
        for name in set(IDENT.findall(t)):
            owners = defs.get(name)
            if owners and len(owners) <= MAX_DEFINERS and f not in owners:
                for to in owners:
                    edges.setdefault((f, to), "INFERRED")
    graph = {
        "version": 1,
        "commit": sh("git", "-C", root, "rev-parse", "HEAD")[1],
        "files": {f: {"defs": file_defs[f]} for f in sorted(text)},
        "edges": [{"from": a, "to": b, "kind": k} for (a, b), k in sorted(edges.items())],
    }
    out = os.path.join(root, OUT)
    os.makedirs(out, exist_ok=True)
    json.dump(graph, open(os.path.join(out, "graph.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(out, "GRAPH_REPORT.md"), "w", encoding="utf-8").write(report(graph))
    print(f"Đã build: {len(text)} file, {len(edges)} cạnh → {OUT}/GRAPH_REPORT.md")


def report(g):
    indeg, outdeg = Counter(), Counter()
    for e in g["edges"]:
        indeg[e["to"]] += 1
        outdeg[e["from"]] += 1
    langs = Counter(os.path.splitext(f)[1] for f in g["files"])
    ex = sum(e["kind"] == "EXTRACTED" for e in g["edges"])
    lines = [
        "# Code graph",
        f"Build ở commit `{g['commit'][:10]}`. Thay đổi chưa commit không có trong graph.",
        f"- {len(g['files'])} file ({', '.join(f'{k}: {v}' for k, v in langs.most_common())})",
        f"- {len(g['edges'])} cạnh: {ex} EXTRACTED (import tường minh), {len(g['edges']) - ex} INFERRED (suy từ tên class/module, chỉ là gợi ý)",
        "",
        "## File được dùng nhiều nhất (sửa ở đây ảnh hưởng rộng)",
        *[f"- `{f}` ← {n} file" for f, n in indeg.most_common(15)],
        "",
        "## File phụ thuộc nhiều nhất",
        *[f"- `{f}` → {n} file" for f, n in outdeg.most_common(10)],
        "",
        "## Cách hỏi",
        "- `.claude/agent-team/code-graph.py who-uses <Tên|file>`",
        "- `.claude/agent-team/code-graph.py uses <file>`",
        "- `.claude/agent-team/code-graph.py explain <Tên|file>`",
    ]
    return "\n".join(lines) + "\n"


def load(root):
    p = os.path.join(root, OUT, "graph.json")
    if not os.path.isfile(p):
        print("Chưa có graph. Nhờ Lead chạy: .claude/agent-team/code-graph.py build", file=sys.stderr)
        sys.exit(3)
    g = json.load(open(p))
    head = sh("git", "-C", root, "rev-parse", "HEAD")[1]
    if head and g.get("commit") and head != g["commit"]:
        print(f"CẢNH BÁO: graph build ở {g['commit'][:10]}, HEAD hiện {head[:10]}. Mâu thuẫn với code thì tin code.", file=sys.stderr)
    return g


def targets(g, key):
    if key in g["files"]:
        return [key]
    return sorted(f for f, v in g["files"].items() if key in v["defs"])


def neighbors(g, files, direction):
    s = set(files)
    key_a, key_b = ("to", "from") if direction == "in" else ("from", "to")
    return sorted({(e[key_b], e["kind"]) for e in g["edges"] if e[key_a] in s and e[key_b] not in s})


def show(title, items):
    print(title)
    for f, k in items[:50]:
        print(f"  [{k}] {f}")
    if len(items) > 50:
        print(f"  … còn {len(items) - 50}")
    if not items:
        print("  (không có)")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"build", "who-uses", "uses", "explain"}:
        print(__doc__)
        sys.exit(2)
    cmd, root = sys.argv[1], repo_root()
    if cmd == "build":
        return build(root)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    g, key = load(root), sys.argv[2]
    files = targets(g, key)
    if not files:
        print(f"Không khớp '{key}' (thử tên class/module hoặc đường dẫn file đầy đủ)")
        sys.exit(4)
    if cmd == "who-uses":
        show(f"Dùng {key} (định nghĩa ở {', '.join(files)}):", neighbors(g, files, "in"))
    elif cmd == "uses":
        show(f"{key} dùng:", neighbors(g, files, "out"))
    else:
        print(f"{key}: định nghĩa ở {', '.join(files)}")
        for f in files:
            print(f"  {f} định nghĩa: {', '.join(g['files'][f]['defs']) or '(không có class/module)'}")
        show("Được dùng bởi:", neighbors(g, files, "in"))
        show("Dùng:", neighbors(g, files, "out"))


if __name__ == "__main__":
    main()
