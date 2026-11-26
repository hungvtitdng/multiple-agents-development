#!/usr/bin/env python3
"""agent-team guard - PreToolUse hook. Exit 2 = chặn, lý do in ra stderr."""
import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time

PROTECTED_BRANCHES = {"main", "master", "develop"}
READONLY_ROLES = {
    "business-analyst", "solution-architect", "technical-architect",
    "test-designer", "code-reviewer", "security", "scout", "challenger", "ui-designer",
}
# File thiết kế của task: docs/agent-tasks/<task-id>/design/<file> -> role được ghi
DESIGN_OWNERS = [
    (re.compile(r"^mockup-[\w.-]+\.html$"), {"ui-designer"}),
    (re.compile(r"^(_wf\.(css|js)|index\.html)$"), {"ui-designer"}),  # CSS / JS dùng chung + mục lục mockup
    (re.compile(r"^(workflow|state)\.md$"), {"business-analyst"}),
    (re.compile(r"^sequence\.md$"), {"solution-architect", "technical-architect"}),
]
DOCS_DIR = "docs/agent-tasks/"
OWNER_ZONE = {"backend-dev": "be", "frontend-dev": "fe", "test-executor": "test"}
_BA = {"business-analyst"}
_ARCH = {"solution-architect", "technical-architect"}
# Knowledge base: thư mục/file -> role được ghi. Lead ghi được tất cả. Không nằm trong danh sách = chỉ Lead.
KB_OWNERS = [
    ("docs/domain/", _BA), ("docs/business-rules.md", _BA), ("docs/domain-model.md", _BA),
    ("docs/roles-and-permissions.md", _BA), ("docs/permission-matrix.md", _BA), ("docs/flows/", _BA), ("docs/glossary.md", _BA),
    ("docs/project-overview.md", _ARCH), ("docs/architecture.md", _ARCH), ("docs/tech-stack.md", _ARCH),
    ("docs/architecture/", _ARCH), ("docs/engineering/", _ARCH), ("docs/decisions/", _ARCH),
    ("docs/integrations/", _ARCH),
    ("docs/api/", _ARCH | {"backend-dev"}), ("docs/database/", _ARCH | {"backend-dev"}),
    ("docs/modules/", _BA | _ARCH | {"backend-dev", "frontend-dev"}),
    ("docs/functions/", _ARCH | {"backend-dev", "frontend-dev"}),  # chỉ mục hàm: dev sửa trong cùng commit
    ("docs/testing/", {"test-designer", "test-executor"}),
    ("docs/security/", {"security"}),
    # App Mode: tài liệu sản phẩm (APP, brief, intake, questions còn lại = chỉ Lead)
    ("docs/product/design/", {"ui-designer"}), ("docs/product/screens.md", {"ui-designer"}),
    ("docs/product/problem.md", _BA), ("docs/product/coverage.md", _BA), ("docs/product/defaults.md", _BA),
    ("docs/product/requirements.md", _BA), ("docs/product/flows.md", _BA), ("docs/product/data.md", _BA),
    ("docs/product/legacy-map.md", _BA),
]
PRODUCT_APP = "docs/product/APP.md"
GAP_CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "gap-check.py")
COMMIT_MSG_RE = re.compile(r"^\[[a-z][a-z-]*\] [\w.-]+: \S.*$")
TRAILER_RE = re.compile(r"(?i)signed-off-by|co-authored-by|reviewed-by|generated-by|generated with")
STAGE_WRITE_RE = re.compile(r">+\s*['\"]?\S*\.agent-team/stage")
STAGE_VALUE_RE = re.compile(r"(?:echo|printf)\s+(?:-\w+\s+)*['\"]?(S[1-6])\b")
# Điều kiện (đọc từ TASK.md) trước khi Lead sang giai đoạn mới
GATE_CLASS = {"NHỎ", "VỪA", "LỚN", "APP", "MODULE", "ĐÃ"}
MODULE_DOC_RE = re.compile(r"^docs/product/modules/[\w.-]+/")  # module mới: cùng chủ sở hữu file như docs/product/
TEST_FILE_RE = re.compile(r"(^|/)(__tests__|__mocks__)/|(_spec|_test)\.\w+$|\.(spec|test)\.\w+$|(^|/)test_[^/]+\.py$")
STAGE_ZONES = {"S1": set(), "S2": set(), "S3": {"be", "fe"}, "S4": {"test"}}
GRAPHIFY = {"graphify", "graphifyy", "graphify-mcp"}
GRAPHIFY_READ = {"explain", "affected", "query", "path", "god-nodes", "--version", "--help", "-h"}
GRAPHIFY_LEAD = {"update", "merge-graphs"}  # extract (gọi LLM), install, hook, watch... chặn với mọi người
PERM_CMDS = {"chmod", "chown", "chgrp", "setfacl", "chattr"}
SNAP_MAX = 2_000_000
WRITE_CMDS = {"tee", "mv", "cp", "rm", "touch", "truncate", "install", "dd", "ln"}
HIDDEN_RE = re.compile(r"(^|[\s/'\"=])\.agent-team(/|\s|$|['\"])")
CLONE_SCRIPT = "agent-db"
BOARD = "board.py"
BOARD_ROLE_CMDS = {"post", "read", "status", "whys", "done", "progress"}
HEREDOC_RE = re.compile(r"<<(-?)\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")

ENV_SAMPLES = {".env.example", ".env.sample", ".env.template", ".env.dist"}
SECRET_NAME_RES = [
    re.compile(r"^\.env(\..+)?$"),
    re.compile(r"^master\.key$"),
    re.compile(r"^.+\.key$"),
    re.compile(r"^.+\.pem$"),
    re.compile(r"^id_(rsa|ed25519|ecdsa|dsa)(\..*)?$"),
    re.compile(r"^\.(npmrc|pgpass|netrc)$"),
    re.compile(r"^.+\.(dump|sql\.gz|bak)$"),
]
SECRET_CONTENT_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"(?i)\b(postgres(ql)?|mysql2?|redis|mongodb(\+srv)?|amqp)://[^:\s/]+:[^@\s]{3,}@"),
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)"
               r"\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
]
PLACEHOLDERS = ("example", "changeme", "xxxx", "dummy", "placeholder", "<", "${", "your_")

DB_TASK_RE = re.compile(
    r"\bdb:(migrate|rollback|drop|reset|setup|schema:load|structure:load|seed|prepare|create|purge|truncate_all)\b"
    r"|\b(prisma|knex|sequelize|typeorm)\b.*\bmigrat"
    r"|\balembic\s+(upgrade|downgrade)\b"
    r"|\bdropdb\b|(?i:\bdrop\s+(database|table)\b)|(?i:\btruncate\s+table\b)"
)


def block(reason):
    sys.stderr.write(f"[agent-team guard] BLOCKED: {reason}\n")
    sys.exit(2)


def norm_role(data):
    raw = data.get("agent_type") or data.get("subagent_type") or os.environ.get("AGENT_TEAM_ROLE") or ""
    return raw.strip().lower().split(":")[-1]


ENV_FILE_RE = re.compile(r"^\.env(\..+)?$")


def is_env_file(p):
    """.env, .env.local...: được xem / sửa, chỉ cấm commit / push (mẫu .env.example không tính)."""
    base = os.path.basename((p or "").strip("'\"").rstrip("/"))
    return bool(ENV_FILE_RE.match(base)) and base not in ENV_SAMPLES


def is_secret_path(p):
    if not p:
        return False
    base = os.path.basename(p.strip("'\"").rstrip("/"))
    if base in ENV_SAMPLES:
        return False
    return any(r.match(base) for r in SECRET_NAME_RES)


OPERATORS = {"&&", "||", ";", "|", "&", ";;", "|&"}
READ_ONLY_FIRST = {"grep", "egrep", "fgrep", "rg", "git", "cat", "echo", "printf", "find",
                   "ls", "head", "tail", "sed", "jq", "less", "wc"}


def parse(cmd):
    """Tách lệnh thành các segment (list token), hiểu dấu nháy."""
    segs = []
    for line in cmd.splitlines():
        try:
            lx = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lx.whitespace_split = True
            toks = list(lx)
        except ValueError:
            toks = line.split()
        cur = []
        for t in toks:
            if t in OPERATORS:
                if cur:
                    segs.append(cur)
                cur = []
            else:
                cur.append(t)
        if cur:
            segs.append(cur)
    return segs


def unquoted(cmd):
    return re.sub(r"'[^']*'|\"(\\.|[^\"\\])*\"", "''", cmd)


def first_cmd(tk):
    while tk and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tk[0]):
        tk = tk[1:]
    return os.path.basename(tk[0]) if tk else ""


def git(cwd, *args):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=20)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


# ---------- rule chung: mọi agent ----------

def check_secret_tokens(cmd):
    for tk in parse(cmd):
        for t in tk:
            for part in re.split(r"[=:,]", t):
                if is_secret_path(part) and not is_env_file(part):
                    block(f"không được đụng file nhạy cảm '{part}' (key, credentials, dump DB...). `.env*` thì được xem / sửa, không được commit")


def check_env_dump(cmd):
    for tk in parse(cmd):
        if not tk:
            continue
        if tk[0] == "printenv" or (tk[0] == "env" and all(t.startswith("-") for t in tk[1:])):
            block("không được in biến môi trường (có thể chứa KEY)")
        if tk[:2] == ["docker", "inspect"] or (len(tk) >= 3 and tk[0] in ("docker", "docker-compose") and "config" in tk[1:4]):
            block("docker inspect / compose config in ra secret")


def check_db(cmd):
    for tk in parse(cmd):
        fc = first_cmd(tk)
        if fc in READ_ONLY_FIRST or fc.startswith(CLONE_SCRIPT):
            continue
        if DB_TASK_RE.search(" ".join(tk)):
            block("migration/lệnh DB chỉ được chạy qua agent-db.sh (DB riêng của task), không đụng DB thật")


def scan_outgoing(cwd):
    code, upstream = git(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if code == 0 and upstream:
        rng = f"{upstream}..HEAD"
    else:
        rng = None
        for base in ("origin/develop", "develop", "origin/main", "main", "origin/master", "master"):
            if git(cwd, "rev-parse", "--verify", "-q", base)[0] == 0:
                rng = f"{base}...HEAD"
                break
        if not rng:
            return
    _, names = git(cwd, "diff", "--name-only", rng)
    for n in names.splitlines():
        if is_secret_path(n):
            block(f"commit chứa file nhạy cảm '{n}', không push")
    _, diff = git(cwd, "diff", "-U0", rng)
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        for r in SECRET_CONTENT_RES:
            m = r.search(line)
            if m and not any(p in m.group(0).lower() for p in PLACEHOLDERS):
                block(f"phát hiện chuỗi giống secret trong diff: '{m.group(0)[:20]}...'")


def git_target(tk, cwd):
    """(thư mục repo, subcommand, args). Hiểu `git -C <dir>` và `-c k=v` trước subcommand."""
    d, i = cwd, 1
    while i < len(tk) and tk[i].startswith("-"):
        if tk[i] == "-C" and i + 1 < len(tk):
            d = os.path.join(d, os.path.expanduser(tk[i + 1]))
            i += 2
        elif tk[i] == "-c":
            i += 2
        else:
            i += 1
    return d, (tk[i] if i < len(tk) else ""), tk[i + 1:]


def check_commit_msg(args):
    """Project có agent-team: commit đúng 1 dòng `[role] task-id: mô tả`, không trailer/chữ ký."""
    msgs, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-s", "--signoff"):
            block("commit không được có chữ ký (--signoff)")
        if a in ("-m", "--message") and i + 1 < len(args):
            msgs.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--message="):
            msgs.append(a.split("=", 1)[1])
        elif re.match(r"^-[a-z]*m$", a) and len(a) > 2 and i + 1 < len(args):
            msgs.append(args[i + 1])
            i += 2
            continue
        elif a.startswith("-m") and len(a) > 2:
            msgs.append(a[2:])
        i += 1
    if len(msgs) != 1:
        block("commit cần đúng 1 `-m \"[role] task-id: mô tả\"` (một dòng, không body)")
    m = msgs[0]
    if "\n" in m or TRAILER_RE.search(m) or not COMMIT_MSG_RE.match(m):
        block("commit message phải một dòng `[role] task-id: mô tả`, không body, không Co-authored-by/Signed-off-by")


LEAD_GIT = {"commit", "push", "merge", "rebase", "cherry-pick", "revert", "am", "pull", "tag", "worktree"}


def check_git(cmd, cwd, role=None):
    hook_cwd = cwd
    cur = cwd
    for tk in parse(cmd):
        if first_cmd(tk) == "cd" and len(tk) > 1:
            cur = os.path.join(cur, os.path.expanduser(tk[1]))
            continue
        if "git" not in tk or first_cmd(tk) in READ_ONLY_FIRST - {"git"}:
            continue
        cwd, sub, args = git_target(tk[tk.index("git"):], cur)
        if role and sub in LEAD_GIT:
            block(f"git {sub}: chỉ Lead làm (agent sửa file xong báo danh sách file, Lead commit theo role)")
        _, branch = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")

        if sub == "push":
            if any(a in ("-f", "--force", "--force-with-lease", "--mirror", "-d", "--delete") or a.startswith("--force") or a.startswith("+") for a in args):
                block("không force push / xoá branch remote")
            for a in args:
                target = a.split(":")[-1].replace("refs/heads/", "")
                if target in PROTECTED_BRANCHES:
                    block(f"không push vào '{target}'")
            if branch in PROTECTED_BRANCHES:
                block(f"đang ở '{branch}', chỉ push từ branch agent/*")
            scan_outgoing(cwd)
        elif sub in ("commit", "merge", "rebase", "cherry-pick", "revert", "am", "pull"):
            if branch in PROTECTED_BRANCHES:
                block(f"không {sub} trên '{branch}', hãy dùng branch agent/*")
            if sub == "commit":
                if find_root(hook_cwd):
                    check_commit_msg(args)
                _, staged = git(cwd, "diff", "--cached", "--name-only")
                for n in staged.splitlines():
                    if is_secret_path(n):
                        block(f"đang stage file nhạy cảm '{n}'")
        elif sub == "reset" and "--hard" in args:
            block("git reset --hard bị cấm")
        elif sub == "clean" and any(a.startswith("-") and "f" in a for a in args):
            block("git clean -f bị cấm")
        elif sub == "branch" and any(a in ("-D", "--delete", "-d") for a in args):
            block("không xoá branch")
        elif sub in ("checkout", "restore") and "." in args:
            block(f"git {sub} . sẽ xoá thay đổi chưa commit")


def board_segments(cmd):
    """[(chỉ số token board.py, segment)] cho mọi lệnh gọi board.py."""
    out = []
    for tk in parse(cmd):
        for i, t in enumerate(tk):
            if os.path.basename(t) == BOARD:
                out.append((i, tk))
                break
    return out


def strip_heredocs(cmd):
    """Bỏ thân heredoc (nội dung bài post) để không bị soi như lệnh."""
    out, lines, i = [], cmd.splitlines(), 0
    while i < len(lines):
        out.append(lines[i])
        m = HEREDOC_RE.search(lines[i]) if "<<" in unquoted(lines[i]) else None
        i += 1
        if m:
            while i < len(lines) and (lines[i].strip() if m.group(1) else lines[i]) != m.group(2):
                i += 1
            i += 1
    return "\n".join(out)


def check_board(cmd, role):
    """board.py: role chỉ post/read/status và chỉ post bằng tên mình; challenger không dùng."""
    if role and BOARD in cmd and any(first_cmd(tk).startswith("$") for tk in parse(cmd)):
        block("chạy board.py bằng đường dẫn trực tiếp, không qua biến")
    for i, tk in board_segments(cmd):
        sub = tk[i + 1] if i + 1 < len(tk) else ""
        if not role:
            continue
        if role == "challenger":
            block("challenger không được đọc board (mù ticket)")
        if sub not in BOARD_ROLE_CMDS:
            block(f"board.py {sub}: chỉ Lead được dùng (role chỉ post/read/status/whys/done/progress)")
        if sub in ("post", "done", "progress"):
            who = ""
            for j, t in enumerate(tk):
                if t == "--role" and j + 1 < len(tk):
                    who = tk[j + 1]
                elif t.startswith("--role="):
                    who = t.split("=", 1)[1]
            if who.strip().lower().split(":")[-1] != role:
                block(f"chỉ được {sub} bằng tên mình: --role {role}")


def check_graphify(cmd, role):
    """Graphify: role chỉ lệnh đọc; Lead thêm update/merge-graphs; lệnh còn lại (extract gọi LLM, install, hook...) chặn hết."""
    for tk in parse(cmd):
        for i, t in enumerate(tk):
            name = os.path.basename(t)
            if name not in GRAPHIFY:
                continue
            if name == "graphify-mcp":
                block("không chạy graphify-mcp")
            sub = tk[i + 1] if i + 1 < len(tk) else ""
            if sub == "graphify":  # uvx graphifyy graphify ...
                sub = tk[i + 2] if i + 2 < len(tk) else ""
            allowed = GRAPHIFY_READ | (set() if role else GRAPHIFY_LEAD)
            if sub not in allowed:
                who = "role chỉ được" if role else "chỉ được"
                block(f"graphify {sub or '(trống)'}: {who} {'/'.join(sorted(allowed - {'--help', '-h', '--version'}))}. "
                      "extract (gọi LLM), install, hook, watch bị chặn")
            break


def check_rm(cmd):
    for tk in parse(cmd):
        if tk and tk[0] == "rm" and any(t.startswith("-") and "r" in t for t in tk[1:]):
            if any(t in ("/", "~", ".", "..", "*", "./*", "$HOME") for t in tk[1:]):
                block("rm -r trên thư mục gốc bị cấm")


# ---------- rule riêng: role chỉ đọc ----------

READONLY_CMDS = {
    "ls", "cat", "head", "tail", "grep", "egrep", "fgrep", "rg", "wc", "tree", "pwd",
    "which", "file", "stat", "du", "diff", "sort", "uniq", "cut", "jq", "echo", "printf",
    "true", "date", "basename", "dirname", "realpath",
    "rspec", "rubocop", "brakeman", "bundle-audit", "bundler-audit", "jest", "vitest",
    "eslint", "pytest", "tsc",
}
GIT_READ = {"diff", "log", "show", "status", "blame", "branch", "rev-parse", "ls-files",
            "ls-tree", "grep", "shortlog", "describe", "merge-base", "cat-file", "fetch"}
TEST_WORDS = {"test", "spec", "lint", "audit", "rspec", "rubocop", "brakeman", "jest",
              "vitest", "eslint", "playwright", "tsc", "bundle-audit", "bundler-audit"}
FIX_FLAGS = {"-a", "-A", "--fix", "--write", "--autocorrect", "--autocorrect-all", "fix", "-u", "--update-snapshot"}
DOCKER_VAL_OPTS = {"-e", "--env", "-u", "--user", "-w", "--workdir", "-f", "--file", "-p",
                   "--project-name", "--profile", "--project-directory", "--name", "--entrypoint"}


def strip_docker(tk):
    """docker compose exec/run <svc> CMD -> CMD (None nếu là lệnh docker khác)."""
    i = 1
    if tk[0] == "docker" and len(tk) > 1 and tk[1] == "compose":
        i = 2
    elif tk[0] != "docker-compose" and tk[0] != "docker":
        return tk
    while i < len(tk) and tk[i].startswith("-"):
        i += 2 if tk[i] in DOCKER_VAL_OPTS else 1
    if i >= len(tk):
        return None
    sub = tk[i]
    if sub in ("ps", "logs", "top", "images"):
        return []
    if sub not in ("exec", "run"):
        return None
    if sub == "run" and "--rm" not in tk:
        return None
    i += 1
    while i < len(tk) and tk[i].startswith("-"):
        i += 2 if tk[i] in DOCKER_VAL_OPTS else 1
    return tk[i + 1:] if i + 1 <= len(tk) else None


def readonly_segment_ok(tk):
    while tk and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tk[0]):
        tk = tk[1:]
    if not tk:
        return True
    if tk[0] in ("docker", "docker-compose"):
        inner = strip_docker(tk)
        return inner is not None and readonly_segment_ok(inner)
    cmd = os.path.basename(tk[0])
    if cmd == BOARD:
        return len(tk) > 1 and tk[1] in BOARD_ROLE_CMDS
    if any(t in FIX_FLAGS for t in tk[1:]):
        return False
    if cmd.startswith(CLONE_SCRIPT):
        return len(tk) > 1 and tk[1] in ("status", "test", "e2e")
    if cmd in GRAPHIFY:
        return len(tk) > 1 and tk[1] in GRAPHIFY_READ
    if cmd == "kb-check.py":
        return True  # chỉ đọc: báo file KB nào còn khung
    if cmd == "git":
        return git_target(tk, "")[1] in GIT_READ
    if cmd == "find":
        return not any(t in ("-delete", "-exec", "-execdir", "-ok", "-okdir") or t.startswith("-fprint") for t in tk)
    if cmd == "sed":
        return not any(t.startswith("-i") or t == "--in-place" for t in tk)
    if cmd in READONLY_CMDS:
        return True
    if cmd in ("bundle", "npm", "yarn", "pnpm", "npx", "rails", "rake", "bin/rails", "bin/rspec", "bin/rake", "go"):
        return any(w in TEST_WORDS or w.startswith("test") or w.startswith("lint") for w in tk[1:])
    if tk[0] in ("bin/rails", "bin/rspec", "bin/rake", "./bin/rails", "./bin/rspec"):
        return any(w in TEST_WORDS for w in tk[1:]) or "rspec" in tk[0]
    return False


def check_readonly_bash(cmd, role):
    uq = unquoted(cmd)
    if "`" in uq or "$(" in uq:
        block(f"role '{role}' chỉ đọc: không dùng subshell")
    if re.search(r"(^|[^0-9&=-])>{1,2}(?!\s*(/dev/null|&))", uq) or re.search(r"\btee\b", uq):
        block(f"role '{role}' chỉ đọc: không ghi file bằng redirect/tee")
    for tk in parse(cmd):
        if not readonly_segment_ok(tk):
            block(f"role '{role}' chỉ đọc: lệnh '{' '.join(tk)[:60]}' không nằm trong danh sách cho phép")


def full_path(path, cwd):
    return os.path.normpath(os.path.join(cwd, path)).replace("\\", "/") if path else ""


def docs_rel(path, cwd):
    """Đường dẫn tương đối trong docs/ của repo chính, None nếu không thuộc docs/ (hoặc chưa init)."""
    root = find_root(cwd)
    if not root or not path:
        return None
    rel = os.path.relpath(full_path(path, cwd), root).replace("\\", "/")
    return rel if rel.startswith("docs/") else None


def kb_owners(rel):
    rel = MODULE_DOC_RE.sub("docs/product/", rel)
    for pre, roles in KB_OWNERS:
        if rel == pre or (pre.endswith("/") and rel.startswith(pre)):
            return roles
    return None


def docs_verdict(rel, role, cwd):
    """None nếu role được ghi rel trong docs/, ngược lại là lý do chặn."""
    if rel.startswith(DOCS_DIR):
        if role == "scout" and os.path.basename(rel) == "CONTEXT.md":
            return None
        parts = rel[len(DOCS_DIR):].split("/")
        if len(parts) == 3 and parts[1] == "design":
            for rx, roles in DESIGN_OWNERS:
                if rx.match(parts[2]):
                    return None if role in roles else f"design/{parts[2]} do {', '.join(sorted(roles))} ghi"
            return "design/ chỉ gồm mockup-<màn>.html, _wf.css, _wf.js, index.html (ui-designer), workflow.md / state.md (BA), sequence.md (Architect)"
        return "docs/agent-tasks (TASK, board) chỉ Lead ghi. Trả kết quả cho Lead, không tự ghi"
    if role == "scout" and stage_value(cwd) is None:
        return None  # init: Scout dựng nháp KB khi chưa có task
    owners = kb_owners(rel)
    if owners is None:
        return f"'{rel}' chỉ Lead được ghi"
    if role not in owners:
        return f"role '{role}' không sở hữu '{rel}' (chủ: {', '.join(sorted(owners))}). Báo Lead"
    return None


def check_docs(path, cwd, role):
    rel = docs_rel(path, cwd)
    if role and rel is not None:
        why = docs_verdict(rel, role, cwd)
        if why:
            block(why)


def check_readonly_write(path, cwd, role):
    if docs_rel(path, cwd) is None:
        block(f"role '{role}' chỉ được ghi tài liệu KB của mình trong docs/")


# ---------- khóa vùng ghi: dev chỉ sửa BE/FE của mình, Tester chỉ sửa test ----------

def find_root(cwd):
    """Thư mục chứa .claude/agent-team.config (đi ngược từ cwd). None nếu không có."""
    d = os.path.abspath(cwd)
    while True:
        if os.path.isfile(os.path.join(d, ".claude", "agent-team.config")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def load_zones(cwd):
    """Đọc BE_PATHS/FE_PATHS/TEST_PATHS từ .claude/agent-team.config. None nếu không có."""
    d = find_root(cwd)
    if not d:
        return None
    cfg = os.path.join(d, ".claude", "agent-team.config")
    zones = {"be": [], "fe": [], "test": []}
    keys = {"BE_PATHS": "be", "FE_PATHS": "fe", "TEST_PATHS": "test"}
    for line in open(cfg, encoding="utf-8", errors="ignore"):
        m = re.match(r"^\s*(BE_PATHS|FE_PATHS|TEST_PATHS)=(.*)$", line)
        if m:
            val = m.group(2).split("#")[0].strip().strip("'\"")
            zones[keys[m.group(1)]] = [os.path.normpath(p.strip("/")) for p in val.split() if p.upper() != "TODO"]
    return d, zones


def repo_tops(cwd):
    """Repo cần theo dõi: REPOS trong config (nhiều repo con) hoặc repo chứa cwd."""
    root = find_root(cwd)
    if root:
        cfg = os.path.join(root, ".claude", "agent-team.config")
        for line in open(cfg, encoding="utf-8", errors="ignore"):
            m = re.match(r"^\s*REPOS=(.*)$", line)
            if m:
                names = m.group(1).split("#")[0].strip().strip("'\"").split()
                tops = [os.path.join(root, n) for n in names if os.path.exists(os.path.join(root, n, ".git"))]
                if tops:
                    return tops
    code, top = git(cwd, "rev-parse", "--show-toplevel")
    return [top] if code == 0 else []


def zone_of(rel, zones):
    under = lambda ps: any(rel == p or rel.startswith(p + "/") for p in ps)
    if rel.startswith("..") and not under(zones["be"] + zones["fe"] + zones["test"]):
        return None  # ngoài root và không thuộc repo nào khai báo
    if under(zones["test"]) or TEST_FILE_RE.search(rel):
        return "test"
    if under(zones["be"]):
        return "be"
    if under(zones["fe"]):
        return "fe"
    return None


def migration_dirs(cwd):
    """(root, [thư mục migration]) từ MIGRATION_PATHS trong config. None nếu không khai báo."""
    root = find_root(cwd)
    if not root:
        return None
    for line in open(os.path.join(root, ".claude", "agent-team.config"), encoding="utf-8", errors="ignore"):
        m = re.match(r"^\s*MIGRATION_PATHS=(.*)$", line)
        if m:
            val = m.group(1).split("#")[0].strip().strip("'\"")
            dirs = [os.path.normpath(p.strip("/")) for p in val.split() if p.upper() != "TODO"]
            return (root, dirs) if dirs else None
    return None


def check_migration_new(path, cwd):
    """Mọi người (kể cả Lead): file migration chỉ sinh bằng generator trong container, không tự tạo/đổi tên."""
    loaded = migration_dirs(cwd) if path else None
    if not loaded:
        return
    root, dirs = loaded
    full = full_path(path, cwd)
    rel = os.path.relpath(full, root).replace("\\", "/")
    for d in dirs:
        if rel == d or (rel.startswith(d + "/") and not os.path.exists(full)):
            block(f"không tự tạo / đổi tên file migration ('{rel}'). Sinh bằng "
                  "`.claude/agent-team/agent-db.sh generate <task-id> <Tên> [field:type...]` (generator chạy trong container), "
                  "rồi Edit file vừa sinh")


def check_owner(path, cwd, role):
    """Chặn role ghi vào vùng của role khác."""
    mine = OWNER_ZONE.get(role)
    loaded = load_zones(cwd) if mine else None
    if not loaded or not path:
        return
    root, zones = loaded
    rel = os.path.relpath(full_path(path, cwd), root).replace("\\", "/")
    z = zone_of(rel, zones)
    if z and z != mine:
        block(f"role '{role}' chỉ được sửa vùng '{mine}', '{rel}' thuộc vùng '{z}'. Post lên board và @ chủ vùng")


def bash_write_targets(cmd):
    """File bị ghi bởi lệnh Bash (redirect, tee, mv, cp, rm, sed -i...)."""
    out = []
    for tk in parse(cmd):
        while tk and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tk[0]):
            tk = tk[1:]
        if not tk:
            continue
        fc = os.path.basename(tk[0])
        if fc in WRITE_CMDS or (fc == "sed" and any(t.startswith("-i") or t == "--in-place" for t in tk)):
            out += [t for t in tk[1:] if not t.startswith("-")]
        for i, t in enumerate(tk):
            if t.startswith(">"):
                tgt = t.lstrip(">")
                out.append(tgt if tgt else (tk[i + 1] if i + 1 < len(tk) else ""))
    return [t for t in out if t and not t.startswith("&") and t != "/dev/null"]


# ---------- chặn theo giai đoạn: không cần biết ai gọi ----------

def stage_value(cwd):
    """Giai đoạn hiện tại (S1..S6), None nếu chưa có file stage."""
    root = find_root(cwd)
    if not root:
        return None
    try:
        return open(os.path.join(root, ".agent-team", "stage"), encoding="utf-8").read().strip().upper() or None
    except OSError:
        return None


def stage_zones(cwd):
    """Vùng được ghi ở giai đoạn hiện tại (file .agent-team/stage do Lead ghi). None = không giới hạn."""
    return STAGE_ZONES.get(stage_value(cwd))


def task_field(text, name):
    """Giá trị dòng `- <name>: <giá trị>` trong TASK.md ('' nếu thiếu hoặc còn TODO)."""
    m = re.search(rf"(?im)^[\s>*-]*{re.escape(name)}\s*:\s*(.*)$", text)
    v = re.sub(r"[`*_]", "", m.group(1)).strip() if m else ""
    return "" if v.upper().startswith("TODO") or v.startswith("<") else v


def gate_missing(stage, text):
    """Điều kiện còn thiếu trong TASK.md để sang `stage`."""
    f = lambda n: task_field(text, n)
    first = lambda n: (f(n).split() or [""])[0].upper()
    miss = []
    if stage == "S3":
        if first("Loại") not in GATE_CLASS:
            miss.append("Loại (NHỎ/VỪA/LỚN/ĐÃ CHIA/APP/MODULE)")
        elif first("Loại") == "MODULE":
            miss.append("task MODULE chỉ làm tài liệu, không có code: code ở các task con (/agent-team:task <thư mục module> T-<n>)")
        elif first("Loại") == "NHỎ":
            if not f("Tiêu chí nghiệm thu"):
                miss.append("Tiêu chí nghiệm thu")
        elif first("Loại") == "ĐÃ":  # ĐÃ CHIA: kế thừa thiết kế module, không debate lại
            if not f("Tiêu chí nghiệm thu"):
                miss.append("Tiêu chí nghiệm thu (AC của task, từ bảng task của module)")
            if not f("Thiết kế module"):
                miss.append("Thiết kế module (đường dẫn phương án + API contract đã chốt)")
            if first("Security duyệt solution") not in ("APPROVED", "N/A"):
                miss.append("Security duyệt solution: APPROVED (chép từ thiết kế module)")
        else:
            if not f("Phương án chốt"):
                miss.append("Phương án chốt")
            if first("Security duyệt solution") not in ("APPROVED", "N/A"):
                miss.append("Security duyệt solution: APPROVED")
            # APP: thiết kế nằm ở docs/product, gap-check kiểm (check_stage_change)
            for k in (("Workflow", "UI mockup") if first("Loại") != "APP" else ()):
                if first(k) not in ("YES", "N/A"):
                    miss.append(f"{k}: YES hoặc N/A")
    elif stage == "S5":
        if first("Kết quả test") not in (("PASS", "N/A") if "(M-SKEL" in f("Loại").upper() else ("PASS",)):
            miss.append("Kết quả test: PASS")
        if first("Lint/format") not in ("PASS", "N/A"):
            miss.append("Lint/format: PASS hoặc N/A")
        if first("Gap còn mở") != "0":
            miss.append("Gap còn mở: 0 (đóng hết gap ở mục 14)")
        mvp = first("Chế độ test") == "MVP"
        if first("E2E") not in (("PASS", "N/A", "DEFER") if mvp else ("PASS", "N/A")):
            miss.append("E2E: PASS hoặc N/A (Chế độ test: MVP → được DEFER)")
        elif first("E2E") == "N/A" and first("UI mockup") == "YES":
            miss.append("E2E: task có UI (UI mockup: YES) thì phải PASS, không được N/A")
    elif stage == "S6":
        ok = ("APPROVED", "N/A") if "(M-SKEL" in f("Loại").upper() else ("APPROVED",)
        if first("Code review") not in ok:
            miss.append("Code review: APPROVED")
        if first("Security review") not in ok:
            miss.append("Security review: APPROVED")
        if first("Cập nhật KB") not in ("YES", "KHÔNG"):
            miss.append("Cập nhật KB: YES hoặc KHÔNG CẦN")
        if first("Bài học") not in ("YES", "KHÔNG"):
            miss.append("Bài học: YES hoặc KHÔNG CÓ")
    return miss


def open_whys(root, task):
    """Số WHY chưa được cả team đồng ý trên board SQLite (0 nếu chưa có board)."""
    p = os.path.join(root, ".agent-team", "board.db")
    if not os.path.isfile(p):
        return 0
    try:
        import sqlite3
        db = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        n = db.execute("SELECT count(*) FROM whys WHERE task=? AND status IN ('open','voting')", (task,)).fetchone()[0]
        db.close()
        return n
    except Exception:
        return 0


def cfg_value(root, key, default=""):
    """Giá trị 1 key: .claude/agent-team.local.config (riêng mỗi dev, gitignore) trước, rồi .claude/agent-team.config."""
    for name in ("agent-team.local.config", "agent-team.config"):
        try:
            for line in open(os.path.join(root, ".claude", name), encoding="utf-8", errors="ignore"):
                m = re.match(rf"^\s*{re.escape(key)}=(.*)$", line)
                if m:
                    v = m.group(1).split("#")[0].strip().strip("'\"")
                    if v or name == "agent-team.config":  # local để trống = không ghi đè
                        return v
        except OSError:
            pass
    return default


def is_kb_file(rel):
    """File KB thật (không tính tài liệu riêng task, test case/report, bài học, SPEC sinh tự động)."""
    if not rel.startswith("docs/") or rel.startswith(("docs/agent-tasks/", "docs/testing/")):
        return False
    return os.path.basename(rel) != "LESSONS.md" and rel != "docs/product/SPEC.md"


def kb_changed(root):
    """Có file KB đổi so với nhánh gốc không (gồm cả chưa commit). None = không xác định được nhánh gốc."""
    base = cfg_value(root, "BASE_BRANCH", "develop")
    mb = next((out for ref in (f"origin/{base}", base)
               for code, out in [git(root, "merge-base", "HEAD", ref)] if code == 0 and out), None)
    if not mb:
        return None
    _, changed = git(root, "diff", "--name-only", "--relative", mb)
    _, new = git(root, "ls-files", "--others", "--exclude-standard")
    return any(is_kb_file(f) for f in changed.splitlines() + new.splitlines())


def e2e_evidence_missing(root, task):
    """E2E: PASS phải có ảnh ở mọi chiều rộng trong VIEWPORTS: docs/testing/evidence/<task>/*-<rộng>.png."""
    rel = f"docs/testing/evidence/{task}"
    d = os.path.join(root, rel)
    files = os.listdir(d) if os.path.isdir(d) else []
    widths = cfg_value(root, "VIEWPORTS", "1280").split() or ["1280"]
    lack = [w for w in widths if not any(f.endswith(f"-{w}.png") for f in files)]
    return [f"E2E: PASS nhưng thiếu ảnh chiều rộng {', '.join(lack)} trong {rel}/ (<TC>-<trạng thái>-<rộng>.png)"] if lack else []


def run_gap_check(root, doc_dir=None):
    """gap-check --gate --spec-check: [] nếu sạch, ngược lại 1 dòng lý do."""
    if not os.path.isfile(GAP_CHECK):
        return ["không tìm thấy scripts/gap-check.py của plugin"]
    try:
        extra = [f"--dir={doc_dir}"] if doc_dir else []
        r = subprocess.run([sys.executable, GAP_CHECK, "--gate", "--spec-check", *extra, root], capture_output=True, text=True, timeout=30)
    except Exception as e:
        return [f"gap-check lỗi: {e}"]
    if r.returncode == 0:
        return []
    bad = [ln.split(None, 1)[1] for ln in r.stdout.splitlines() if ln.startswith("THIEU")]
    return [f"gap-check ({len(bad)} mục, xem đủ: .claude/agent-team/gap-check.py): {'; '.join(bad[:3]) or (r.stderr.strip() or 'lỗi')}"]


def product_gate(root, stage, is_app):
    """App Mode. S3: task APP qua gap-check; task khác chờ owner duyệt.
    S6: mọi task trong app (đang có APP.md) phải để docs/product đúng + SPEC.md mới."""
    has_app = os.path.isfile(os.path.join(root, PRODUCT_APP))
    if stage == "S3" and is_app:
        return run_gap_check(root)
    if stage == "S3" and has_app:
        v = task_field(open(os.path.join(root, PRODUCT_APP), encoding="utf-8", errors="ignore").read(), "Owner duyệt")
        if (v.split() or [""])[0].upper() != "APPROVED":
            return [f"{PRODUCT_APP}: Owner duyệt: APPROVED (App Mode chưa qua cổng owner)"]
    if stage == "S6" and has_app:
        return run_gap_check(root)
    return []


def module_gate(root, stage, text):
    """Task con của module mới (TASK.md `- Module: docs/product/modules/<tên>`):
    S3 chờ owner duyệt ở MODULE.md; S6 tài liệu module phải đúng + SPEC.md mới."""
    d = task_field(text, "Module").split(" ")[0].strip("`/")
    if not d or d.upper().startswith("N/A"):
        return []
    status = os.path.join(root, d, "MODULE.md")
    if not os.path.isfile(status):
        return [f"Module: {d} không có MODULE.md (chạy /agent-team:module trước)"]
    if stage == "S3":
        v = task_field(open(status, encoding="utf-8", errors="ignore").read(), "Owner duyệt")
        if (v.split() or [""])[0].upper() != "APPROVED":
            return [f"{d}/MODULE.md: Owner duyệt: APPROVED (module chưa qua cổng owner)"]
    if stage == "S6":
        return run_gap_check(root, d)
    return []


def table_rows(path, first_re):
    """Các dòng bảng markdown có ô đầu khớp first_re, trả về list ô đã bỏ dấu `."""
    if not os.path.isfile(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and re.match(first_re, cells[0]):
            rows.append(cells)
    return rows


def mocks_missing(root, task_dir, text):
    """Sổ MOCKS.md: dòng chờ task này (module: cả task đã DONE) phải VERIFIED và file mock đã xoá."""
    d = task_field(text, "Module").split(" ")[0].strip("`/")
    module = bool(d) and not d.upper().startswith("N/A")
    book = os.path.join(root, d, "MOCKS.md") if module else os.path.join(task_dir, "MOCKS.md")
    task = os.path.basename(task_dir)
    waits = {task}
    for r in table_rows(os.path.join(root, d, "MODULE.md"), r"T-\d+$") if module else []:
        if len(r) >= 7 and (r[5] == task or r[6].upper().startswith("DONE")):
            waits |= {r[0], r[5]} - {""}
    miss = []
    for r in table_rows(book, r"MK-\d+$"):
        if len(r) < 6 or (module and r[4] not in waits):
            continue
        if r[5].upper() != "VERIFIED":
            miss.append(f"{r[0]} chưa VERIFIED ({r[5] or 'trống'})")
        if r[1] and os.path.exists(os.path.join(root, r[1])):
            miss.append(f"{r[0]} file mock {r[1]} chưa xoá")
    rel = os.path.relpath(book, root)
    return [f"{rel}: {m} (SWAP: nối BE thật, xoá mock, E2E PASS)" for m in miss]



# ---------- tìm code có mục tiêu: chặn quét mù cả repo (trừ Lead, Scout khi init / kb) ----------

SCAN_HINT = ("không quét cả repo. Tìm theo thứ tự: CONTEXT.md → KB docs/ + chỉ mục hàm docs/functions/ → "
             "graphify explain|affected → mở đúng file hoặc tìm trong thư mục cụ thể (vd app/services/). Thiếu thông tin → trả `HỎI LEAD: <cần gì>`")
VALUE_OPTS = {"-e", "-f", "-m", "-A", "-B", "-C", "--include", "--exclude", "--exclude-dir", "-g", "--glob", "-t", "--type",
              "-T", "--type-not", "--max-count", "--context", "--maxdepth", "-maxdepth", "-name", "-iname", "-path", "-type"}


def pipe_segments(cmd):
    """[(token, có nhận dữ liệu từ pipe không)] theo từng segment."""
    out = []
    for line in cmd.splitlines():
        try:
            lx = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lx.whitespace_split = True
            toks = list(lx)
        except ValueError:
            toks = line.split()
        cur, piped, prev = [], False, None
        for t in toks + [";"]:
            if t in OPERATORS or t in (";", "&&", "||", "|", "&"):
                if cur:
                    out.append((cur, piped))
                piped, cur = t == "|", []
            else:
                cur.append(t)
    return out


def positional(args):
    out, skip = [], False
    for t in args:
        if skip:
            skip = False
        elif t in VALUE_OPTS:
            skip = True
        elif not t.startswith("-"):
            out.append(t)
    return out


def scan_free(role, cwd):
    return not role or (role == "scout" and stage_value(cwd) is None)


def is_whole_repo(p, cwd):
    """p là gốc repo (hoặc thư mục cha của gốc) → tìm ở đây = quét cả repo."""
    full = os.path.normpath(os.path.join(cwd, os.path.expanduser(p or ".")))
    tops = {os.path.normpath(t) for t in repo_tops(cwd)}
    root = find_root(cwd)
    if root:
        tops.add(os.path.normpath(root))
    return full in tops or any(t.startswith(full.rstrip(os.sep) + os.sep) for t in tops)


def blind_bash(cmd, cwd):
    """Lý do nếu lệnh Bash là quét mù cả repo, ngược lại None."""
    for tk, piped in pipe_segments(cmd):
        while tk and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tk[0]):
            tk = tk[1:]
        if not tk:
            continue
        fc, args = os.path.basename(tk[0]), tk[1:]
        if fc == "git" and args[:1] == ["grep"]:
            fc, args = "git-grep", args[1:]
        pos = positional(args)
        if fc in ("grep", "egrep", "fgrep"):
            rec = any(a in ("-r", "-R", "--recursive", "--dereference-recursive") or re.match(r"^-[a-zA-Z]*[rR][a-zA-Z]*$", a) for a in args)
            paths = pos if "-e" in args or "-f" in args else pos[1:]
            if rec and (not paths or any(is_whole_repo(p, cwd) for p in paths)):
                return f"`{fc} -r` cả repo"
        elif fc in ("rg", "ag", "ack"):
            paths = pos if "-e" in args else pos[1:]
            if not piped and (not paths or any(is_whole_repo(p, cwd) for p in paths)):
                return f"`{fc}` cả repo"
        elif fc == "git-grep":
            if "--" not in args:
                return "`git grep` không giới hạn đường dẫn"
        elif fc == "find":
            paths = [a for a in args if not a.startswith("-")][:1]
            deep = next((int(args[i + 1]) for i, a in enumerate(args[:-1]) if a in ("-maxdepth", "--maxdepth") and args[i + 1].isdigit()), None)
            if (not paths or is_whole_repo(paths[0], cwd)) and (deep is None or deep > 2):
                return "`find` cả repo"
        elif fc == "ls" and any(re.match(r"^-[a-zA-Z]*R", a) for a in args):
            if not pos or any(is_whole_repo(p, cwd) for p in pos):
                return "`ls -R` cả repo"
        elif fc == "tree" and (not pos or any(is_whole_repo(p, cwd) for p in pos)) and "-L" not in args:
            return "`tree` cả repo"
    return None


def check_blind_scan(tool, ti, role, cwd):
    if scan_free(role, cwd):
        return
    why = None
    if tool == "Grep" and is_whole_repo(ti.get("path") or "", cwd):
        why = "Grep cả repo (thêm path thư mục cụ thể)"
    elif tool == "Glob" and is_whole_repo(ti.get("path") or "", cwd) and (ti.get("pattern") or "").startswith("**"):
        why = "Glob **/* cả repo"
    elif tool == "Bash":
        why = blind_bash(ti.get("command", ""), cwd)
    if why:
        block(f"{why}: {SCAN_HINT}")


# ---------- lệnh không tự dừng: làm agent (và Lead đang chờ agent) treo mãi ----------

FOREVER = [
    (re.compile(r"\bdocker(-compose|\s+compose)\s+(\S+\s+)*up\b(?!.*(\s-d\b|--detach|--wait|--abort-on-container-exit|--exit-code-from))"), "docker compose up không -d", "docker compose up -d <service>"),
    (re.compile(r"\btail\s+(-\w*f\w*|--follow)\b"), "tail -f", "tail -n 200 <file>"),
    (re.compile(r"(^|[;&|]\s*)watch\s"), "watch", "chạy lệnh 1 lần"),
    (re.compile(r"\b(npm|pnpm|yarn|bun)\s+(run\s+)?(dev|start|serve|watch)\b"), "dev server", "build / test 1 lần, hoặc chạy nền có timeout"),
    (re.compile(r"\b(rails|bin/rails)\s+(s|server)\b|\bphp\s+artisan\s+serve\b|\bnodemon\b"), "server chạy mãi", "chạy test thay vì mở server"),
    (re.compile(r"(--watch\b|\bvitest(?!\s+run)(\s|$))"), "test chế độ watch", "vitest run / jest (không --watch)"),
]


def check_forever(cmd):
    """Chặn lệnh không tự kết thúc (mọi người, kể cả Lead): agent đứng chờ mãi, Lead chờ agent mãi."""
    flat = " ".join(unquoted(cmd).split())
    if re.search(r"\btimeout\s+\d+", flat) or flat.rstrip().endswith("&"):
        return
    for rx, what, alt in FOREVER:
        if rx.search(flat):
            block(f"{what}: lệnh không tự dừng sẽ làm treo. Dùng: {alt} (hoặc bọc `timeout <giây> ...`)")

def check_stage_change(new_stage, cwd):
    """Lead đổi giai đoạn: TASK.md (task mới nhất) phải đủ điều kiện."""
    root = find_root(cwd)
    base = os.path.join(root, DOCS_DIR) if root else ""
    if not root or not new_stage or not os.path.isdir(base):
        return
    tasks = [os.path.join(base, d, "TASK.md") for d in os.listdir(base) if os.path.isfile(os.path.join(base, d, "TASK.md"))]
    if not tasks:
        return
    latest = max(tasks, key=os.path.getmtime)
    miss = gate_missing(new_stage, open(latest, encoding="utf-8", errors="ignore").read())
    cur = stage_value(cwd)
    if cur in ("S2", "S3", "S4", "S5") and new_stage != cur:
        sp = os.path.join(os.path.dirname(latest), "board", "SUMMARY.md")
        text = open(sp, encoding="utf-8", errors="ignore").read() if os.path.isfile(sp) else ""
        if not re.search(rf"(?m)^##\s+{cur}\b", text):
            miss.append(f"tóm tắt giai đoạn {cur} (mục `## {cur}` trong board/SUMMARY.md: quyết định, kết quả, việc còn mở) "
                        "- giai đoạn sau chỉ đọc tóm tắt, cần chi tiết thì query board")
    if new_stage == "S3":
        n = open_whys(root, os.path.basename(os.path.dirname(latest)))
        if n:
            miss.append(f"{n} WHY chưa được cả team đồng ý (board.py status)")
        text = open(latest, encoding="utf-8", errors="ignore").read()
        ddir = os.path.join(os.path.dirname(latest), "design")
        has = lambda rx: os.path.isdir(ddir) and any(re.match(rx, f) for f in os.listdir(ddir))
        yes = lambda k: (task_field(text, k).split() or [""])[0].upper() == "YES"
        if yes("Workflow") and not has(r"^workflow\.md$"):
            miss.append("Workflow: YES nhưng chưa có design/workflow.md")
        if yes("UI mockup") and not has(r"^mockup-.+\.html$"):
            miss.append("UI mockup: YES nhưng chưa có design/mockup-<màn>.html")
        miss += product_gate(root, "S3", (task_field(text, "Loại").split() or [""])[0].upper() == "APP")
        miss += module_gate(root, "S3", text)
    if new_stage == "S5":
        text = open(latest, encoding="utf-8", errors="ignore").read()
        if (task_field(text, "E2E").split() or [""])[0].upper() == "PASS":
            miss += e2e_evidence_missing(root, os.path.basename(os.path.dirname(latest)))
    if new_stage == "S6":
        text = open(latest, encoding="utf-8", errors="ignore").read()
        # "Cập nhật KB: YES" phải có file KB đổi thật (không chỉ lời khai)
        if (task_field(text, "Cập nhật KB").split() or [""])[0].upper() == "YES" and kb_changed(root) is False:
            miss.append("Cập nhật KB: YES nhưng không có file KB nào trong docs/ đổi so với nhánh gốc "
                        "(không tính agent-tasks/, testing/, LESSONS.md, SPEC.md). Cập nhật KB hoặc ghi KHÔNG CẦN + lý do")
        miss += product_gate(root, "S6", False)
        miss += module_gate(root, "S6", text)
        miss += mocks_missing(root, os.path.dirname(latest), text)
    if miss:
        block(f"chưa đủ điều kiện sang {new_stage}. Thiếu trong {os.path.relpath(latest, root)}: {'; '.join(miss)}")


def latest_task(root):
    base = os.path.join(root, DOCS_DIR)
    tasks = [os.path.join(base, d, "TASK.md") for d in os.listdir(base)] if os.path.isdir(base) else []
    tasks = [t for t in tasks if os.path.isfile(t)]
    return max(tasks, key=os.path.getmtime) if tasks else None


def load_board():
    import importlib.util
    spec = importlib.util.spec_from_file_location("board", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "board.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_plan(ti, cwd):
    """Lead gọi agent: S3-S5 phải có danh sách bước; S3 có FE_PATHS thì BE ∥ FE hoặc ghi lý do. Qua thì ▶ bước của agent đó."""
    root = find_root(cwd)
    path = latest_task(root) if root else None
    if not path:
        return
    task, stage = os.path.basename(os.path.dirname(path)), stage_value(cwd)
    dbp = os.path.join(root, ".agent-team", "board.db")
    rows = []
    if os.path.isfile(dbp):
        try:
            con = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True, timeout=5)
            rows = con.execute("SELECT * FROM plan_steps WHERE task=?", (task,)).fetchall()
            cols = [c[0] for c in con.execute("SELECT * FROM plan_steps LIMIT 0").description]
            con.close()
            rows = [dict(zip(cols, r)) for r in rows]
        except sqlite3.Error:
            rows = []
    if stage in ("S3", "S4", "S5") and not rows:
        block(f"chưa có danh sách bước cho {task}. Trước khi gọi agent: "
              f"`board.py plan {task} --set \"bước 1 @backend-dev ∥ bước 2 @frontend-dev | bước 3 @test-executor\"`, "
              "rồi in `progress.py --list` vào chat cho user")
    if stage == "S3" and rows and cfg_value(root, "FE_PATHS"):
        groups = {}
        for r in rows:
            groups.setdefault(r.get("grp"), set()).add(r.get("role"))
        par = any(g is not None and {"backend-dev", "frontend-dev"} <= v for g, v in groups.items())
        why = task_field(open(path, encoding="utf-8", errors="ignore").read(), "Song song")
        if not par and not why:
            block("S3 có FE_PATHS: cho backend-dev ∥ frontend-dev chạy cùng lúc (cùng nhóm ∥ trong `board.py plan`), "
                  "hoặc ghi lý do vào TASK.md: `- Song song: KHÔNG - <vì sao: FE chờ API nào / task chỉ BE / chỉ FE>`")
    role = (ti.get("subagent_type") or "").strip().lower().split(":")[-1]
    if rows and role:
        try:
            os.chdir(root)
            board = load_board()
            db = board.connect()
            board.begin_agent(db, task, role, root)
            db.close()
        except BaseException as e:  # ghi trạng thái lỗi thì bỏ qua, không chặn gọi agent
            if os.environ.get("AGENT_TEAM_DEBUG") == "1":
                sys.stderr.write(f"[agent-team guard] begin_agent: {e!r}\n")


def check_stage(path, cwd):
    sz = stage_zones(cwd)
    loaded = load_zones(cwd) if sz is not None else None
    if not loaded or not path:
        return
    root, zones = loaded
    rel = os.path.relpath(full_path(path, cwd), root).replace("\\", "/")
    z = zone_of(rel, zones)
    if z and z not in sz:
        block(f"giai đoạn hiện tại không được sửa vùng '{z}' ('{rel}'). Cần sửa → báo Lead đổi giai đoạn")


# ---------- log agent_type + kiểm tra diff sau khi tool chạy (PostToolUse) ----------

def debug_log(event, data, role, cwd):
    """AGENT_TEAM_DEBUG=1: ghi lại hook nhận được gì để biết agent_type có tới không."""
    if os.environ.get("AGENT_TEAM_DEBUG") != "1":
        return
    root = find_root(cwd) or os.path.abspath(cwd)
    d = os.path.join(root, ".agent-team")
    os.makedirs(d, exist_ok=True)
    rec = {"t": int(time.time()), "event": event, "tool": data.get("tool_name"), "role": role,
           "agent_type": data.get("agent_type"), "subagent_type": data.get("subagent_type"),
           "agent_id": data.get("agent_id"), "keys": sorted(data.keys())}
    with open(os.path.join(d, "guard.log"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def dirty_files(top):
    """{path tương đối: (mtime_ns, size)} cho mọi file đang khác HEAD hoặc chưa track."""
    try:
        r = subprocess.run(["git", "status", "--porcelain", "-z", "-uall"], cwd=top,
                           capture_output=True, text=True, timeout=20)
    except Exception:
        return {}
    out, ents, i = {}, r.stdout.split("\0"), 0
    while i < len(ents):
        e = ents[i]
        i += 1
        if len(e) < 4:
            continue
        if e[0] in "RC":
            i += 1
        try:
            st = os.stat(os.path.join(top, e[3:]))
            out[e[3:]] = (st.st_mtime_ns, st.st_size)
        except OSError:
            out[e[3:]] = (None, None)
    return out


def snap_dir(top, data):
    _, gd = git(top, "rev-parse", "--absolute-git-dir")
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{data.get('session_id', 's')}-{data.get('agent_id', 'main')}")
    return os.path.join(gd or top, "agent-team-snap", key)


def watched(role, cwd):
    """Role cần theo dõi diff: role chỉ đọc, hoặc dev/tester khi có config vùng."""
    if stage_zones(cwd) is not None or role in READONLY_ROLES:
        return True
    return role in OWNER_ZONE and bool(load_zones(cwd))


def take_snapshot(data, role, cwd):
    for top in repo_tops(cwd):
        sd = snap_dir(top, data)
        shutil.rmtree(sd, ignore_errors=True)
        os.makedirs(os.path.join(sd, "files"))
        meta = {}
        for i, (rel, (mt, sz)) in enumerate(dirty_files(top).items()):
            saved = False
            src = os.path.join(top, rel)
            if sz is not None and sz <= SNAP_MAX and os.path.isfile(src):
                shutil.copy2(src, os.path.join(sd, "files", str(i)))
                saved = str(i)
            meta[rel] = [mt, sz, saved]
        json.dump(meta, open(os.path.join(sd, "meta.json"), "w"))


def path_allowed(rel, role, cwd):
    zones = (load_zones(cwd) or (None, None))[1]
    z = zone_of(rel, zones) if zones else None
    sz = stage_zones(cwd)
    if sz is not None and z and z not in sz:
        return False
    if not role:
        return True
    if rel.startswith("docs/"):
        return docs_verdict(rel, role, cwd) is None
    if role in READONLY_ROLES:
        return False
    return z is None or z == OWNER_ZONE.get(role)


def revert(top, rel, pre):
    """Trả file về trạng thái trước lệnh. Trả về True nếu hoàn tác được."""
    dst = os.path.join(top, rel)
    if rel in pre:
        saved = pre[rel][2]
        if saved is False:
            return False
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(pre["_dir"], "files", saved), dst)
        return True
    if git(top, "ls-files", "--error-unmatch", "--", rel)[0] == 0:
        return git(top, "restore", "--staged", "--worktree", "--source=HEAD", "--", rel)[0] == 0
    try:
        os.remove(dst)
        return True
    except OSError:
        return False


ACT_SQL = """CREATE TABLE IF NOT EXISTS act_writes (path TEXT NOT NULL, role TEXT NOT NULL, at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS act_bash (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, start REAL NOT NULL, end REAL);"""


def act_db(cwd):
    """board.db của thư mục (chính hoặc worktree): ai ghi file nào, ai đang chạy Bash (để không hoàn tác nhầm khi nhiều agent cùng làm)."""
    root = find_root(cwd)
    if not root:
        return None
    try:
        os.makedirs(os.path.join(root, ".agent-team"), exist_ok=True)
        con = sqlite3.connect(os.path.join(root, ".agent-team", "board.db"), timeout=5)
        con.executescript(ACT_SQL)
        return con
    except sqlite3.Error:
        return None


def act_write(path, role, cwd):
    con = act_db(cwd)
    if con:
        try:
            full = os.path.realpath(path if os.path.isabs(path) else os.path.join(cwd, path))
            con.execute("DELETE FROM act_writes WHERE at < ?", (int(time.time()) - 86400,))
            con.execute("INSERT INTO act_writes VALUES(?,?,?)", (full, role or "lead", time.time()))
            con.commit()
        finally:
            con.close()


def act_bash(role, cwd, end=False):
    con = act_db(cwd)
    if not con:
        return
    try:
        now, r = time.time(), role or "lead"
        if end:
            row = con.execute("SELECT id FROM act_bash WHERE role=? AND end IS NULL ORDER BY id DESC LIMIT 1", (r,)).fetchone()
            if row:
                con.execute("UPDATE act_bash SET end=? WHERE id=?", (now, row[0]))
        else:
            con.execute("DELETE FROM act_bash WHERE start < ? AND (end IS NOT NULL OR start < ?)", (now - 86400, now - 86400))
            con.execute("UPDATE act_bash SET end=? WHERE role=? AND end IS NULL", (now, r))  # role bắt đầu lệnh mới = lệnh trước đã xong
            con.execute("INSERT INTO act_bash(role, start) VALUES(?,?)", (r, now))
        con.commit()
    finally:
        con.close()


def others_activity(role, cwd, since):
    """(file người khác ghi bằng Edit/Write từ `since`, có người khác chạy Bash trùng khoảng này)."""
    con = act_db(cwd)
    if not con:
        return set(), False
    try:
        me = role or "lead"
        files = {r[0] for r in con.execute("SELECT path FROM act_writes WHERE role != ? AND at >= ?", (me, since))}
        now = time.time()  # Bash mở quá 11 phút (lệnh tối đa 10 phút, PostToolUse không tới khi lỗi) coi như đã xong
        busy = con.execute("SELECT 1 FROM act_bash WHERE role != ? AND start <= ? AND ((end IS NULL AND start >= ?) OR end > ?) LIMIT 1",
                           (me, now, now - 660, since)).fetchone() is not None
        return files, busy
    finally:
        con.close()


def post_check(data, role, cwd):
    act_bash(role, cwd, end=True)
    if not watched(role, cwd):
        return
    root = find_root(cwd)
    root = os.path.realpath(root) if root else None
    bad, stuck, unsure = [], [], []
    for top in repo_tops(cwd):
        top = os.path.realpath(top)
        sd = snap_dir(top, data)
        try:
            pre = json.load(open(os.path.join(sd, "meta.json")))
            since = os.path.getmtime(os.path.join(sd, "meta.json"))
        except Exception:
            continue
        pre["_dir"] = sd
        others, others_bash = others_activity(role, cwd, since)
        for rel, (mt, sz) in dirty_files(top).items():
            if rel in pre and tuple(pre[rel][:2]) == (mt, sz):
                continue
            rr = os.path.relpath(os.path.join(top, rel), root or top).replace("\\", "/")
            if path_allowed(rr, role, cwd):
                continue
            if os.path.realpath(os.path.join(top, rel)) in others:
                continue  # agent / Lead khác ghi (Edit / Write) trong lúc lệnh này chạy: không phải của role này
            if others_bash:
                unsure.append(rr)  # có người khác cũng chạy Bash cùng lúc: không biết ai ghi → không hoàn tác, báo Lead
                continue
            (bad if revert(top, rel, pre) else stuck).append(rr)
        shutil.rmtree(sd, ignore_errors=True)
    if unsure and root:
        with open(os.path.join(root, ".agent-team", "guard.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": int(time.time()), "event": "unsure_write", "role": role, "files": unsure[:20]},
                               ensure_ascii=False) + "\n")
    if bad or stuck:
        msg = f"role '{role}' vừa ghi ngoài vùng của mình."
        if bad:
            msg += f" Đã hoàn tác: {', '.join(bad[:5])}."
        if stuck:
            msg += f" KHÔNG hoàn tác được (báo Lead): {', '.join(stuck[:5])}."
        block(msg + " Post lên board và @chủ vùng sửa.")


def effective_cwd(tool, ti, cwd):
    """Worktree của task (WORKTREE_DIR): tính gốc repo theo file được sửa / `cd <dir> &&` đầu lệnh, không theo cwd của phiên."""
    cand = ""
    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob") and path:
        full = path if os.path.isabs(path) else os.path.join(cwd, path)
        cand = full if os.path.isdir(full) else os.path.dirname(full)
    elif tool == "Bash":
        segs = parse(ti.get("command", "") or "")
        if segs and segs[0] and segs[0][0] == "cd" and len(segs[0]) > 1:
            cand = os.path.join(cwd, os.path.expanduser(segs[0][1]))
    if cand:
        r = find_root(cand)
        if r and r != find_root(cwd):
            return r
    return cwd


def pool_active(cwd):
    """Phiên chính đang điều phối nhiều task (bảng pool có task chưa DONE)."""
    root = find_root(cwd)
    p = os.path.join(root, ".agent-team", "board.db") if root else ""
    if not p or not os.path.isfile(p):
        return False
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        n = con.execute("SELECT count(*) FROM pool WHERE state NOT IN ('DONE')").fetchone()[0]
        con.close()
        return n > 0
    except sqlite3.Error:
        return False


def touches_hidden(text):
    return bool(HIDDEN_RE.search(text or ""))


POST = len(sys.argv) > 1 and sys.argv[1] == "post"


SYS_PKG_RE = re.compile(r"\b((apt-get|apt|apk|yum|dnf)\s+(install|add|remove|upgrade)|pecl\s+install|docker-php-ext-(install|enable))\b")


def check_shared_container(cmd, cwd):
    """CLONE_MODE=schema: mọi worktree chung 1 container app → không cài package hệ thống."""
    root = find_root(cwd)
    if not root or cfg_value(root, "CLONE_MODE") != "schema":
        return
    if SYS_PKG_RE.search(cmd):
        block("container app dùng chung cho mọi task: không cài package hệ thống. Cần thì báo GAP → task riêng sửa Dockerfile, rebuild khi pool rảnh")


def bind_worktree(data, role, cwd, tool):
    """Agent đã làm ở 1 worktree thì không được sửa / chạy lệnh ở worktree khác (gắn theo agent_id)."""
    key = data.get("agent_id")
    if not role or not key or tool not in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash"):
        return
    path = (data.get("tool_input") or {}).get("file_path") or (data.get("tool_input") or {}).get("notebook_path") or ""
    d = os.path.dirname(os.path.join(cwd, path)) if path else cwd
    while not os.path.isfile(os.path.join(d, ".git")):
        if os.path.dirname(d) == d or os.path.isdir(os.path.join(d, ".git")):
            return
        d = os.path.dirname(d)
    cwd = d
    try:
        m = re.search(r"gitdir:\s*(.+?)/\.git/worktrees/", open(os.path.join(d, ".git"), encoding="utf-8").read())
    except OSError:
        return
    if not m:
        return
    p = os.path.join(m.group(1), ".agent-team", "agent_worktree.json")
    try:
        seen = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    prev = seen.get(key)
    if prev and prev != cwd:
        block(f"agent này làm ở worktree '{os.path.basename(prev)}', không được đụng worktree '{os.path.basename(cwd)}' của task khác")
    if not prev:
        seen[key] = cwd
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(seen, open(p, "w", encoding="utf-8"))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    role = norm_role(data)
    cwd = effective_cwd(tool, ti, cwd)

    debug_log("post" if POST else "pre", data, role, cwd)
    if POST:
        post_check(data, role, cwd)
        sys.exit(0)

    if tool in ("Agent", "Task") and not role:
        if not pool_active(cwd):  # điều phối nhiều task: danh sách bước nằm trong từng worktree
            check_plan(ti, cwd)
        sys.exit(0)

    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob"):
        if (is_secret_path(path) and not is_env_file(path)) or (is_secret_path(ti.get("glob", "")) and not is_env_file(ti.get("glob", ""))):
            block(f"không được đọc/sửa file nhạy cảm '{path or ti.get('glob')}'")

    bind_worktree(data, role, cwd, tool)

    # challenger không biết ticket: không đọc docs/ (TASK, board, CONTEXT, KB)
    if role == "challenger":
        if (tool in ("Read", "Grep", "Glob") and (docs_rel(path, cwd) is not None or "agent-tasks" in (ti.get("glob") or "") + (ti.get("pattern") or "")
                                                   )) or (tool == "Bash" and "agent-tasks" in ti.get("command", "")):
            block("challenger không được đọc docs/ (TASK, board, CONTEXT). Chỉ dùng yêu cầu gốc Lead đưa và diff/code")

    if tool in ("Grep", "Glob", "Bash"):
        check_blind_scan(tool, ti, role, cwd)

    # state DB của task: agent không được đọc/ghi (Lead thì được)
    if role and tool in ("Read", "Grep", "Glob", "Write", "Edit", "MultiEdit", "NotebookEdit"):
        if touches_hidden(full_path(path, cwd) + "/") or touches_hidden(ti.get("glob", "")):
            block("không được đụng .agent-team/ (state DB của task)")

    if tool == "Bash":
        cmd = ti.get("command", "")
        if board_segments(cmd.split("\n", 1)[0]):
            cmd = strip_heredocs(cmd)
        check_board(cmd, role)
        if role and re.search(r"\bpool\.py\b", cmd):
            block("pool.py (điều phối task, worktree, merge) chỉ Lead dùng")
        check_forever(cmd)
        if role and any(first_cmd(tk) in PERM_CMDS for tk in parse(cmd)):
            block("không được đổi quyền file (chmod/chown...), nhờ Lead")
        check_graphify(cmd, role)
        if role and touches_hidden(cmd):
            block("không được đụng .agent-team/ (state DB của task)")
        if role and "agent-tasks" in cmd and (
                re.search(r">|\btee\b|\bsed\s+(-\w*\s+)*-i|\b(mv|cp|rm|touch|truncate)\b", unquoted(cmd))):
            block("docs/agent-tasks (TASK, board) chỉ Lead ghi, trả kết quả cho Lead")
        if not role and STAGE_WRITE_RE.search(cmd):
            m = STAGE_VALUE_RE.search(cmd)
            if not m:
                block("ghi giai đoạn theo dạng `echo S<n> > .agent-team/stage`")
            check_stage_change(m.group(1), cwd)
        check_secret_tokens(cmd)
        check_env_dump(cmd)
        check_db(cmd)
        check_shared_container(cmd, cwd)
        check_git(cmd, cwd, role)
        check_rm(cmd)
        if role in READONLY_ROLES:
            check_readonly_bash(cmd, role)
        for tgt in bash_write_targets(cmd):
            check_migration_new(tgt, cwd)
            check_stage(tgt, cwd)
            check_owner(tgt, cwd, role)
            check_docs(tgt, cwd, role)

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        check_migration_new(path, cwd)
        check_stage(path, cwd)
        if not role and tool == "Write" and path.replace("\\", "/").endswith(".agent-team/stage"):
            check_stage_change((ti.get("content") or "").strip().upper(), cwd)

    if role and tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        if role in READONLY_ROLES:
            check_readonly_write(path, cwd, role)
        check_owner(path, cwd, role)
        check_docs(path, cwd, role)

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit") and path:
        act_write(path, role, cwd)
    if tool == "Bash":
        act_bash(role, cwd)
        if watched(role, cwd):
            take_snapshot(data, role, cwd)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # lỗi guard thì không chặn, chỉ cảnh báo
        sys.stderr.write(f"[agent-team guard] warning: {e}\n")
        sys.exit(0)
