---
description: Cài agent team cho project - tạo config, copy script + template, khung Knowledge Base trong docs/ (dự án có sẵn code thì Scout dựng luôn nháp KB + quy chuẩn code), thêm mục Agent Team vào CLAUDE.md.
argument-hint: [--skip-kb]
model: sonnet
---

Thiết lập agent team cho project hiện tại. Liệt kê ngắn từng bước trước khi làm. Tham số: $ARGUMENTS (`--skip-kb` = không dựng nháp KB từ code).

1. **Tìm thư mục plugin**:
   `find ~/.claude/plugins -type d -path "*agent-team" -exec test -f {}/scripts/agent-db.sh \; -print | head -1`
2. **Nhận diện project** (chỉ đọc):
   - Stack BE/FE/test: Gemfile, package.json, thư mục spec/test
   - Lệnh lint/format đang có (rubocop, eslint, prettier, ruff...) → `LINT_CMD`, `FORMAT_CMD`
   - Thư mục migration → `MIGRATION_PATHS`; lệnh generator migration của framework (chạy trong container app) → `MIGRATION_GEN_CMD`. Không chắc → `TODO`.
   - Thư mục chứa hàm public dùng lại nhiều (service, repository, model, use-case; FE: api client, hooks, store) → `FUNCTION_INDEX_PATHS` (chỉ mục hàm `docs/functions/`, so với graph). Repo trống → để trống, Architect điền ở task dựng khung.
   - **E2E / responsive:** có `@playwright/test` trong package.json → `E2E_CMD="npx playwright test"`; lệnh chạy server app trong container → `APP_START_CMD`, cổng → `APP_PORT`; FE tách repo (SPA) → `E2E_FE_START_CMD`, `E2E_FE_URL`. Có CSS media query / framework responsive → `VIEWPORTS="375 768 1280"`, chỉ máy tính → `"1280"`. Không chắc → `TODO`. Chưa cài Playwright → báo user lệnh cài (không tự cài): `npm i -D @playwright/test && npx playwright install chromium`.
   - docker-compose: file nằm trong repo hay repo khác, tên service DB và app, loại DB (postgres/mysql)
   - Branch gốc (develop/main/master) của **từng repo** (`git symbolic-ref --short refs/remotes/origin/HEAD`). Giống nhau → `BASE_BRANCH`. Repo nào khác → `BASE_BRANCHES="<repo>=<nhánh>"`.
   - **Có mấy repo git?** Tìm repo ở thư mục hiện tại và thư mục con cấp 1 (`.git`). Thư mục hiện tại là repo thì hỏi thêm user có repo khác đi kèm không (vd `../FrontEnd`).
   - **Có code sẵn không?** `git ls-files` có file mã nguồn (rb, py, js/ts, go, java, php, vue...) → dự án có sẵn code.
2a. **Dự án mới (App Mode):**
   - Chưa có git → `git init -b main`, `BASE_BRANCH=main`. Chưa có code nên `BE_PATHS`, `FE_PATHS`, `TEST_PATHS`, lệnh test/lint để `TODO`: Architect điền sau khi chốt stack (`/agent-team:app` mục 9). FE và BE chung 1 repo → `FE_PATHS=""`, đường dẫn FE nằm trong `BE_PATHS`.
   - Không có remote (`git remote` rỗng) → `PUSH=0` (không fetch/push, branch nằm ở máy). Có remote → `PUSH=1`.
   - Copy `templates/product/project-setup.md` → `docs/product/project-setup.md` (không ghi đè). Báo user: dev điền phiếu này trước khi chạy `/agent-team:app`.
2b. **Nhiều repo → chọn repo chính** (chỉ hỏi khi ≥ 2 repo, 1 câu hỏi duy nhất bằng AskUserQuestion):
   - Câu hỏi: "Chọn repo chính, nơi chứa `.claude/`, `docs/`, `CLAUDE.md`". Mỗi lựa chọn là tên 1 repo tìm thấy. Gợi ý đầu tiên: repo BE/API.
   - Mọi file init tạo **trong repo chính**. **Không tạo gì ở thư mục cha.**
   - Config: `REPOS=". ../FrontEnd"` (`.` là repo chính). `BE_PATHS`, `FE_PATHS`, `TEST_PATHS` tính từ repo chính, vd `FE_PATHS="../FrontEnd"`.
   - Dặn user: mở Claude Code ở **repo chính**, rồi thêm repo còn lại bằng `/add-dir ../FrontEnd`.
3. **Tạo `.claude/agent-team.config`** từ `templates/agent-team.config.example`, điền giá trị đã nhận diện (kể cả `LINT_CMD`, `FORMAT_CMD`). Giữ mặc định `COST_TIER=standard` (economy | standard | max) và `LESSONS_PATH=docs/LESSONS.md`. Giá trị không chắc → `TODO` và báo user. Tuyệt đối không ghi password/KEY.
3b. **⛔ User duyệt cấu hình chạy (bắt buộc, trước mọi lần gọi agent; không tự quyết thay):** in bảng dưới với giá trị vừa ghi vào config + đề xuất theo trường hợp của dự án này, rồi hỏi bằng `AskUserQuestion` ("Sửa" / "Tôi sẽ tự ghi ok"). User sửa → ghi lại config, in lại bảng, hỏi lại. **Duyệt = user tự mở `.claude/agent-team.config` sửa dòng `CONFIG_APPROVED=ok`** (bạn không ghi dòng này, hook chặn; hook cũng chặn mọi lần gọi agent khi dòng này còn trống). Bước 4-7 chỉ chép file vẫn làm được; tới 7b mà chưa `ok` → in "Bước tiếp: sửa `CONFIG_APPROVED=ok` rồi chạy lại `/agent-team:init`" và DỪNG.
   | Key | Giá trị | Ý nghĩa | Đề xuất theo trường hợp |
   |---|---|---|---|
   | `COST_TIER` | economy / standard / max | model mỗi role (bảng ở `task.md` mục 2) | thử nghiệm: economy · bình thường: standard · nghiệp vụ khó / tiền / bảo mật: max |
   | Scout dựng KB | số Scout dự kiến + model từng mảng (`kb.md` mục 2) | đọc code có sẵn | có code cũ / chuẩn bị migrate: mảng đọc logic dùng opus |
   | `MAX_PARALLEL` | số task chạy cùng lúc | nhanh hơn nhưng tốn quota + máy | quota thấp / máy yếu: 3-5 · bình thường: 8 · tối đa đang dùng: 15 |
   | `MAX_DEBATE` | số debate module cùng lúc | | 2-4 |
   | `API_RESPONSE` | flat / cooked | flat: BE chỉ đọc + lọc theo quyền, FE tự tính; API nào có vai trò không được thấy dữ liệu thô thì BE vẫn xử lý | mặc định: flat · FE mỏng / nhiều client dùng chung API cần BE tính sẵn: cooked |
   | `TEST_MODE` | full / mvp | mvp: E2E để cuối, ra bản dùng thử nhanh | app mới cần demo sớm: mvp |
   | `CLONE_MODE` | container / schema | schema: 1 container DB + 1 container app cho mọi task | chạy song song nhiều: schema |
   | `PUSH` | 0 / 1 | có tự push branch task không | |
4. **Copy vào project**:
   - `scripts/agent-db.sh` → `.claude/agent-team/agent-db.sh` (chmod +x)
   - `templates/TASK.md`, `POST.md`, `SUMMARY.md`, `CONTEXT.md`, `MOCKS.md` → `.claude/agent-team/templates/`
   - `scripts/kb-check.py` → `.claude/agent-team/kb-check.py` (chmod +x)
   - `scripts/board.py`, `scripts/pool.py` → `.claude/agent-team/` (chmod +x). `pool.py`: điều phối nhiều task song song (worktree). Board chat SQLite, dữ liệu ở `.agent-team/board.db` (đã gitignore).
   - `scripts/gap-check.py` → `.claude/agent-team/gap-check.py` (chmod +x). Kiểm tài liệu sản phẩm `docs/product/` của App Mode.
   - `scripts/owner-form.py` → `.claude/agent-team/owner-form.py` (chmod +x, cần `gap-check.py` cùng thư mục). Sinh form `.xlsx` gửi owner và nhập câu trả lời.
   - `CLONE_MODE=schema` (1 container DB + 1 container app): thêm vào compose của app `volumes: ["./:/var/www/main", "./.worktrees:/var/www/.worktrees", "/var/www/main/.worktrees", "./.env:/var/www/.env:ro"]` + `ports: ["8800-8899:8800-8899"]` (mở sẵn 100 cổng, không phải restart container; mount `.env` để symlink `../../.env` của worktree trỏ đúng cả trên máy lẫn trong container): thư mục chính `:8800`, worktree `:8801`, `:8802`... (`E2E_PORT_BASE` mặc định 8801 khi `CLONE_MODE=schema`). Thêm `.worktrees` vào ignore của tool quét thư mục: `tsconfig` `exclude`, ESLint `ignores`, Vite `server.watch.ignored`, PHPUnit / Pint chỉ quét `app/`, `tests/`.
   - **`CLONE_MODE=schema`: bạn (Lead) tự đánh giá dự án rồi điền, không chép bảng mẫu** (mặc định trong config mẫu là Laravel). Bảng dưới chỉ là gợi ý; giá trị thật lấy từ **bằng chứng trong repo**:
     1. Đọc: `Dockerfile` (`WORKDIR`, lệnh chạy), compose (service, volume, cổng), lock file có trong repo, `.gitignore` (thư mục sinh ra khi chạy: dependency, cache, build), file cấu hình DB (app đọc biến nào), cấu hình linter / test / watcher (tool nào quét cả thư mục).
     2. Điền 5 dòng của bảng cho đúng dự án này. Dự án lai (vd Laravel + Go worker) → gộp giá trị của từng phần. Trong bảng duyệt cấu hình (bước 3b) ghi **mỗi giá trị kèm nguồn** (`file:dòng`); không tìm ra bằng chứng → `TODO`, không đoán.
     3. **Chạy thử sau khi user duyệt** (trước khi gọi agent): `pool.py side init-check` → `agent-db.sh up init-check` → `agent-db.sh test init-check` (và `e2e` nếu có `E2E_CMD`) → kiểm DB riêng `<DB_NAME>_init-check` có bảng, thư mục dependency của worktree là bản riêng, app lên đúng cổng → `agent-db.sh down init-check` + xoá worktree. Bước nào lỗi: sửa đúng key gây lỗi trong config, chạy lại, ghi vào `release-notes.md` giá trị đã đổi + vì sao.
     4. Về sau, task lỗi do cấu hình này (worktree thiếu dependency, ghi nhầm DB, trùng cổng, tool quét lẫn `.worktrees`): bạn sửa config ngay, báo user 1 dòng (key, cũ → mới, lý do), ghi bài học. Không phải chờ user duyệt lại (`CONFIG_APPROVED` chỉ duyệt lần đầu).

     Gợi ý theo stack:

     | | Laravel | Rails | Go | Node (Nest / Express) |
     |---|---|---|---|---|
     | `SHARED_DEPS` (thư mục mỗi worktree phải có bản riêng, không dùng chung) | `vendor:composer.lock node_modules:package-lock.json` | `node_modules:yarn.lock` (gem cài trong project: thêm `vendor/bundle:Gemfile.lock`) | để trống (module cache nằm trong container; có thư mục `vendor/`: `vendor:go.sum`) | `node_modules:<lock file>` |
     | `CONTAINER_MAIN` / `CONTAINER_WT` | theo `WORKDIR`, vd `/var/www/main` · `/var/www/.worktrees` | vd `/rails/main` · `/rails/.worktrees` | vd `/app/main` · `/app/.worktrees` | vd `/app/main` · `/app/.worktrees` |
     | `SCHEMA_ENV` (tách DB + service dùng chung) | `DB_DATABASE={db} REDIS_PREFIX={task}_ CACHE_PREFIX={task}_ QUEUE_CONNECTION=sync MAIL_MAILER=log` | biến mà `config/database.yml` đọc, vd `DB_NAME={db}`; Redis / cache / Sidekiq: namespace `{task}` | biến DB mà app đọc, vd `DB_NAME={db}` | biến DB mà app đọc |
     | `APP_START_CMD` | `PHP_CLI_SERVER_WORKERS=8 php -S 0.0.0.0:{port} -t public` | `bin/rails s -b 0.0.0.0 -p {port}` | `PORT={port} go run ./cmd/<app>` | `PORT={port} npm run start` |
     | Tool quét thư mục chính phải bỏ qua `.worktrees` | PHPUnit / Pint chỉ quét `app/`, `tests/`; `tsconfig` `exclude`; ESLint `ignores`; Vite `server.watch.ignored` | RuboCop `AllCops.Exclude`; Tailwind `content`; Jest `modulePathIgnorePatterns` | `go build / test ./...` tự bỏ thư mục bắt đầu bằng dấu chấm; chỉ cần thêm vào `exclude_dir` của Air / watcher | `tsconfig` `exclude`; ESLint `ignores`; Jest `modulePathIgnorePatterns`; nodemon `ignore` |
     | Bẫy riêng | không chạy `config:cache` (cache giữ tên DB, bỏ qua `SCHEMA_ENV` → task ghi nhầm DB) | `database.yml` ghi cứng tên DB thì `SCHEMA_ENV` không có tác dụng: đổi sang đọc ENV | binary build ra thư mục của từng worktree, không ghi chung 1 đường dẫn | cổng ghi cứng trong code thì `{port}` không có tác dụng |

     Stack không có trong bảng: áp cùng 5 câu hỏi (thư mục dependency nào, đường dẫn trong container, biến nào tách DB, lệnh chạy app theo cổng, tool nào quét cả thư mục).
   - `scripts/progress.py` → `.claude/agent-team/progress.py` (chmod +x). Thêm vào `.claude/settings.json` của repo chính (merge, không ghi đè key khác; đã có `statusLine` thì hỏi user): `"statusLine": {"type": "command", "command": "python3 .claude/agent-team/progress.py"}`. Status line hiện các bảng có khung: module của app / task của module (`M | Module | Trạng thái`), giai đoạn S1-S6 (ngang), các bước (`# | Bước | Role | Trạng thái`: ✅ Xong / ▶ Đang làm Np / ⏳ Chờ / ⛔ Chặn). Mặc định status line 1 dòng (`PROGRESS_LINES=1`), bảng đầy đủ ghi vào `.agent-team/STATUS.md` (mở preview, tự cập nhật); `PROGRESS_LINES=table` → bảng trên status line. `progress.py --list` in đủ danh sách ✅ / ▶ / ○ để Lead dán vào chat. Về sau hook `SessionStart` (`hooks/sync.py`) tự chép lại script khi plugin cập nhật và tự thêm `statusLine` nếu thiếu.
5. **CLAUDE.md**: chưa có mục "## Agent Team" thì thêm nội dung `templates/claude-md-section.md` vào cuối. Không sửa phần khác.
5a. **Vẽ sơ đồ trong báo cáo**: kiểm `mmdc --version` (Mermaid CLI). Chưa có → báo user lệnh cài `npm i -g @mermaid-js/mermaid-cli` (không tự cài). Không có thì REPORT.html vẫn tạo được, sơ đồ hiện dạng văn bản.
5b. **Code graph = Graphify (tùy chọn)**: hỏi user có muốn dùng không. Không → `USE_CODE_GRAPH=0`, bỏ qua.
   - Có → kiểm `graphify --version`. Chưa có thì **không tự cài**, báo user lệnh cài trong `release-notes.md` của plugin (`uv tool install --python 3.11 graphifyy==<bản>`, tên gói 2 chữ y) và 2 biến `GRAPHIFY_BACKEND=none`, `GRAPHIFY_QUERY_LOG_DISABLE=1`.
     1. Build lần đầu (chỉ đọc code, không gọi LLM): chạy `graphify update .` (nhiều repo: `graphify update <repo>` từng repo trong `REPOS`, rồi `graphify merge-graphs <repo>/graphify-out/graph.json ... --out graphify-out/merged-graph.json` ở repo chính). Chưa cài `graphify` → bỏ qua, báo ở cuối.
     2. Lỗi → báo user, không đoán. **Không chạy** `graphify install`, `graphify hook install`, `graphify claude install` (đụng hook guard), `graphify extract` (gọi LLM).
     3. Báo user: graph dựng bằng tree-sitter từ file đã commit, tới mức hàm, có `file:dòng`.
6. **.gitignore**: `.agent-team/` thêm vào repo chính. `graphify-out/`, `.env*`, dump thêm vào **mọi repo trong `REPOS`**. Thêm nếu chưa có:
   ```
   .agent-team/
   graphify-out/
   .env*
   !.env.example
   *.dump
   *.sql.gz
   # agent-team: script do plugin chép mỗi phiên (hook sync.py) + config riêng mỗi dev → không commit
   .claude/agent-team/*.py
   .claude/agent-team/*.sh
   .claude/agent-team/__pycache__/
   .claude/agent-team.local.config
   .claude/agent-team.secret
   .claude/agent-team/e2e-template/
   e2e/.auth/
   ```
   Commit: `.claude/agent-team.config` (config chung của team), `.claude/agent-team/templates/`, `.claude/settings.json`.
   Tạo `.claude/agent-team.local.config` từ `templates/agent-team.local.config.example` (riêng máy này: `DEV_ID`, `MAX_PARALLEL`, `E2E_PORT_BASE`...).
7. **Khung Knowledge Base `docs/`** trong repo chính (tên thư mục luôn là `docs` viết thường, vì guard so khớp phân biệt hoa thường):
   - Copy `templates/kb/` → `docs/`, **không ghi đè file đã có**. Thêm `docs/agent-tasks/.gitkeep`.
   - Đã có `Docs/` viết hoa → hỏi user đổi tên thành `docs` (`git mv Docs docs`) trước khi tạo.
   - Project đã có `docs/domain/` từ bản cũ → giữ nguyên (BA vẫn ghi được), không di chuyển.
   - Project đã có tài liệu nghiệp vụ nơi khác → đọc làm nguồn, không tự di chuyển hay ghi đè.
7b. **Dự án có sẵn code và không có `--skip-kb` → dựng KB ngay, đọc sâu logic (không chỉ liệt kê thư mục):**
   1. Copy `scripts/kb-check.py` → `.claude/agent-team/kb-check.py` (chmod +x).
   2. **Đọc `<thư mục plugin>/commands/kb.md` rồi làm đúng quy trình trong đó** (mục 1-5): Bản đồ → nhiều Scout song song theo mảng (module, kiến trúc/API/DB, frontend, quy chuẩn/test) → Scout tổng hợp nghiệp vụ → `kb-check.py` và gọi lại Scout cho file còn `THIEU` (tối đa 2 vòng). Thư mục plugin lấy ở bước 1.
   3. Mọi mục gắn nhãn (`Observed`/`Unverified`/`Assumption`), có `file:dòng` và `verified-at: <commit>`. Business rule suy từ code không bao giờ là Confirmed.
   4. Lệnh lint/format Scout báo → điền `LINT_CMD`, `FORMAT_CMD` nếu bước 2 chưa nhận diện được.
   5. **Không có lối thoát "quá dài thì bỏ qua".** Chưa đọc hết thì ghi rõ trong `docs/README.md` mục "Tình trạng KB" (đã quét / chưa quét / vì sao) và báo user chạy `/agent-team:kb <module>` để làm tiếp.
   6. Dự án mới (chưa có code): bỏ qua bước này, chỉ giữ khung. Quy chuẩn code đặt ở A0-A2 của `/agent-team:app` (từ `project-setup.md` mục 6), trước khi viết kiến trúc. Làm app từ ý tưởng: `/agent-team:app <ý tưởng>` (tự copy `templates/product/` → `docs/product/`).
8. **Ghi `release-notes.md`** (tạo nếu chưa có), mục `Release notes - DD/MM/YYYY`: đã cài agent team, file nào được thêm, key mới (`LINT_CMD`, `FORMAT_CMD`, `COST_TIER`, `LESSONS_PATH`, `FUNCTION_INDEX_PATHS`).
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền, kết quả `kb-check.py` (đạt/tổng), phần KB chưa quét và còn `Unverified`. **Không commit**, để user xem trước. Cuối cùng in **"Bước tiếp"** theo đúng trường hợp của dự án này (3-4 dòng đánh số, dòng 1 làm được ngay; đầy đủ ở README plugin mục "Bắt đầu"):
   - Dự án mới: (1) dev điền `docs/product/project-setup.md` (2) gom logo / màu / app tham khảo vào `docs/product/design-ref/` (3) `/agent-team:app "<ý tưởng>"`.
   - Có code sẵn: (1) đọc lướt `docs/`, sửa chỗ KB hiểu sai (2) còn `THIEU` → `/agent-team:kb` (3) `/agent-team:audit` 1 lần (4) `/agent-team:task "<việc>"` hoặc `/agent-team:module "<tính năng lớn>"`.
   - Có `docs/legacy/` (viết lại hệ thống cũ): như dự án mới, `/agent-team:app` tự dùng `docs/legacy/`.
