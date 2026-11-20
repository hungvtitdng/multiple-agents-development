## Agent Team

Project dùng plugin `agent-team`. Chạy task: `/agent-team:task <task>`. Module mới trong app đang chạy (owner duyệt qua form, rồi chia task con): `/agent-team:module <ý tưởng>`. Làm cả app từ ý tưởng: `/agent-team:app <ý tưởng>` (tài liệu sản phẩm ở `docs/product/`, owner duyệt rồi mới code). Làm tiếp task dang dở: `/agent-team:resume <task-id>`. Hỏi về logic dự án (chỉ đọc, có dẫn nguồn): `/agent-team:ask <câu hỏi>`. Dựng/làm đầy KB từ code: `/agent-team:kb`.

- Config project: `.claude/agent-team.config` (nhánh gốc, đường dẫn BE/FE/test, DB clone, lint/format, `REPOS` nếu nhiều repo)
- Mọi tài liệu nằm trong `docs/` (Knowledge Base, **đọc trước khi làm**, mỗi thư mục có chủ ghi riêng, xem `docs/README.md`). Quy chuẩn code ở `docs/engineering/`.
- Nhiều repo con (`REPOS`): `.claude/`, `docs/` nằm ở repo chính; mỗi repo có branch `agent/<task-id>` riêng, commit/push bằng `git -C <repo> ...`
- Tài liệu mỗi task: `docs/agent-tasks/<task-id>/` gồm `TASK.md`, `CONTEXT.md` (Scout), `board/` (Lead ghi)
- Migration/test DB: chỉ qua `.claude/agent-team/agent-db-clone.sh` (DB clone, không đụng DB hiện tại). File migration **chỉ sinh** bằng `agent-db-clone.sh generate` (generator trong container), không tự tạo/đổi tên (guard chặn).
- Báo cáo mỗi task: `docs/agent-tasks/<task-id>/REPORT.html` (gửi client) + `REPORT.md` (`board.py report`).
- Giao diện phải dùng được ở mọi chiều rộng trong `VIEWPORTS` (config). Task có UI: E2E Playwright bằng `agent-db-clone.sh e2e <task-id>`, ảnh bằng chứng mỗi chiều rộng ở `docs/testing/evidence/<task-id>/` (hook kiểm trước S5).
- Thiết kế mỗi task: `docs/agent-tasks/<task-id>/design/`: `workflow.md`, `state.md` (BA), `sequence.md` (Architect), `mockup-<màn>.html` (ui-designer, **wireframe đen trắng đủ chức năng + trạng thái**). FE code đủ chức năng của wireframe nhưng dùng màu, font, component của dự án.

### Quy chuẩn chung (mọi agent)
- Mỗi task 1 branch `agent/<task-id>`. Tự commit + push. Không push/merge vào main/develop, không force push, không rewrite lịch sử.
- Commit **một dòng** `[role] task-id: mô tả`. Không body, không Co-authored-by/Signed-off-by (guard chặn).
- Không đọc/sửa/commit `.env*`, key, credentials, dump DB.
- Không sửa code cũ khi không cần thiết, không refactor ngoài phạm vi. Comment ngắn, chỉ khi cần.
- Theo đúng stack, convention và `docs/engineering/`. Chạy lint/format (`LINT_CMD`, `FORMAT_CMD`) trước khi commit.
- Thêm ENV/lệnh chạy mới → ghi `release-notes.md` (chỉ tên biến).
- **Không hỏi user.** Thiếu business rule: Lead chọn best solution, ghi nhãn `Assumption`, báo ở cuối. Kỹ thuật: team tự quyết. Ngoại lệ App Mode: câu nghiệp vụ gom vào form `.xlsx` gửi owner (mỗi câu 1 đề xuất của team, owner ghi OK hoặc góp ý; `owner-form.py build` / `import`), câu kỹ thuật hỏi dev; câu mức CAO phải có câu trả lời của owner trước khi code. Agent vẫn không hỏi, trả câu hỏi về Lead.
- Security bắt buộc mọi task. Critical/High phải sửa, Lead không được override.
- Debate bằng subagent trên **board chat SQLite** (`.claude/agent-team/board.py`): mỗi lượt agent đọc tóm tắt lượt trước + toàn bộ lượt đang mở, post bằng tên mình (≤ 15 dòng), `@role` = phải trả lời. Chỉ Lead mở/đóng lượt, tóm tắt, export. Điểm chấm không post, chỉ trả về Lead. Không ghi TASK.md.
- Skill chung của plugin (`agent-team:debate-board`, `acceptance-criteria`, `test-case-design`, `security-review`, `migration-safety`, `test-automation`, `code-review`, `decision-record`): agent tự nạp khi cần. Kiến thức riêng của dự án nằm trong KB `docs/`.
- Đọc `CONTEXT.md` của task, không tự quét lại repo. Bài học các task trước: `LESSONS_PATH` (mặc định `docs/LESSONS.md`). Đã sai một lần thì không vấp lại: Lead ghi lỗi ngay khi xảy ra (Sai gì, Nguyên nhân gốc, Cách tránh kiểm tra được); dev đọc trước khi code; Code Reviewer coi lặp lại lỗi cũ là High; lặp lại thì thành quy tắc trong `docs/engineering/review-checklist.md`.
- `challenger` là reviewer mù ticket (VỪA/LỚN ở S5): chỉ nhận yêu cầu gốc + diff, không đọc `docs/`.
- Mức model theo `COST_TIER` (economy | standard | max) trong config.
- Guard chặn theo giai đoạn (`.agent-team/stage` do Lead ghi): S1-S2 chỉ tài liệu, S3 chỉ code, S4 chỉ test; và theo chủ sở hữu KB. Ghi sai vùng bị chặn hoặc hoàn tác.
- Nhãn thông tin: `Verified` · `Unverified` · `Assumption` · `Observed` · `Planned` · `Deprecated`. Không ghi dự kiến như đã làm; không báo test PASS khi chưa chạy.
- Code graph = **Graphify** (nếu có `graphify-out/`): đọc `GRAPH_REPORT.md` trước, query bằng `graphify explain|affected|query|path` (nhiều repo: `--graph graphify-out/merged-graph.json`). Cạnh `INFERRED` chỉ là gợi ý. Chỉ Lead `graphify update`. Cấm `graphify extract` (gọi LLM), `install`, `hook install` (guard chặn).
- Trả lời ngắn (rút gọn từ i-have-adhd, MIT), áp dụng cho tin nhắn và báo cáo gửi user:
  - Dòng đầu là hành động tiếp theo hoặc kết quả, không lời dạo đầu, không tổng kết lại việc vừa làm, không câu chào kết.
  - Việc nhiều bước thì đánh số, mỗi bước một hành động. Danh sách dài thì gom nhóm, tối đa 5 mục mỗi nhóm.
  - Lỗi: nêu nguyên nhân + cách sửa. Ước lượng thời gian bằng số cụ thể.
  - Cuối cùng: đúng 1 việc user làm được trong 2 phút (nếu còn việc mở).
