#!/usr/bin/env python3
"""Test show_post.py: python3 tests/test_show_post.py"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "plugins", "agent-team", "hooks", "show_post.py")
d = tempfile.mkdtemp()
board = os.path.join(d, "docs/agent-tasks/T1/board")
os.makedirs(board)
open(os.path.join(board, "S2-R2-security-1.md"), "w").write(
    "<!-- mẫu -->\n**Role:** security\n" + "".join(f"dòng {i}\n" for i in range(30)))
open(os.path.join(board, "SUMMARY.md"), "w").write("x\n")
fail = total = 0


def run(tool, rel):
    data = {"tool_name": tool, "tool_input": {"file_path": rel}, "cwd": d}
    r = subprocess.run([sys.executable, HOOK], input=json.dumps(data), capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout)["systemMessage"] if r.stdout.strip() else "")


def check(desc, ok):
    global fail, total
    total += 1
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {desc}")


code, msg = run("Write", "docs/agent-tasks/T1/board/S2-R2-security-1.md")
check("hiện bài post với tiêu đề role + vòng", code == 0 and msg.startswith("┌─ [security · S2-R2]"))
check("bỏ dòng comment mẫu", "mẫu" not in msg)
check("cắt còn 15 dòng + báo số dòng còn lại", "… còn 16 dòng" in msg and msg.count("│ ") == 16)
check("kèm đường dẫn file", msg.endswith("S2-R2-security-1.md"))
check("SUMMARY.md không hiện", run("Write", "docs/agent-tasks/T1/board/SUMMARY.md")[1] == "")
check("Edit không hiện", run("Edit", "docs/agent-tasks/T1/board/S2-R2-security-1.md")[1] == "")
check("file ngoài board không hiện", run("Write", "app/S2-R2-security-1.md")[1] == "")
check("file không tồn tại không lỗi", run("Write", "docs/agent-tasks/T1/board/S2-R9-tester-1.md") == (0, ""))
print(f"\n{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
