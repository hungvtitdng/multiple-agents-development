#!/usr/bin/env python3
"""CLONE_MODE=schema (v0.40): 1 container DB + 1 container app, mỗi worktree 1 DB riêng + exec -w đúng thư mục.
docker giả ghi lại lệnh. python3 tests/test_schema_mode.py"""
import os
import subprocess
import tempfile

SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins", "agent-team", "scripts", "agent-db-clone.sh")
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
bin_dir = os.path.join(d, "bin")
os.makedirs(bin_dir)
log = os.path.join(d, "docker.log")
open(os.path.join(bin_dir, "docker"), "w").write(f'#!/bin/sh\necho "$@" >> {log}\n')
os.chmod(os.path.join(bin_dir, "docker"), 0o755)
cfg = ('CLONE_MODE=schema\nDB_ENGINE=mysql\nDB_SERVICE=mysql\nDB_NAME=cay\nAPP_SERVICE=app\n'
       'MIGRATE_CMD="php artisan migrate"\nSEED_CMD="php artisan db:seed"\nTEST_CMD="php artisan test"\n')
open(os.path.join(main, ".claude", "agent-team.config"), "w").write(cfg)
open(os.path.join(main, "composer.lock"), "w").write("{}\n")
open(os.path.join(main, ".gitignore"), "w").write("vendor/\n.worktrees/\n")
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
check("up: vendor symlink về thư mục chính (../../vendor)", os.path.islink(os.path.join(wt, "vendor")) and os.readlink(os.path.join(wt, "vendor")) == "../../vendor")
code, out, dk = run(main, "test", "m2-t1", "--filter", "Idp")
check("test ở thư mục chính: exec -w /var/www/main, DB riêng cay_m2_t1", "-w /var/www/main -e DB_DATABASE=cay_m2_t1 app sh -c php artisan test --filter Idp" in dk)
code, out, dk = run(wt, "down", "m6-t1")
check("down: xoá đúng DB có tiền tố, không đụng DB chính", code == 0 and "DROP DATABASE IF EXISTS `cay_m6_t1`" in dk and "`cay`" not in dk)
check("không tạo container clone riêng (docker run)", "docker run" not in dk and " run " not in f" {dk} ")

print(f"\n{total - fail}/{total} passed")
raise SystemExit(1 if fail else 0)
