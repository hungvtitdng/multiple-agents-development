---
description: Cài agent team cho project hiện tại - tạo config, copy script DB clone + template, thêm mục Agent Team vào CLAUDE.md.
model: sonnet
---

Thiết lập agent team cho project hiện tại. Liệt kê ngắn từng bước trước khi làm.

1. **Tìm thư mục plugin**:
   `find ~/.claude/plugins -type d -path "*agent-team" -exec test -f {}/scripts/agent-db-clone.sh \; -print | head -1`
2. **Nhận diện project** (chỉ đọc):
   - Stack BE/FE/test: Gemfile, package.json, thư mục spec/test
   - docker-compose: file nằm trong repo hay repo khác, tên service DB và app, loại DB (postgres/mysql)
   - Branch gốc (develop/main/master) của **từng repo** (`git symbolic-ref --short refs/remotes/origin/HEAD`). Giống nhau → `BASE_BRANCH`. Repo nào khác → ghi vào `BASE_BRANCHES="<repo>=<nhánh>"`.
   - **Có mấy repo git?** Tìm repo ở thư mục hiện tại và thư mục con cấp 1 (`.git`). Thư mục hiện tại là repo thì hỏi thêm user có repo khác đi kèm không (vd `../FrontEnd`).
2b. **Nhiều repo → chọn repo chính** (chỉ hỏi khi ≥ 2 repo, 1 câu hỏi duy nhất bằng AskUserQuestion):
   - Câu hỏi: "Chọn repo chính, nơi chứa `.claude/`, `docs/`, `CLAUDE.md`". Mỗi lựa chọn là tên 1 repo tìm thấy. Gợi ý đầu tiên: repo BE/API (nơi có logic nghiệp vụ).
   - Mọi file init (`.claude/`, `docs/`, `CLAUDE.md`, `code-graph-out/`) tạo **trong repo chính**. **Không tạo gì ở thư mục cha.**
   - Config: `REPOS=". ../FrontEnd"` (`.` là repo chính, repo khác ghi đường dẫn tới nó từ repo chính). `BE_PATHS`, `FE_PATHS`, `TEST_PATHS` tính từ repo chính, vd `BE_PATHS="app lib"`, `FE_PATHS="../FrontEnd"`, `TEST_PATHS="spec ../FrontEnd/e2e"`.
   - Dặn user: mở Claude Code ở **repo chính**, rồi thêm repo còn lại bằng `/add-dir ../FrontEnd` (hoặc `claude --add-dir ../FrontEnd`).
3. **Tạo `.claude/agent-team.config`** từ `templates/agent-team.config.example`, điền giá trị đã nhận diện.
   - Giá trị không chắc → để `TODO` và báo user.
   - Tuyệt đối không ghi password/KEY vào file này.
4. **Copy vào project**:
   - `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh` (chmod +x)
   - `templates/TASK.md`, `templates/POST.md`, `templates/SUMMARY.md` → `.claude/agent-team/templates/`
5. **CLAUDE.md**: nếu chưa có mục "## Agent Team" thì thêm nội dung `templates/claude-md-section.md` vào cuối. Không sửa phần khác.
5b. **Code graph (tùy chọn)**: hỏi user có muốn dùng không. Không → ghi `USE_CODE_GRAPH=0` vào config, bỏ qua.
   - Có → không cài gói ngoài, chỉ cần `python3` (nhiều repo: chạy ở repo chính, graph gộp tất cả repo trong `REPOS`):
     1. Copy `scripts/code-graph.py` → `.claude/agent-team/code-graph.py` (chmod +x).
     2. Build lần đầu: `.claude/agent-team/code-graph.py build` → `code-graph-out/GRAPH_REPORT.md`. Lệnh lỗi → báo user, không đoán.
     3. Báo user: graph quét file đã commit (`git ls-files`), hỗ trợ rb, py, js/ts, go, java, php, vue. Cạnh INFERRED là gợi ý.
6. **.gitignore**: `.agent-team/` và `code-graph-out/` thêm vào repo chính. Các dòng `.env*`, dump thêm vào **mọi repo trong `REPOS`**. Thêm nếu chưa có:
   ```
   .agent-team/
   code-graph-out/
   .env*
   !.env.example
   *.dump
   *.sql.gz
   ```
7. **Tạo cấu trúc `docs/`** trong repo chính (mọi tài liệu nằm ở đây, tên thư mục luôn là `docs` viết thường, vì guard so khớp phân biệt hoa thường):
   ```
   docs/
   ├── domain/        knowledge base: BA ghi, mọi role đọc
   │   ├── README.md, glossary.md, business-rules.md, decisions.md   (copy từ templates/domain/, không ghi đè file đã có)
   └── agent-tasks/   task + board (thêm .gitkeep)
   ```
   - Project đã có tài liệu nghiệp vụ nơi khác → hỏi user, không tự di chuyển.
   - Đã có `Docs/` viết hoa → hỏi user đổi tên thành `docs` (`git mv Docs docs`) trước khi tạo.
8. **Ghi `release-notes.md`** (tạo nếu chưa có), mục `Release notes - DD/MM/YYYY`: đã cài agent team, file nào được thêm.
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền. **Không commit**, để user xem trước.
