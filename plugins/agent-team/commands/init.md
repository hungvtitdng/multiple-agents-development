---
description: Cài agent team cho project - tạo config, copy script + template, khung Knowledge Base trong docs/ (dự án có sẵn code thì Scout dựng luôn nháp KB + quy chuẩn code), thêm mục Agent Team vào CLAUDE.md.
argument-hint: [--skip-kb]
model: sonnet
---

Thiết lập agent team cho project hiện tại. Liệt kê ngắn từng bước trước khi làm. Tham số: $ARGUMENTS (`--skip-kb` = không dựng nháp KB từ code).

1. **Tìm thư mục plugin**:
   `find ~/.claude/plugins -type d -path "*agent-team" -exec test -f {}/scripts/agent-db-clone.sh \; -print | head -1`
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
4. **Copy vào project**:
   - `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh` (chmod +x)
   - `templates/TASK.md`, `POST.md`, `SUMMARY.md`, `CONTEXT.md`, `MOCKS.md` → `.claude/agent-team/templates/`
   - `scripts/kb-check.py` → `.claude/agent-team/kb-check.py` (chmod +x)
   - `scripts/board.py` → `.claude/agent-team/board.py` (chmod +x). Board chat SQLite, dữ liệu ở `.agent-team/board.db` (đã gitignore).
   - `scripts/gap-check.py` → `.claude/agent-team/gap-check.py` (chmod +x). Kiểm tài liệu sản phẩm `docs/product/` của App Mode.
   - `scripts/owner-form.py` → `.claude/agent-team/owner-form.py` (chmod +x, cần `gap-check.py` cùng thư mục). Sinh form `.xlsx` gửi owner và nhập câu trả lời.
   - `scripts/progress.py` → `.claude/agent-team/progress.py` (chmod +x). Thêm vào `.claude/settings.json` của repo chính (merge, không ghi đè key khác; đã có `statusLine` thì hỏi user): `"statusLine": {"type": "command", "command": "python3 .claude/agent-team/progress.py"}`. Status line hiện `[task] S3 CODE · bước 2/4: <tên bước> · còn: <bước chưa làm> · chờ: role · WHY mở`. `progress.py --list` in đủ danh sách ✅ / ▶ / ○ để Lead dán vào chat. Về sau hook `SessionStart` (`hooks/sync.py`) tự chép lại script khi plugin cập nhật và tự thêm `statusLine` nếu thiếu.
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
   ```
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
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền, kết quả `kb-check.py` (đạt/tổng), phần KB chưa quét và còn `Unverified`. **Không commit**, để user xem trước. Cuối cùng: đúng 1 việc làm tiếp (≤ 2 phút), vd chạy `/agent-team:task <task đầu tiên>` (dự án mới: `/agent-team:app <ý tưởng>`).
