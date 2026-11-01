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
   - Branch gốc (develop/main)
   - **1 repo hay nhiều repo?** Thư mục hiện tại không phải repo git nhưng có thư mục con có `.git` (vd `be/`, `fe/`) → nhiều repo: ghi `REPOS="be fe"`, `BE_PATHS="be"`, `FE_PATHS="fe"`, `TEST_PATHS` tính từ thư mục cha (vd `be/spec fe/e2e`). Hỏi user nếu không chắc.
3. **Tạo `.claude/agent-team.config`** từ `templates/agent-team.config.example`, điền giá trị đã nhận diện.
   - Giá trị không chắc → để `TODO` và báo user.
   - Tuyệt đối không ghi password/KEY vào file này.
4. **Copy vào project**:
   - `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh` (chmod +x)
   - `templates/TASK.md`, `templates/POST.md`, `templates/SUMMARY.md` → `.claude/agent-team/templates/`
5. **CLAUDE.md**: nếu chưa có mục "## Agent Team" thì thêm nội dung `templates/claude-md-section.md` vào cuối. Không sửa phần khác.
5b. **Code graph (tùy chọn)**: hỏi user có muốn dùng không. Không → ghi `USE_CODE_GRAPH=0` vào config, bỏ qua.
   - Có → không cài gói ngoài, chỉ cần `python3` (nhiều repo: chạy ở thư mục cha, graph gộp tất cả repo trong `REPOS`):
     1. Copy `scripts/code-graph.py` → `.claude/agent-team/code-graph.py` (chmod +x).
     2. Build lần đầu: `.claude/agent-team/code-graph.py build` → `code-graph-out/GRAPH_REPORT.md`. Lệnh lỗi → báo user, không đoán.
     3. Báo user: graph quét file đã commit (`git ls-files`), hỗ trợ rb, py, js/ts, go, java, php, vue. Cạnh INFERRED là gợi ý.
6. **.gitignore** (nhiều repo: `.agent-team/` và `code-graph-out/` nằm ở thư mục cha, chỉ thêm nếu thư mục cha là repo git và thêm luôn tên các repo con vào đó; các dòng `.env*`, dump thêm vào **từng repo con**). Thêm nếu chưa có:
   ```
   .agent-team/
   code-graph-out/
   .env*
   !.env.example
   *.dump
   *.sql.gz
   ```
7. **Tạo cấu trúc `docs/`** (mọi tài liệu nằm ở đây; nhiều repo thì `docs/` ở thư mục cha):
   ```
   docs/
   ├── domain/        knowledge base: BA ghi, mọi role đọc
   │   ├── README.md, glossary.md, business-rules.md, decisions.md   (copy từ templates/domain/, không ghi đè file đã có)
   └── agent-tasks/   task + board (thêm .gitkeep)
   ```
   - Project đã có tài liệu nghiệp vụ nơi khác → hỏi user, không tự di chuyển.
   - Nhiều repo: khuyên user `git init` ở thư mục cha để versioning `docs/` và `.claude/` (repo docs), thêm các repo con vào `.gitignore` của nó.
8. **Ghi `release-notes.md`** (tạo nếu chưa có), mục `Release notes - DD/MM/YYYY`: đã cài agent team, file nào được thêm.
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền. **Không commit**, để user xem trước.
