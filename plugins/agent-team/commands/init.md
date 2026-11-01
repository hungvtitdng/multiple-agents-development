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
3. **Tạo `.claude/agent-team.config`** từ `templates/agent-team.config.example`, điền giá trị đã nhận diện.
   - Giá trị không chắc → để `TODO` và báo user.
   - Tuyệt đối không ghi password/KEY vào file này.
4. **Copy vào project**:
   - `scripts/agent-db-clone.sh` → `.claude/agent-team/agent-db-clone.sh` (chmod +x)
   - `templates/TASK.md`, `templates/POST.md`, `templates/SUMMARY.md` → `.claude/agent-team/templates/`
5. **CLAUDE.md**: nếu chưa có mục "## Agent Team" thì thêm nội dung `templates/claude-md-section.md` vào cuối. Không sửa phần khác.
5b. **Graphify (tùy chọn, code graph)**: hỏi user có muốn dùng không. Không → ghi `USE_GRAPHIFY=0` vào config, bỏ qua.
   - Có → làm lần lượt, **hỏi xác nhận trước khi cài**:
     1. `command -v graphify`. Chưa có thì đề nghị user chạy (đúng tên gói **graphifyy**, 2 chữ y; kiểm tra trang PyPI trỏ về `github.com/Graphify-Labs/graphify`):
        `uv tool install graphifyy==0.9.100` (hoặc `pipx install graphifyy==0.9.100`)
     2. `graphify install --project` (chỉ ghi vào project, không đụng `~/.claude`).
     3. **Không** chạy `graphify hook install` hay cài hook Claude Code của Graphify (dễ đụng hook guard của agent-team). Lead tự cập nhật graph theo giai đoạn.
     4. Build graph lần đầu: `/graphify .` (hoặc code-only nếu repo ít tài liệu). Lệnh nào lỗi → báo user, không đoán.
   - Ghi chú vào release-notes: tùy chọn `GRAPHIFY_QUERY_LOG_DISABLE=1` nếu không muốn log câu query vào `~/.cache/graphify-queries.log`.
6. **.gitignore**: thêm nếu chưa có:
   ```
   .agent-team/
   graphify-out/
   .env*
   !.env.example
   *.dump
   *.sql.gz
   ```
7. Tạo `docs/agent-tasks/.gitkeep`.
8. **Ghi `release-notes.md`** (tạo nếu chưa có), mục `Release notes - DD/MM/YYYY`: đã cài agent team, file nào được thêm.
9. Báo user: danh sách file đã tạo/sửa, các `TODO` cần điền. **Không commit**, để user xem trước.
