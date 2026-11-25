#!/usr/bin/env bash
# DB clone cho agent team: copy DB local sang container riêng, migrate/test trên đó.
# DB hiện tại chỉ bị đọc (dump), không bị sửa.
set -euo pipefail

usage() {
  cat <<EOF
Usage: agent-db-clone.sh <command> <task-id> [args]
  up       <task-id>          tạo container clone + copy data
  migrate  <task-id>          chạy MIGRATE_CMD trên clone
  rollback <task-id>          chạy ROLLBACK_CMD trên clone
  verify   <task-id>          migrate -> rollback -> migrate
  test     <task-id> [args]   chạy TEST_CMD trên clone
  e2e      <task-id> [args]   chạy app (APP_START_CMD) trên clone rồi E2E_CMD trên máy, theo VIEWPORTS;
                              ảnh bằng chứng ở docs/testing/evidence/<task-id>/
  generate <task-id> <args>   sinh file migration bằng MIGRATION_GEN_CMD, chạy TRONG container app
  down     <task-id>          xoá clone
  status                      liệt kê clone đang chạy
EOF
  exit 1
}
die() { echo "ERROR: $*" >&2; exit 1; }

CMD="${1:-}"; TASK="${2:-}"
[ -n "$CMD" ] || usage

ROOT="$PWD"
while [ "$ROOT" != "/" ] && [ ! -f "$ROOT/.claude/agent-team.config" ]; do ROOT="$(dirname "$ROOT")"; done
[ -f "$ROOT/.claude/agent-team.config" ] || ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CONFIG="$ROOT/.claude/agent-team.config"
[ -f "$CONFIG" ] || die "thiếu $CONFIG, chạy /agent-team:init"
# shellcheck disable=SC1090
. "$CONFIG"
# riêng mỗi dev (gitignore): ghi đè config chung, vd E2E_PORT_BASE, HANG_MINUTES
# shellcheck disable=SC1091
if [ -f "$ROOT/.claude/agent-team.local.config" ]; then  # chỉ dòng có giá trị (để trống = không ghi đè)
  . <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=[^[:space:]#]' "$ROOT/.claude/agent-team.local.config")
fi

CLONE_MODE="${CLONE_MODE:-container}"
MAIN="$(dirname "$(cd "$ROOT" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || echo "$ROOT/.git")")"
[ "$CLONE_MODE" != schema ] || COMPOSE_DIR="${COMPOSE_DIR:-$MAIN}"
COMPOSE_DIR="${COMPOSE_DIR:-$ROOT}"
case "$COMPOSE_DIR" in /*) ;; *) COMPOSE_DIR="$ROOT/$COMPOSE_DIR" ;; esac
export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}" COMPOSE_PROFILES="${COMPOSE_PROFILES:-}"
STATE_DIR="$ROOT/.agent-team/clones"
[ -n "${CLONE_ENV:-}" ] || CLONE_ENV='DATABASE_URL={url}'

dc() { (cd "$COMPOSE_DIR" && docker compose "$@"); }

if [ "$CMD" = "status" ] && [ "$CLONE_MODE" = schema ]; then
  dc ps
  exit 0
fi
if [ "$CMD" = "status" ]; then
  docker ps -a --filter label=agent-team.clone=1 --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
  exit 0
fi
[ -n "$TASK" ] || usage

SAFE="$(printf '%s' "$TASK" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9_.-' '-')"
NAME="agent-clone-$SAFE"
STATE="$STATE_DIR/$NAME.state"

clone_up() {
  if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
    echo "Clone $NAME đã tồn tại"; return 0
  fi
  local cid image net pass st
  cid="$(dc ps -q "$DB_SERVICE")"
  [ -n "$cid" ] || die "service '$DB_SERVICE' chưa chạy"
  image="$(docker inspect -f '{{.Config.Image}}' "$cid")"
  net="$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$cid" | awk '{print $1}')"
  pass="$(openssl rand -hex 16)"   # password riêng của clone, không dùng password DB thật
  mkdir -p "$STATE_DIR"

  echo "Tạo clone $NAME từ image $image (network $net)..."
  case "$DB_ENGINE" in
    postgres)
      docker run -d --name "$NAME" --network "$net" --label agent-team.clone=1 \
        -e POSTGRES_USER=agent -e POSTGRES_PASSWORD="$pass" -e POSTGRES_DB="$DB_NAME" "$image" >/dev/null
      for _ in $(seq 1 90); do
        docker exec "$NAME" pg_isready -h 127.0.0.1 -U agent -d "$DB_NAME" >/dev/null 2>&1 && break; sleep 1
      done
      echo "Copy data $DB_NAME -> clone..."
      set +e
      docker exec "$cid" sh -c 'PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump -U "${POSTGRES_USER:-postgres}" -Fc --no-owner --no-acl "$1"' _ "$DB_NAME" \
        | docker exec -i "$NAME" sh -c 'pg_restore -U agent -d "$1" --no-owner --no-acl' _ "$DB_NAME"
      st=("${PIPESTATUS[@]}"); set -e
      [ "${st[0]}" -eq 0 ] || { docker rm -f "$NAME" >/dev/null; die "pg_dump lỗi"; }
      [ "${st[1]}" -eq 0 ] || echo "WARN: pg_restore có cảnh báo (thường do extension/owner), kiểm tra lại"
      printf 'CLONE_HOST=%s\nCLONE_PORT=5432\nCLONE_USER=agent\nCLONE_PASSWORD=%s\nCLONE_URL=postgres://agent:%s@%s:5432/%s\n' \
        "$NAME" "$pass" "$pass" "$NAME" "$DB_NAME" > "$STATE"
      ;;
    mysql)
      docker run -d --name "$NAME" --network "$net" --label agent-team.clone=1 \
        -e MYSQL_ROOT_PASSWORD="$pass" -e MARIADB_ROOT_PASSWORD="$pass" "$image" >/dev/null
      for _ in $(seq 1 90); do
        docker exec "$NAME" sh -c 'B=$(command -v mysqladmin || command -v mariadb-admin); MYSQL_PWD="$MYSQL_ROOT_PASSWORD" $B ping -h 127.0.0.1 -uroot --silent' >/dev/null 2>&1 && break; sleep 1
      done
      echo "Copy data $DB_NAME -> clone..."
      set +e
      docker exec "$cid" sh -c 'B=$(command -v mysqldump || command -v mariadb-dump); MYSQL_PWD="${MYSQL_ROOT_PASSWORD:-$MARIADB_ROOT_PASSWORD}" $B -uroot --single-transaction --routines --triggers --databases "$1"' _ "$DB_NAME" \
        | docker exec -i "$NAME" sh -c 'B=$(command -v mysql || command -v mariadb); MYSQL_PWD="$MYSQL_ROOT_PASSWORD" $B -uroot'
      st=("${PIPESTATUS[@]}"); set -e
      [ "${st[0]}" -eq 0 ] && [ "${st[1]}" -eq 0 ] || { docker rm -f "$NAME" >/dev/null; die "copy data lỗi"; }
      printf 'CLONE_HOST=%s\nCLONE_PORT=3306\nCLONE_USER=root\nCLONE_PASSWORD=%s\nCLONE_URL=mysql2://root:%s@%s:3306/%s\n' \
        "$NAME" "$pass" "$pass" "$NAME" "$DB_NAME" > "$STATE"
      ;;
    *) die "DB_ENGINE '$DB_ENGINE' chưa hỗ trợ (postgres|mysql)" ;;
  esac
  chmod 600 "$STATE"
  echo "Clone sẵn sàng: $NAME"
}

migration_files() {
  local d
  for d in ${MIGRATION_PATHS:-}; do
    [ -d "$ROOT/$d" ] && find "$ROOT/$d" -maxdepth 1 -type f -print
  done | sort
}

check_dup_versions() {
  # migration trùng số version (timestamp) → lỗi, không cho chạy tiếp
  local d dup
  for d in ${MIGRATION_PATHS:-}; do
    [ -d "$ROOT/$d" ] || continue
    dup="$(ls "$ROOT/$d" | sed -n 's/^\([0-9]\{6,\}\)_.*/\1/p' | sort | uniq -d)"
    [ -z "$dup" ] || die "migration trùng version trong $d: $(echo "$dup" | tr '\n' ' ')"
  done
}

generate_migration() {
  [ -n "${MIGRATION_GEN_CMD:-}" ] || die "thiếu MIGRATION_GEN_CMD trong config"
  [ -n "${MIGRATION_PATHS:-}" ] || die "thiếu MIGRATION_PATHS trong config"
  [ $# -gt 0 ] || die "thiếu tên migration"
  local before after user=() cmd
  before="$(migration_files)"
  case "${MIGRATION_GEN_USER:-}" in
    "") ;;
    host) user=(-u "$(id -u):$(id -g)") ;;
    *) user=(-u "$MIGRATION_GEN_USER") ;;
  esac
  cmd="$MIGRATION_GEN_CMD $(printf '%q ' "$@")"
  echo ">> [$APP_SERVICE] $cmd"
  if [ "$CLONE_MODE" = schema ]; then
    dc exec -T ${user[@]+"${user[@]}"} -w "$CPATH" "$APP_SERVICE" sh -c "$cmd"
  elif [ -n "$(dc ps --status running -q "$APP_SERVICE" 2>/dev/null)" ]; then
    dc exec -T ${user[@]+"${user[@]}"} "$APP_SERVICE" sh -c "$cmd"
  else
    dc run --rm --no-deps ${user[@]+"${user[@]}"} "$APP_SERVICE" sh -c "$cmd"
  fi
  after="$(migration_files)"
  [ "$before" != "$after" ] || die "generator không tạo file migration nào (kiểm MIGRATION_GEN_CMD, volume mount của $APP_SERVICE)"
  check_dup_versions
  echo "File mới:"; comm -13 <(echo "$before") <(echo "$after")
}

clone_envs() {
  # điền ENVS=(-e K=V ...) trỏ app vào DB clone (tạo clone nếu chưa có)
  [ -f "$STATE" ] || clone_up
  # shellcheck disable=SC1090
  . "$STATE"
  local pair v
  ENVS=()
  for pair in $CLONE_ENV; do
    v="${pair//\{host\}/$CLONE_HOST}"; v="${v//\{port\}/$CLONE_PORT}"
    v="${v//\{user\}/$CLONE_USER}"; v="${v//\{password\}/$CLONE_PASSWORD}"
    v="${v//\{db\}/$DB_NAME}"; v="${v//\{url\}/$CLONE_URL}"
    ENVS+=(-e "$v")
  done
}

run_on_clone() {
  clone_envs
  echo ">> [$NAME] $1"
  dc run --rm --no-deps "${ENVS[@]}" "$APP_SERVICE" sh -c "$1"
}

wait_url() {
  local _
  for _ in $(seq 1 "${E2E_WAIT:-120}"); do
    curl -s -o /dev/null "$1" && return 0; sleep 1
  done
  die "app không lên ở $1 sau ${E2E_WAIT:-120}s (xem log: docker logs $APP_RUN)"
}

e2e_run() {
  # App chạy trong container nối DB clone → (FE trên máy nếu có) → E2E_CMD trên máy, lặp VIEWPORTS
  [ -n "${E2E_CMD:-}" ] || die "thiếu E2E_CMD trong config (vd \"npx playwright test\")"
  [ -n "${APP_START_CMD:-}" ] || die "thiếu APP_START_CMD trong config"
  local port="${E2E_PORT:-$(cat "$ROOT/.agent-team/e2e_port" 2>/dev/null || echo 3999)}" base evid  # worktree: cổng riêng do pool.py cấp
  APP_RUN="agent-e2e-$SAFE" FE_PID=""  # toàn cục: trap EXIT chạy sau khi hàm kết thúc
  clone_envs
  docker rm -f "$APP_RUN" >/dev/null 2>&1 || true
  trap 'docker rm -f "$APP_RUN" >/dev/null 2>&1 || true; [ -z "$FE_PID" ] || { pkill -P "$FE_PID" 2>/dev/null; kill "$FE_PID" 2>/dev/null; } || true' EXIT
  echo ">> [$APP_RUN] $APP_START_CMD (localhost:$port → ${APP_PORT:-3000})"
  dc run -d --rm --no-deps --name "$APP_RUN" -p "$port:${APP_PORT:-3000}" "${ENVS[@]}" "$APP_SERVICE" sh -c "$APP_START_CMD" >/dev/null
  base="http://localhost:$port"
  wait_url "$base"
  if [ -n "${E2E_FE_START_CMD:-}" ]; then
    [ -n "${E2E_FE_URL:-}" ] || die "có E2E_FE_START_CMD thì cần E2E_FE_URL"
    (cd "$ROOT" && API_URL="$base" exec sh -c "$E2E_FE_START_CMD") >/dev/null 2>&1 &
    FE_PID=$!
    base="$E2E_FE_URL"
    wait_url "$base"
  fi
  evid="$ROOT/docs/testing/evidence/$TASK"
  mkdir -p "$evid"
  echo ">> E2E $base | VIEWPORTS=${VIEWPORTS:-1280} | ảnh: docs/testing/evidence/$TASK/"
  (cd "$ROOT" && BASE_URL="$base" VIEWPORTS="${VIEWPORTS:-1280}" EVIDENCE_DIR="$evid" TASK_ID="$TASK" sh -c "$E2E_CMD $*")
}

# ---- CLONE_MODE=schema: 1 container DB + 1 container app cho mọi worktree ----
# DB riêng mỗi task trong cùng DB server (<DB_NAME>_<task>); lệnh chạy bằng exec -w <thư mục worktree trong container>
SDB="${DB_NAME}_$(printf '%s' "$SAFE" | tr '.-' '__')"
CMAIN="${CONTAINER_MAIN:-/var/www/main}"
CWT="${CONTAINER_WT:-/var/www/.worktrees}"
if [ "$ROOT" = "$MAIN" ]; then CPATH="$CMAIN"; else CPATH="$CWT/$(basename "$ROOT")"; fi

db_sql() {
  case "$DB_ENGINE" in
    mysql) dc exec -T "$DB_SERVICE" sh -c 'B=$(command -v mysql || command -v mariadb); MYSQL_PWD="${MYSQL_ROOT_PASSWORD:-$MARIADB_ROOT_PASSWORD}" $B -uroot -e "$0"' "$1" ;;
    postgres) dc exec -T "$DB_SERVICE" sh -c 'psql -U "${POSTGRES_USER:-postgres}" -d postgres -c "$0"' "$1" ;;
    *) die "DB_ENGINE '$DB_ENGINE' chưa hỗ trợ (postgres|mysql)" ;;
  esac
}

schema_envs() {
  local pair
  ENVS=()
  for pair in ${SCHEMA_ENV:-DB_DATABASE=\{db\}}; do ENVS+=(-e "${pair//\{db\}/$SDB}"); done
}

link_deps() {
  # vendor / node_modules: symlink về bản của thư mục chính; lock file khác → cài riêng trong worktree
  [ "$ROOT" != "$MAIN" ] || return 0
  local d lock
  for d in ${SHARED_DEPS:-vendor:composer.lock node_modules:package-lock.json}; do
    lock="${d#*:}"; d="${d%%:*}"
    { [ -e "$ROOT/$d" ] || [ ! -d "$MAIN/$d" ]; } && continue
    if [ -f "$ROOT/$lock" ] && ! cmp -s "$ROOT/$lock" "$MAIN/$lock"; then
      echo "WARN: $lock khác thư mục chính → cài $d riêng trong worktree"
    else
      ln -s "../../$d" "$ROOT/$d"
    fi
  done
}

run_schema() {
  schema_envs
  echo ">> [$APP_SERVICE:$CPATH] DB=$SDB · $1"
  dc exec -T -w "$CPATH" "${ENVS[@]}" "$APP_SERVICE" sh -c "$1"
}

kill_port() {
  dc exec -T "$APP_SERVICE" sh -c 'for d in /proc/[0-9]*; do tr "\0" " " < $d/cmdline 2>/dev/null | grep -qE ":$0( |$)" && kill ${d#/proc/} 2>/dev/null; done; true' "$1" || true
}

schema_up() {
  local q='`'
  case "$DB_ENGINE" in postgres) q='"' ;; esac
  db_sql "CREATE DATABASE ${q}${SDB}${q}" 2>/dev/null || echo "DB $SDB đã có"
  link_deps
  run_schema "$MIGRATE_CMD"
  [ -z "${SEED_CMD:-}" ] || run_schema "$SEED_CMD"
  echo "DB $SDB sẵn sàng (migrate + seed), code: $CPATH"
}

schema_down() {
  local q='`'
  case "$DB_ENGINE" in postgres) q='"' ;; esac
  case "$SDB" in "${DB_NAME}_"?*) ;; *) die "tên DB '$SDB' sai tiền tố, không xoá" ;; esac
  [ ! -f "$ROOT/.agent-team/e2e_port" ] || kill_port "$(cat "$ROOT/.agent-team/e2e_port")"
  db_sql "DROP DATABASE IF EXISTS ${q}${SDB}${q}"
  echo "Đã xoá DB $SDB"
}

schema_e2e() {
  [ -n "${E2E_CMD:-}" ] || die "thiếu E2E_CMD trong config"
  [ -n "${APP_START_CMD:-}" ] || die "thiếu APP_START_CMD trong config"
  local port="${E2E_PORT:-$(cat "$ROOT/.agent-team/e2e_port" 2>/dev/null || echo 3999)}" base evid start
  schema_envs
  start="${APP_START_CMD//\{port\}/$port}"
  kill_port "$port"
  trap 'kill_port "$port"' EXIT
  echo ">> [$APP_SERVICE:$CPATH] $start (localhost:$port)"
  dc exec -d -w "$CPATH" "${ENVS[@]}" -e APP_URL="http://localhost:$port" "$APP_SERVICE" sh -c "$start"
  base="http://localhost:$port"
  APP_RUN="$APP_SERVICE" wait_url "$base"
  evid="$ROOT/docs/testing/evidence/$TASK"
  mkdir -p "$evid"
  echo ">> E2E $base | VIEWPORTS=${VIEWPORTS:-1280} | ảnh: docs/testing/evidence/$TASK/"
  (cd "$ROOT" && BASE_URL="$base" VIEWPORTS="${VIEWPORTS:-1280}" EVIDENCE_DIR="$evid" TASK_ID="$TASK" sh -c "$E2E_CMD $*")
}

if [ "$CLONE_MODE" = schema ]; then
  case "$CMD" in
    up)       schema_up ;;
    generate) shift 2; generate_migration "$@" ;;
    migrate)  check_dup_versions; run_schema "$MIGRATE_CMD" ;;
    rollback) run_schema "$ROLLBACK_CMD" ;;
    verify)
      check_dup_versions
      run_schema "$MIGRATE_CMD"; run_schema "$ROLLBACK_CMD"; run_schema "$MIGRATE_CMD"
      echo "VERIFY OK: migrate -> rollback -> migrate"
      ;;
    test)     shift 2; run_schema "$TEST_CMD $*" ;;
    e2e)      shift 2; schema_e2e "$@" ;;
    down)     schema_down ;;
    *) usage ;;
  esac
  exit 0
fi

case "$CMD" in
  up)       clone_up ;;
  generate) shift 2; generate_migration "$@" ;;
  migrate)  check_dup_versions; run_on_clone "$MIGRATE_CMD" ;;
  rollback) run_on_clone "$ROLLBACK_CMD" ;;
  verify)
    check_dup_versions
    run_on_clone "$MIGRATE_CMD"
    run_on_clone "$ROLLBACK_CMD"
    run_on_clone "$MIGRATE_CMD"
    echo "VERIFY OK: migrate -> rollback -> migrate"
    ;;
  test)
    shift 2
    run_on_clone "$TEST_CMD $*"
    ;;
  e2e)
    shift 2
    e2e_run "$@"
    ;;
  down)
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    rm -f "$STATE"
    echo "Đã xoá $NAME"
    ;;
  *) usage ;;
esac
