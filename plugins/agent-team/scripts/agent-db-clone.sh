#!/usr/bin/env bash
# Tên cũ, giữ để lệnh / quyền cũ vẫn chạy: dùng agent-db.sh
exec "$(dirname "$0")/agent-db.sh" "$@"
