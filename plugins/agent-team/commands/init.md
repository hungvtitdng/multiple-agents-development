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
   - docker-compose: file nằm trong repo hay repo khác, tên service DB và app, loại DB (postgres/mysql)
   - Branch gốc (develop/main/master) của **từng repo** (`git symbolic-ref --short refs/remotes/origin/HEAD`). Giống nhau → `BASE_BRANCH`. Repo nào khác → `BASE_BRANCHES="<repo>=<nhánh>"`.
   - **Có mấy repo git?** Tìm repo ở thư mục hiện tại và thư mục con cấp 1 (`.git`). Thư mục hiện tại là repo thì hỏi thêm user có repo khác đi kèm không (vd `../FrontEnd`).
   - **Có code sẵn không?** `git ls-files` có file mã nguồn (rb, py, js/ts, go, java, php, vue...) → dự án có sẵn code.
2b. **Nhiều repo → chọn repo chính** (chỉ hỏi khi ≥ 2 repo, 1 câu hỏi duy nhất bằng AskUserQuestion):
   - Câu hỏi: "Chọn repo chính, nơi chứa `.claude/`, `docs/`, `CLAUDE.md`". Mỗi lựa chọn là tên 1 repo tìm thấy. Gợi ý đầu tiên: repo BE/API.
   - Mọi file init tạo **trong repo chính**. **Không tạo gì ở thư mục cha.**
   - Config: `REPOS=". ../FrontEnd"` (`.` là repo chính). `BE_PATHS`, `FE_PATHS`, `TEST_PATHS` tính từ repo chính, vd `FE_PATHS="../FrontEnd"`.
   - Dặn user: mở Claude Code ở **repo chính**, rồi thêm repo còn lại bằng `/add-dir ../FrontEnd`.
3. **Tạo `.claude/agent-team.config`** từ `templates/agent-team.config.example`, điền giá trị đã nhận diện (kể cả `LINT_CMD`, `FORMAT_CMD`). Giữ mặc định `COST_TIER=standard` (economy | standard | max) và `LESSONS_PATH=docs/LESSONS.md`. Giá trị không chắc → `TODO` và báo user. Tuyệt đối không ghi password/KEY.
4. **Copy vào project**:
   - `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh` (chmod +x)
   - `templates/TASK.md`, `POST.md`, `SUMMARY.md`, `CONTEXT.md` → `.claude/agent-team/templates/`
5. **CLAUDE.md**: chưa có mục "## Agent Team" thì thêm nội dung `templates/claude-md-section.md` vào cuối. Không sửa phần khác.
5b. **Code graph (tùy chọn)**: hỏi user có muốn dùng không. Không → `USE_CODE_GRAPH=0`, bỏ qua.
   - Có → không cài gói ngoài, chỉ cần `python3` (nhiều repo: chạy ở repo chính):
     1. Copy `scripts/code-graph.py` → `.claude/agent-team/code-graph.py` (chmod +x).
     2. Build lần đầu: `.claude/agent-team/code-graph.py build` → `code-graph-out/GRAPH_REPORT.md`. Lỗi → báo user, không đoán.
     3. Báo user: graph quét file đã commit, hỗ trợ rb, py, js/ts, go, java, php, vue. Cạnh INFERRED là gợi ý.
6. **.gitignore**: `.agent-team/` và `code-graph-out/` thêm vào repo chính. `.env*`, dump thêm vào **mọi repo trong `REPOS`**. Thêm nếu chưa có:
   ```
   .agent-team/
   code-graph-out/
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
7b. **Dự án có sẵn code và không có `--skip-kb` → dựng nháp KB ngay:**
   1. Gọi subagent `agent-team:scout` (sonnet). Giao: đọc một lần mọi repo trong `REPOS`, điền KB theo mục "Việc 2" trong định nghĩa của Scout (`project-overview`, `architecture`, `tech-stack`, `domain-model`, `api/endpoints`, `database/schema`, `integrations/`, `testing/test-strategy`, `modules/<tên>/README.md`, `engineering/coding-standards.md`).
   2. Mọi mục gắn `Unverified`, có nguồn và `verified-at: <commit>`. Business rule suy từ code chỉ là `Assumption`. Quy chuẩn code là `Observed` (pattern chiếm đa số, kèm ví dụ `file:dòng`).
   3. Scout báo lại lệnh lint/format nhận diện được → điền vào `LINT_CMD`, `FORMAT_CMD` nếu step 2 chưa có.
   4. Repo lớn: Scout quét theo module chính và ghi rõ phần chưa quét. Lỗi hoặc quá dài → báo user, KB sẽ tạo dần ở các task sau.
   5. Dự án mới (chưa có code): bỏ qua bước này, chỉ giữ khung. Architect đặt quy chuẩn ở task đầu tiên.
8. **Ghi `release-notes.md`** (tạo nếu chưa có), mục `Release notes - DD/MM/YYYY`: đã cài agent team, file nào được thêm, key mới (`LINT_CMD`, `FORMAT_CMD`, `COST_TIER`, `LESSONS_PATH`).
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền, phần KB còn `Unverified`. **Không commit**, để user xem trước. Cuối cùng: đúng 1 việc làm tiếp (≤ 2 phút), vd chạy `/agent-team:run <task đầu tiên>`.
