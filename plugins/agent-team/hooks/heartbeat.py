#!/usr/bin/env python3
"""agent-team heartbeat: ghi trạng thái subagent vào board.db (last_seen, tool đang chạy, DONE khi kết thúc).
Dùng cho `board.py wait / status / stuck` và status line. Không bao giờ chặn: lỗi gì cũng exit 0.
Gọi: heartbeat.py pre | post | stop | lead-stop  (PreToolUse, PostToolUse, SubagentStop, Stop).
`lead-stop`: còn agent đang chạy thì nhắc Lead chờ bằng wait (in JSON decision=block, vẫn exit 0)."""
import importlib.util
import json
import os
import sys


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else "pre"
    data = json.load(sys.stdin)
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("board", os.path.join(here, "..", "scripts", "board.py"))
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)
    board.lead_stop(data) if event == "lead-stop" else board.heartbeat(event, data)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:  # die() của board gọi sys.exit: vẫn không chặn tool
        if os.environ.get("AGENT_TEAM_DEBUG") == "1":
            sys.stderr.write(f"[agent-team heartbeat] {e!r}\n")
    sys.exit(0)
