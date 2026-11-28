---
description: Chạy nhiều task độc lập cùng lúc từ danh sách mã ticket - mỗi task 1 phiên Claude nền trong worktree riêng, không cần mở thêm terminal. `-s` xem trạng thái.
argument-hint: <mã ticket 1> <mã ticket 2> ... | mine | -s
---

Tham số:

$ARGUMENTS

Bạn chỉ **chuẩn bị và mở phiên**, không làm task, không chờ task xong. Trả lời user ngắn: dòng đầu là kết quả, cuối là đúng 1 việc user làm tiếp.

## `-s` (hoặc không có tham số): xem trạng thái
Chạy `python3 .claude/agent-team/pool.py batch`, in lại nguyên bảng rồi dừng. Dòng `⏸ ĐANG DỪNG` đưa lên đầu, kèm lệnh `claude attach <id>` của nó.

## `mine` hoặc user viết bằng lời ("làm các task đang giao cho tôi ở To Do"): lấy danh sách rồi chạy
1. `python3 .claude/agent-team/pool.py batch --mine --dry` → in danh sách mã (lấy bằng `TICKET_LIST_CMD`). Lệnh báo chưa biết nguồn ticket: phiên có tool đọc tracker (connector / MCP của Jira, Linear, GitHub) → dùng tool đó tìm ticket đang giao cho user và chưa làm, lấy danh sách mã, ghi nội dung từng ticket theo mục 1 rồi chạy `batch <các mã>` (vẫn áp luật > 5 mã thì hỏi). Không có tool → chép nguyên hướng dẫn của lệnh cho user, dừng.
2. Danh sách "chưa mở" **≤ 5 mã** → chạy luôn `python3 .claude/agent-team/pool.py batch --mine`. **> 5 mã** → in danh sách, hỏi user 1 lần "chạy cả N task?" rồi mới chạy (mỗi task là 1 phiên đầy đủ).
3. User nêu điều kiện lọc khác với `TICKET_LIST_CMD` (sprint khác, trạng thái khác) → không tự sửa lệnh: chạy `--dry`, chọn mã khớp lời user rồi chạy `batch <các mã đó>`; không chắc mã nào khớp thì hỏi.
4. Báo cáo như mục 3.

## 1. Nội dung từng ticket
Nguồn ticket khai ở `.claude/agent-team.local.config` (riêng máy, không commit); token của nguồn đó nằm ở `.claude/agent-team.secret` (hook chặn đọc, chỉ script dùng: không tìm cách đọc hay in).
- Jira (có key trong `agent-team.secret`) / GitHub (`TICKET_SOURCE=github`) / có `TICKET_CMD` → bỏ qua bước này, script tự lấy.
- Còn lại → với mỗi mã cần file `.agent-team/tickets/<mã>.md` chứa **nguyên văn** yêu cầu (tiêu đề, mô tả, tiêu chí nghiệm thu, bình luận có quyết định):
  - File đã có → dùng luôn.
  - Phiên có tool đọc tracker (connector / MCP của Jira, Linear, GitHub) → đọc ticket, ghi nguyên văn vào file. Không tóm tắt, không thêm ý của bạn.
  - Không có → **không đoán nội dung**. Bỏ mã đó ra, cuối cùng báo user: điền key Jira vào `.claude/agent-team.secret`, hoặc dán nội dung vào file trên.

## 2. Mở phiên
Một lệnh cho mọi mã:
```
python3 .claude/agent-team/pool.py batch <mã 1> <mã 2> ...
```
- Mỗi mã: worktree `.worktrees/<mã>` + branch `task/<mã>` + cổng, DB riêng → 1 phiên Claude nền chạy `/agent-team:task` trong đó.
- Tối đa `MAX_PARALLEL` task cùng lúc; mã còn lại xếp hàng, tự mở khi có chỗ.
- Phiên nền chạy ở chế độ quyền `BATCH_PERMISSION` (mặc định `auto`); hook của plugin vẫn chặn như phiên thường.

## 3. Báo cáo (≤ 8 dòng) rồi dừng
- Bảng: mã · đang chạy / chờ / thiếu nội dung.
- Các task **không biết nhau**: 2 task sửa cùng file hoặc cùng thêm migration thì conflict lúc merge, user tự xử lý.
- Cho user: xem trạng thái `/agent-team:tasks -s` · task dừng giữa chừng sẽ có thông báo trên máy, vào trả lời bằng `claude attach <id>` · task xong (đã commit + push) `python3 .claude/agent-team/pool.py side <mã> --done`.
