## Agent Team

Project dùng plugin `agent-team`. Chạy task: `/agent-team:run <task>`. Làm tiếp task dang dở: `/agent-team:resume <task-id>`. Hỏi về logic dự án (chỉ đọc, có dẫn nguồn): `/agent-team:ask <câu hỏi>`. Dựng/làm đầy KB từ code: `/agent-team:kb`.

- Config project: `.claude/agent-team.config` (nhánh gốc, đường dẫn BE/FE/test, DB clone, lint/format, `REPOS` nếu nhiều repo)
- Mọi tài liệu nằm trong `docs/` (Knowledge Base, **đọc trước khi làm**, mỗi thư mục có chủ ghi riêng, xem `docs/README.md`). Quy chuẩn code ở `docs/engineering/`.
- Nhiều repo con (`REPOS`): `.claude/`, `docs/` nằm ở repo chính; mỗi repo có branch `agent/<task-id>` riêng, commit/push bằng `git -C <repo> ...`
- Tài liệu mỗi task: `docs/agent-tasks/<task-id>/` gồm `TASK.md`, `CONTEXT.md` (Scout), `board/` (Lead ghi)
- Migration/test DB: chỉ qua `.claude/agent-team/agent-db-clone.sh` (DB clone, không đụng DB hiện tại)

### Quy chuẩn chung (mọi agent)
- Mỗi task 1 branch `agent/<task-id>`. Tự commit + push. Không push/merge vào main/develop, không force push, không rewrite lịch sử.
- Commit **một dòng** `[role] task-id: mô tả`. Không body, không Co-authored-by/Signed-off-by (guard chặn).
- Không đọc/sửa/commit `.env*`, key, credentials, dump DB.
- Không sửa code cũ khi không cần thiết, không refactor ngoài phạm vi. Comment ngắn, chỉ khi cần.
- Theo đúng stack, convention và `docs/engineering/`. Chạy lint/format (`LINT_CMD`, `FORMAT_CMD`) trước khi commit.
- Thêm ENV/lệnh chạy mới → ghi `release-notes.md` (chỉ tên biến).
- **Không hỏi user.** Thiếu business rule: Lead chọn best solution, ghi nhãn `Assumption`, báo ở cuối. Kỹ thuật: team tự quyết.
- Security bắt buộc mọi task. Critical/High phải sửa, Lead không được override.
- Debate bằng subagent: agent trả kết quả (≤ 15 dòng) cho Lead, không ghi board/TASK.md. Lead chuyển ý kiến giữa các lượt. Điểm chấm chỉ Lead thấy.
- Đọc `CONTEXT.md` của task, không tự quét lại repo. Bài học các task trước: `LESSONS_PATH` (mặc định `docs/LESSONS.md`). Đã sai một lần thì không vấp lại: Lead ghi lỗi ngay khi xảy ra (Sai gì, Nguyên nhân gốc, Cách tránh kiểm tra được); dev đọc trước khi code; Code Reviewer coi lặp lại lỗi cũ là High; lặp lại thì thành quy tắc trong `docs/engineering/review-checklist.md`.
- `challenger` là reviewer mù ticket (VỪA/LỚN ở S5): chỉ nhận yêu cầu gốc + diff, không đọc `docs/`.
- Mức model theo `COST_TIER` (economy | standard | max) trong config.
- Guard chặn theo giai đoạn (`.agent-team/stage` do Lead ghi): S1-S2 chỉ tài liệu, S3 chỉ code, S4 chỉ test; và theo chủ sở hữu KB. Ghi sai vùng bị chặn hoặc hoàn tác.
- Nhãn thông tin: `Verified` · `Unverified` · `Assumption` · `Observed` · `Planned` · `Deprecated`. Không ghi dự kiến như đã làm; không báo test PASS khi chưa chạy.
- Code graph (nếu có `code-graph-out/`): đọc `GRAPH_REPORT.md` trước, query bằng `.claude/agent-team/code-graph.py who-uses|uses|explain`. Cạnh `INFERRED` chỉ là gợi ý. Chỉ Lead build.
- Trả lời ngắn (rút gọn từ i-have-adhd, MIT), áp dụng cho tin nhắn và báo cáo gửi user:
  - Dòng đầu là hành động tiếp theo hoặc kết quả, không lời dạo đầu, không tổng kết lại việc vừa làm, không câu chào kết.
  - Việc nhiều bước thì đánh số, mỗi bước một hành động. Danh sách dài thì gom nhóm, tối đa 5 mục mỗi nhóm.
  - Lỗi: nêu nguyên nhân + cách sửa. Ước lượng thời gian bằng số cụ thể.
  - Cuối cùng: đúng 1 việc user làm được trong 2 phút (nếu còn việc mở).
