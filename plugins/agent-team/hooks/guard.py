#!/usr/bin/env python3
"""agent-team guard - PreToolUse hook. Exit 2 = chặn, lý do in ra stderr."""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

PROTECTED_BRANCHES = {"main", "master", "develop"}
READONLY_ROLES = {
    "business-analyst", "solution-architect", "technical-architect",
    "test-designer", "code-reviewer", "security", "scout",
}
DOCS_DIR = "docs/agent-tasks/"
OWNER_ZONE = {"backend-dev": "be", "frontend-dev": "fe", "test-executor": "test"}
_BA = {"business-analyst"}
_ARCH = {"solution-architect", "technical-architect"}
# Knowledge base: thư mục/file -> role được ghi. Lead ghi được tất cả. Không nằm trong danh sách = chỉ Lead.
KB_OWNERS = [
    ("docs/domain/", _BA), ("docs/business-rules.md", _BA), ("docs/domain-model.md", _BA),
    ("docs/roles-and-permissions.md", _BA), ("docs/glossary.md", _BA),
    ("docs/project-overview.md", _ARCH), ("docs/architecture.md", _ARCH), ("docs/tech-stack.md", _ARCH),
    ("docs/architecture/", _ARCH), ("docs/engineering/", _ARCH), ("docs/decisions/", _ARCH),
    ("docs/integrations/", _ARCH),
    ("docs/api/", _ARCH | {"backend-dev"}), ("docs/database/", _ARCH | {"backend-dev"}),
    ("docs/modules/", _BA | _ARCH | {"backend-dev", "frontend-dev"}),
    ("docs/testing/", {"test-designer", "test-executor"}),
    ("docs/security/", {"security"}),
]
COMMIT_MSG_RE = re.compile(r"^\[[a-z][a-z-]*\] [\w.-]+: \S.*$")
TRAILER_RE = re.compile(r"(?i)signed-off-by|co-authored-by|reviewed-by|generated-by|generated with")
STAGE_WRITE_RE = re.compile(r">+\s*['\"]?\S*\.agent-team/stage")
STAGE_VALUE_RE = re.compile(r"(?:echo|printf)\s+(?:-\w+\s+)*['\"]?(S[1-6])\b")
# Điều kiện (đọc từ TASK.md) trước khi Lead sang giai đoạn mới
GATE_CLASS = {"NHỎ", "VỪA", "LỚN"}
TEST_FILE_RE = re.compile(r"(^|/)(__tests__|__mocks__)/|(_spec|_test)\.\w+$|\.(spec|test)\.\w+$|(^|/)test_[^/]+\.py$")
STAGE_ZONES = {"S1": set(), "S2": set(), "S3": {"be", "fe"}, "S4": {"test"}}
CODE_GRAPH = "code-graph.py"
CODE_GRAPH_READ = {"who-uses", "uses", "explain"}
PERM_CMDS = {"chmod", "chown", "chgrp", "setfacl", "chattr"}
SNAP_MAX = 2_000_000
WRITE_CMDS = {"tee", "mv", "cp", "rm", "touch", "truncate", "install", "dd", "ln"}
HIDDEN_RE = re.compile(r"(^|[\s/'\"=])\.agent-team(/|\s|$|['\"])")
CLONE_SCRIPT = "agent-db-clone"

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
                if is_secret_path(part):
                    block(f"không được đụng file nhạy cảm '{part}' (.env, key, dump DB...)")


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
            block("migration/lệnh DB chỉ được chạy qua agent-db-clone.sh (DB clone), không đụng DB thật")


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


def check_git(cmd, cwd):
    hook_cwd = cwd
    cur = cwd
    for tk in parse(cmd):
        if first_cmd(tk) == "cd" and len(tk) > 1:
            cur = os.path.join(cur, os.path.expanduser(tk[1]))
            continue
        if "git" not in tk or first_cmd(tk) in READ_ONLY_FIRST - {"git"}:
            continue
        cwd, sub, args = git_target(tk[tk.index("git"):], cur)
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
    if any(t in FIX_FLAGS for t in tk[1:]):
        return False
    cmd = os.path.basename(tk[0])
    if cmd.startswith(CLONE_SCRIPT):
        return len(tk) > 1 and tk[1] in ("status", "test")
    if cmd == CODE_GRAPH:
        return len(tk) > 1 and tk[1] in CODE_GRAPH_READ
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
    for pre, roles in KB_OWNERS:
        if rel == pre or (pre.endswith("/") and rel.startswith(pre)):
            return roles
    return None


def docs_verdict(rel, role, cwd):
    """None nếu role được ghi rel trong docs/, ngược lại là lý do chặn."""
    if rel.startswith(DOCS_DIR):
        if role == "scout" and os.path.basename(rel) == "CONTEXT.md":
            return None
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
            miss.append("Loại (NHỎ/VỪA/LỚN)")
        if first("Loại") == "NHỎ":
            if not f("Tiêu chí nghiệm thu"):
                miss.append("Tiêu chí nghiệm thu")
        else:
            if not f("Phương án chốt"):
                miss.append("Phương án chốt")
            if first("Security duyệt solution") not in ("APPROVED", "N/A"):
                miss.append("Security duyệt solution: APPROVED")
    elif stage == "S5":
        if first("Kết quả test") != "PASS":
            miss.append("Kết quả test: PASS")
        if first("Lint/format") not in ("PASS", "N/A"):
            miss.append("Lint/format: PASS hoặc N/A")
    elif stage == "S6":
        if first("Code review") != "APPROVED":
            miss.append("Code review: APPROVED")
        if first("Security review") != "APPROVED":
            miss.append("Security review: APPROVED")
        if first("Cập nhật KB") not in ("YES", "KHÔNG"):
            miss.append("Cập nhật KB: YES hoặc KHÔNG CẦN")
    return miss


def check_stage_change(new_stage, cwd):
    """Lead đổi giai đoạn: TASK.md (task mới nhất) phải đủ điều kiện."""
    root = find_root(cwd)
    if not root or not new_stage:
        return
    tasks = [os.path.join(root, DOCS_DIR, d, "TASK.md") for d in os.listdir(os.path.join(root, DOCS_DIR))
             if os.path.isfile(os.path.join(root, DOCS_DIR, d, "TASK.md"))] if os.path.isdir(os.path.join(root, DOCS_DIR)) else []
    if not tasks:
        return
    latest = max(tasks, key=os.path.getmtime)
    miss = gate_missing(new_stage, open(latest, encoding="utf-8", errors="ignore").read())
    if miss:
        block(f"chưa đủ điều kiện sang {new_stage}. Thiếu trong {os.path.relpath(latest, root)}: {'; '.join(miss)}")


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


def post_check(data, role, cwd):
    if not watched(role, cwd):
        return
    root = find_root(cwd)
    root = os.path.realpath(root) if root else None
    bad, stuck = [], []
    for top in repo_tops(cwd):
        top = os.path.realpath(top)
        sd = snap_dir(top, data)
        try:
            pre = json.load(open(os.path.join(sd, "meta.json")))
        except Exception:
            continue
        pre["_dir"] = sd
        for rel, (mt, sz) in dirty_files(top).items():
            if rel in pre and tuple(pre[rel][:2]) == (mt, sz):
                continue
            rr = os.path.relpath(os.path.join(top, rel), root or top).replace("\\", "/")
            if path_allowed(rr, role, cwd):
                continue
            (bad if revert(top, rel, pre) else stuck).append(rr)
        shutil.rmtree(sd, ignore_errors=True)
    if bad or stuck:
        msg = f"role '{role}' vừa ghi ngoài vùng của mình."
        if bad:
            msg += f" Đã hoàn tác: {', '.join(bad[:5])}."
        if stuck:
            msg += f" KHÔNG hoàn tác được (báo Lead): {', '.join(stuck[:5])}."
        block(msg + " Post lên board và @chủ vùng sửa.")


def touches_hidden(text):
    return bool(HIDDEN_RE.search(text or ""))


POST = len(sys.argv) > 1 and sys.argv[1] == "post"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    role = norm_role(data)

    debug_log("post" if POST else "pre", data, role, cwd)
    if POST:
        post_check(data, role, cwd)
        sys.exit(0)

    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob"):
        if is_secret_path(path) or is_secret_path(ti.get("glob", "")):
            block(f"không được đọc/sửa file nhạy cảm '{path or ti.get('glob')}'")

    # state DB clone: agent không được đọc/ghi (Lead thì được)
    if role and tool in ("Read", "Grep", "Glob", "Write", "Edit", "MultiEdit", "NotebookEdit"):
        if touches_hidden(full_path(path, cwd) + "/") or touches_hidden(ti.get("glob", "")):
            block("không được đụng .agent-team/ (state DB clone)")

    if tool == "Bash":
        cmd = ti.get("command", "")
        if role and any(first_cmd(tk) in PERM_CMDS for tk in parse(cmd)):
            block("không được đổi quyền file (chmod/chown...), nhờ Lead")
        if role and any(os.path.basename(t) == CODE_GRAPH and (i + 1 >= len(tk) or tk[i + 1] not in CODE_GRAPH_READ)
                        for tk in parse(cmd) for i, t in enumerate(tk)):
            block("role chỉ được code-graph.py who-uses/uses/explain. build do Lead làm")
        if role and touches_hidden(cmd):
            block("không được đụng .agent-team/ (state DB clone)")
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
        check_git(cmd, cwd)
        check_rm(cmd)
        if role in READONLY_ROLES:
            check_readonly_bash(cmd, role)
        for tgt in bash_write_targets(cmd):
            check_stage(tgt, cwd)
            check_owner(tgt, cwd, role)
            check_docs(tgt, cwd, role)

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        check_stage(path, cwd)
        if not role and tool == "Write" and path.replace("\\", "/").endswith(".agent-team/stage"):
            check_stage_change((ti.get("content") or "").strip().upper(), cwd)

    if role and tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        if role in READONLY_ROLES:
            check_readonly_write(path, cwd, role)
        check_owner(path, cwd, role)
        check_docs(path, cwd, role)

    if tool == "Bash" and watched(role, cwd):
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
