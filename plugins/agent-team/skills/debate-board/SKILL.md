---
name: debate-board
description: Cách debate trên board chat SQLite của agent team (board.py) - đọc gì trước, post thế nào, phản biện ra sao, trả lời @mention. Dùng khi Lead giao một lượt debate hoặc review có post lên board.
---

# Debate trên board

Board là phòng chat chung của task, lưu trong SQLite. Ai cũng đọc được mọi bài; chỉ post được bằng tên mình. Lệnh chạy thẳng (không qua `python3`):

```
.claude/agent-team/board.py read   <task-id>                     # tóm tắt các lượt trước + toàn bộ lượt đang mở
.claude/agent-team/board.py read   <task-id> --mention <role>    # tin gọi tên mình
.claude/agent-team/board.py read   <task-id> --stage S2 --round 1  # xem lại chi tiết một lượt cũ
.claude/agent-team/board.py status <task-id>                     # lượt đang mở, ai chưa post, @ và WHY còn nợ
.claude/agent-team/board.py whys   <task-id> [--open]            # danh sách WHY + trạng thái
.claude/agent-team/board.py post   <task-id> --role <role> [--reply <id>] <<'EOF'
<nội dung>
EOF
```

## 1. Đọc trước khi viết
1. `board.py read <task-id>`: tóm tắt các lượt trước (Lead viết) + **toàn bộ** bài của lượt đang mở.
2. `board.py read <task-id> --mention <role>`: mọi tin gọi tên mình.
3. Chỉ mở lượt cũ (`--stage --round`) hoặc 1 câu WHY (`--why <n>`) khi cần trích chi tiết. Không đọc lại cả board, không `--all`.

## 2. Viết bài (theo `.claude/agent-team/templates/POST.md`)
- Lượt hỏi chỉ đặt WHY (mục 3), chưa kết luận. Lượt sau mới trả lời / biểu quyết.
- ≤ 15 dòng. Reviewer liệt kê issue được dài hơn (board chặn > 80 dòng).
- Góp ý **mọi phương án** từ góc nhìn vai trò của mình, không chỉ trả lời người gọi tên mình.
- Phản biện phải cụ thể và kiểm chứng được: file, màn hình, query, số liệu, AC-n.
  - Tốt: "B: `OrdersController#index` gọi `order.customer` trong vòng lặp → N+1 khi list 100 đơn."
  - Không chấp nhận: "B không tốt", "nên cân nhắc thêm".
- Trả lời một bài cụ thể: `--reply <id>`. Gọi người phải trả lời: viết `@<role>` trong bài.
- Bổ sung hoặc đổi ý: post bài mới, nói rõ đổi gì và vì sao. Không có lệnh sửa/xoá.

## 3. Hỏi WHY trước, quyết sau
Debate là để **hiểu vì sao**, không phải bỏ phiếu nhanh. Mỗi dòng một lệnh, đứng đầu dòng (dòng sau không có từ khoá thì nối vào nội dung; dòng trống để ngắt):
```
WHY @solution-architect: Vì sao cần bảng mới thay vì thêm cột vào orders?
RE WHY-3: Vì 1 đơn có nhiều lần huỷ một phần (app/models/order.rb:42), một cột không chứa được.
AGREE WHY-3
DISAGREE WHY-3: Vì sao không dùng cột JSON, số lần huỷ tối đa là bao nhiêu?
```
- **Câu hỏi tốt** hỏi về: lý do, bằng chứng, phương án khác đã xét, hậu quả khi sai. Không hỏi kiểu buộc tội ("vì sao lại sai như vậy?").
- **Trả lời tốt**: một câu kết luận + bằng chứng kiểm chứng được. Không có bằng chứng thì nói rõ "chưa chắc" và vì sao vẫn chọn.
- **Biểu quyết**: `AGREE` chỉ khi bị thuyết phục. Chưa thuyết phục thì `DISAGREE` kèm câu vì sao tiếp theo; câu đó đào sâu thêm một tầng (kiểu 5 Whys), không lặp câu cũ.
- WHY đóng khi **cả team debate** (trừ người trả lời) AGREE. Trả lời mới thì mọi người biểu quyết lại.
- Xem việc còn nợ: `board.py status <task-id>` hoặc `board.py whys <task-id> --open`.

## 3b. @mention là nghĩa vụ
- Bị `@<role>` gọi thì **phải trả lời** ở lượt sau (đồng ý / không đồng ý + lý do). `status` liệt kê @ chưa trả lời.
- Đồng ý thì nói ngắn "Đồng ý #12" để đóng; im lặng sau khi Lead nhắc = coi như đồng ý.

## 4. Không đưa lên board
- **Điểm chấm phương án**: chỉ ghi trong kết quả trả về Lead (bỏ phiếu kín). Không post điểm, không hỏi điểm người khác.
- Secret, giá trị `.env`, dữ liệu thật của khách.
- Suy nghĩ dài dòng, lặp lại ý đã có (dẫn số tin thay vì chép lại).

## 4b. Lead tóm tắt mỗi lượt
Lượt chỉ đóng được khi Lead đã `summary` (board từ chối `close`). Lượt sau mọi người đọc tóm tắt thay cho bài cũ, nên bài post phải tự đủ ý, không dựa vào việc người khác nhớ lượt trước.

## 5. Kết thúc lượt (bắt buộc `done`, không chờ Lead)
1. Việc dài (vẽ nhiều màn, viết nhiều test): sau mỗi phần báo tiến độ `board.py progress <task-id> --role <role> --step "4/11 màn" --eta 20`.
2. Xong: `board.py done <task-id> --role <role> --body "<≤ 5 dòng: số tin đã post, điểm chấm (nếu lượt có chấm), Assumption / GAP / HỎI LEAD>"`. Lead đọc kết quả từ đây (SQLite), kể cả khi tin nhắn trả về bị lạc.
3. **Kết thúc ngay**, trả đúng 5 dòng đó về Lead. Không post lại, không chờ Lead xác nhận, không hỏi "Lead đã nhận chưa": board từ chối post / done thêm ở lượt này.
