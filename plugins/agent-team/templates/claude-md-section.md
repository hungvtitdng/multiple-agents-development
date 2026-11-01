## Agent Team

Project dùng plugin `agent-team`. Chạy task: `/agent-team:run <task>`.

- Config project: `.claude/agent-team.config` (branch gốc, đường dẫn BE/FE/test, DB clone, `REPOS` nếu nhiều repo)
- Mọi tài liệu nằm trong `docs/`: `docs/domain/` (knowledge base: thuật ngữ, quy tắc nghiệp vụ, quyết định; **đọc trước khi làm**, chỉ BA/Lead ghi) và `docs/agent-tasks/` (task + board)
- Nhiều repo con (`REPOS`): `.claude/`, `docs/` nằm ở repo chính; mỗi repo có branch `agent/<task-id>` riêng, commit/push bằng `git -C <repo> ...`
- Tài liệu mỗi task: `docs/agent-tasks/<task-id>/TASK.md` (Lead) + `board/` (nơi debate chung)
- Migration/test DB: chỉ qua `.claude/agent-team/agent-db-clone.sh` (DB clone, không đụng DB hiện tại)

### Quy tắc chung (mọi agent)
- Mỗi task 1 branch `agent/<task-id>`. Tự commit + push. Không push/merge vào main/develop, không force push.
- Không đọc/sửa/commit `.env*`, key, credentials, dump DB.
- Không sửa code cũ khi không cần thiết. Comment ngắn, chỉ khi cần.
- Theo đúng stack và convention đang có.
- Thêm ENV/lệnh chạy mới → ghi `release-notes.md` (chỉ tên biến).
- Không hỏi lại user: điểm mơ hồ thì team debate, bế tắc thì Lead quyết.
- Security bắt buộc mọi task. Lỗi Critical/High phải sửa, Lead không được override.
- Debate trên board, không debate qua tin nhắn. Mỗi vòng đọc `board/SUMMARY.md` + toàn bộ bài post của vòng hiện tại.
- Bài post: `board/S<giai đoạn>-R<vòng>-<role>-<n>.md`, đã post thì không sửa. `@role` = bắt buộc trả lời.
- Guard chặn theo giai đoạn (`.agent-team/stage` do Lead ghi): S3 chỉ ghi code, S4 chỉ ghi test. Ghi sai vùng sẽ bị chặn hoặc hoàn tác.
- Code graph (nếu có `code-graph-out/`): đọc `GRAPH_REPORT.md` trước, query bằng `.claude/agent-team/code-graph.py who-uses|uses|explain`. Cạnh `INFERRED` chỉ là gợi ý. Chỉ Lead build.
- Trả lời ngắn (rút gọn từ i-have-adhd, MIT), áp dụng cho tin nhắn và báo cáo gửi user, không áp dụng cho bài post board:
  - Dòng đầu là hành động tiếp theo hoặc kết quả, không lời dạo đầu, không tổng kết lại việc vừa làm, không câu chào kết.
  - Việc nhiều bước thì đánh số, mỗi bước một hành động. Danh sách dài thì gom nhóm, tối đa 5 mục mỗi nhóm.
  - Lỗi: nêu nguyên nhân + cách sửa. Ước lượng thời gian bằng số cụ thể.
  - Cuối cùng: đúng 1 việc user làm được trong 2 phút (nếu còn việc mở).
- Điểm chấm (V4): gửi riêng cho Lead, không ghi file, không post board.
