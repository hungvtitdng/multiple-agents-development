## Agent Team

Project dùng plugin `agent-team`. Chạy task: `/agent-team:run <task>`.

- Config project: `.claude/agent-team.config` (branch gốc, đường dẫn BE/FE/test, DB clone)
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
- Code graph (nếu có `graphify-out/`): đọc `GRAPH_REPORT.md` trước, query bằng `graphify query/path/explain`. Cạnh `INFERRED` chỉ là gợi ý. Chỉ Lead build/update.
- Điểm chấm (V4): gửi riêng cho Lead, không ghi file, không post board.
