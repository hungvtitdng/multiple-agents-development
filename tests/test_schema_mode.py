#!/usr/bin/env python3
"""CLONE_MODE=schema (v0.40): 1 container DB + 1 container app, mỗi worktree 1 DB riêng + exec -w đúng thư mục.
docker giả ghi lại lệnh. python3 tests/test_schema_mode.py"""
import os
import subprocess
import tempfile

SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "agent-db.sh")
fail = total = 0


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


def sh(cwd, *cmd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout


d = os.path.realpath(tempfile.mkdtemp())
main = os.path.join(d, "app")
os.makedirs(os.path.join(main, ".claude"))
os.makedirs(os.path.join(main, "vendor"))
open(os.path.join(main, "vendor", "autoload.php"), "w").write("<?php\n")
open(os.path.join(main, ".env"), "w").write("APP_KEY=x\n")
bin_dir = os.path.join(d, "bin")
os.makedirs(bin_dir)
log = os.path.join(d, "docker.log")
open(os.path.join(bin_dir, "docker"), "w").write(f'#!/bin/sh\necho "$@" >> {log}\n')
os.chmod(os.path.join(bin_dir, "docker"), 0o755)
cfg = ('CLONE_MODE=schema\nDB_ENGINE=mysql\nDB_SERVICE=mysql\nDB_NAME=cay\nAPP_SERVICE=app\n'
       'MIGRATE_CMD="php artisan migrate"\nSEED_CMD="php artisan db:seed"\nTEST_CMD="php artisan test"\n')
open(os.path.join(main, ".claude", "agent-team.config"), "w").write(cfg)
open(os.path.join(main, "composer.lock"), "w").write("{}\n")
open(os.path.join(main, ".gitignore"), "w").write("vendor\n.worktrees/\n.env\n")
sh(main, "git", "init", "-q", "-b", "master"), sh(main, "git", "config", "user.email", "t@t"), sh(main, "git", "config", "user.name", "t")
sh(main, "git", "add", "."), sh(main, "git", "commit", "-qm", "init")
wt = os.path.join(main, ".worktrees", "m6-t1")
sh(main, "git", "worktree", "add", "-q", wt, "-b", "agent/m6-t1")
env = {**os.environ, "PATH": bin_dir + os.pathsep + os.environ["PATH"]}


def run(cwd, *args):
    open(log, "w").close()
    r = subprocess.run(["bash", SH, *args], cwd=cwd, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr, open(log).read()


code, out, dk = run(wt, "up", "m6-t1")
check("up trong worktree: tạo DB cay_m6_t1 trên service mysql", code == 0 and "compose exec -T mysql" in dk and "CREATE DATABASE `cay_m6_t1`" in dk)
check("up: migrate + seed bằng exec -w /var/www/.worktrees/m6-t1, DB_DATABASE=cay_m6_t1",
      "exec -T -w /var/www/.worktrees/m6-t1 -e DB_DATABASE=cay_m6_t1 app sh -c php artisan migrate" in dk and "php artisan db:seed" in dk)
check("up: vendor là bản riêng của worktree (clone, không symlink)",
      not os.path.islink(os.path.join(wt, "vendor")) and os.path.isfile(os.path.join(wt, "vendor", "autoload.php")))
code, out, dk = run(wt, "up", "m6-t1")
check("up lần 2: DB đã có → dùng lại, chỉ migrate, không seed lại", "CREATE DATABASE" not in dk and "migrate" in dk and "db:seed" not in dk)
code, out, dk = run(wt, "test", "m6-t1")
check("test khi DB đã có: không tạo / seed lại", "CREATE DATABASE" not in dk and "db:seed" not in dk and "artisan test" in dk)
code, out, dk = run(main, "test", "m2-t1", "--filter", "Idp")
check("test task chưa có DB: tự tạo DB + migrate + seed trước", "CREATE DATABASE `cay_m2_t1`" in dk and "db:seed" in dk)
check("test ở thư mục chính: exec -w /var/www/main, DB riêng cay_m2_t1", "-w /var/www/main -e DB_DATABASE=cay_m2_t1 app sh -c php artisan test --filter Idp" in dk)
check("up: .env symlink về .env thư mục chính (không copy)", os.path.islink(os.path.join(wt, ".env")) and os.readlink(os.path.join(wt, ".env")) == "../../.env")
open(os.path.join(wt, "vendor", "x.php"), "w").write("<?php\n")
check("wt1 thêm gói vào vendor của nó: vendor thư mục chính không đổi", os.listdir(os.path.join(main, "vendor")) == ["autoload.php"])
wt2 = os.path.join(main, ".worktrees", "m7-t2")
sh(main, "git", "worktree", "add", "-q", wt2, "-b", "agent/m7-t2")
open(os.path.join(wt2, "composer.lock"), "w").write('{"wt2": 1}\n')
code, out, dk = run(wt2, "up", "m7-t2")
check("worktree có lock khác main: clone xong cài trong worktree", "-w /var/www/.worktrees/m7-t2" in dk and "composer install --no-interaction" in dk
      and "x.php" not in os.listdir(os.path.join(wt2, "vendor")))
code, out, dk = run(main, "main-deps", "main")
check("main-deps: lock chưa đổi → không cài lại", "composer install" not in dk)
open(os.path.join(main, "composer.lock"), "w").write('{"x": 1}\n')
code, out, dk = run(main, "main-deps", "main")
check("main-deps sau merge (lock đổi): vendor của wt2 không bị đụng", os.listdir(os.path.join(wt2, "vendor")) == ["autoload.php"])
check("main-deps: cài lại vendor của thư mục chính trong container (-w /var/www/main)", "-w /var/www/main app sh -c composer install --no-interaction" in dk)
code, out, dk = run(main, "main-deps", "main")
check("main-deps lần 2: đã cài theo lock mới → không cài lại", "composer install" not in dk)
open(os.path.join(wt, ".claude", "agent-team.config"), "a").write('SCHEMA_ENV="DB_DATABASE={db} REDIS_PREFIX={task}_"\nSCHEMA_DOWN_CMD="redis-cli --scan --pattern {task}_*"\n')
code, out, dk = run(wt, "test", "m6-t1")
check("SCHEMA_ENV {task}: REDIS_PREFIX=m6_t1_", "-e REDIS_PREFIX=m6_t1_" in dk)
code, out, dk = run(wt, "down", "m6-t1")
check("down: chạy SCHEMA_DOWN_CMD với {task} (dọn Redis / index của task)", "--pattern m6_t1_*" in dk)
check("down: xoá đúng DB có tiền tố, không đụng DB chính", code == 0 and "DROP DATABASE IF EXISTS `cay_m6_t1`" in dk and "`cay`" not in dk)
check("không tạo container clone riêng (docker run)", "docker run" not in dk and " run " not in f" {dk} ")
open(os.path.join(bin_dir, "curl"), "w").write("#!/bin/sh\nexit 0\n")
os.chmod(os.path.join(bin_dir, "curl"), 0o755)
out_e2e = os.path.join(d, "e2e.out")
open(os.path.join(wt, ".claude", "agent-team.config"), "a").write(
    f'E2E_PORT=3999\nAPP_START_CMD="php -S 0.0.0.0:{{port}}"\nE2E_CMD=\'echo "$BASE_URL|$APP_EXEC" > {out_e2e}\'\n')
os.makedirs(os.path.join(wt, ".agent-team"), exist_ok=True)
open(os.path.join(wt, ".agent-team", "e2e_port"), "w").write("8803")
code, out, dk = run(wt, "e2e", "m6-t1")
got = open(out_e2e).read() if os.path.exists(out_e2e) else ""
check("e2e: cổng riêng của worktree (8803) thắng E2E_PORT cố định", code == 0 and got.startswith("http://localhost:8803|") and "0.0.0.0:8803" in dk)
check("e2e: APP_EXEC = exec vào container app chung, đúng thư mục + DB của task",
      "docker compose exec -T -w /var/www/.worktrees/m6-t1 -e DB_DATABASE=cay_m6_t1" in got and got.rstrip().endswith(" app"))

print(f"\n{total - fail}/{total} passed")
raise SystemExit(1 if fail else 0)
