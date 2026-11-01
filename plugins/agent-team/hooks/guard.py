#!/usr/bin/env python3
"""agent-team guard - PreToolUse hook. Exit 2 = chặn, lý do in ra stderr."""
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED_BRANCHES = {"main", "master", "develop"}
READONLY_ROLES = {
    "business-analyst", "solution-architect", "technical-architect",
    "code-reviewer", "solution-reviewer", "test-reviewer", "security",
}
DOCS_DIR = "docs/agent-tasks/"
SCORES_DIR = ".agent-team/scores/"
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


def check_git(cmd, cwd):
    for tk in parse(cmd):
        if "git" not in tk or first_cmd(tk) in READ_ONLY_FIRST - {"git"}:
            continue
        tk = tk[tk.index("git"):]
        sub = next((t for t in tk[1:] if not t.startswith("-")), "")
        args = tk[tk.index(sub) + 1:] if sub in tk else []
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
    if cmd == "git":
        sub = next((t for t in tk[1:] if not t.startswith("-")), "")
        return sub in GIT_READ
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


def check_readonly_write(path, cwd, role):
    full = full_path(path, cwd) + "/"
    if "/" + DOCS_DIR not in full and "/" + SCORES_DIR not in full:
        block(f"role '{role}' chỉ được post vào board hoặc ghi điểm của mình")


# ---------- debate board + điểm chấm (mọi role, trừ Lead) ----------

def check_board(tool, path, cwd, role):
    full = full_path(path, cwd)
    if "/" + DOCS_DIR in full + "/":
        if "/board/" not in full:
            block("TASK.md và file ngoài board/ chỉ Lead được ghi")
        if tool != "Write":
            block("không sửa bài đã post, hãy post bài mới")
        if not re.match(rf"^S[1-6]-R\d+-{re.escape(role)}-\d+\.md$", os.path.basename(full)):
            block(f"tên bài post phải là S<giai đoạn>-R<vòng>-{role}-<n>.md (chỉ post bằng tên mình)")
        if os.path.exists(full):
            block("bài post đã tồn tại, không ghi đè, tăng <n> lên")
    if "/" + SCORES_DIR in full + "/":
        if tool != "Write" or os.path.basename(full) != f"{role}.md":
            block("chỉ được ghi điểm của mình, không đọc/sửa điểm người khác")
        if os.path.exists(full):
            block("đã chấm điểm rồi, không sửa")


def touches_hidden(text):
    return bool(HIDDEN_RE.search(text or ""))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    role = norm_role(data)

    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob"):
        if is_secret_path(path) or is_secret_path(ti.get("glob", "")):
            block(f"không được đọc/sửa file nhạy cảm '{path or ti.get('glob')}'")

    # điểm chấm + state DB clone: agent không được đọc (Lead thì được)
    if role and tool in ("Read", "Grep", "Glob", "Edit", "MultiEdit", "NotebookEdit"):
        if touches_hidden(full_path(path, cwd) + "/") or touches_hidden(ti.get("glob", "")):
            block("không được đọc .agent-team/ (điểm chấm của role khác, state DB clone)")

    if tool == "Bash":
        cmd = ti.get("command", "")
        if role and touches_hidden(cmd):
            block("không được đụng .agent-team/ (điểm chấm của role khác, state DB clone)")
        if role and "agent-tasks" in cmd and (
                re.search(r">|\btee\b|\bsed\s+(-\w*\s+)*-i|\b(mv|cp|rm|touch|truncate)\b", unquoted(cmd))):
            block("board chỉ được post bằng Write tool, không ghi/xoá bằng Bash")
        check_secret_tokens(cmd)
        check_env_dump(cmd)
        check_db(cmd)
        check_git(cmd, cwd)
        check_rm(cmd)
        if role in READONLY_ROLES:
            check_readonly_bash(cmd, role)

    if role and tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        if role in READONLY_ROLES:
            check_readonly_write(path, cwd, role)
        check_board(tool, path, cwd, role)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # lỗi guard thì không chặn, chỉ cảnh báo
        sys.stderr.write(f"[agent-team guard] warning: {e}\n")
        sys.exit(0)
