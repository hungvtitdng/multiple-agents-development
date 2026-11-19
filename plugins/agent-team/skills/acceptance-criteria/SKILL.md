---
name: acceptance-criteria
description: Viết và phản biện acceptance criteria (AC) Given/When/Then đánh số AC-n, kèm checklist điểm mơ hồ nghiệp vụ. Dùng khi BA viết AC hoặc test-designer phản biện AC.
---

# Acceptance criteria

## Dạng chuẩn
```
AC-<n>: <tên ngắn>
  Given <trạng thái dữ liệu + người dùng + quyền>
  When  <một hành động>
  Then  <kết quả quan sát được: dữ liệu, response, UI, thông báo>
  Nhãn: Confirmed | Verified | Assumption | Proposed  · Nguồn: <ticket / file:dòng / KB>
```
- Một AC = một hành vi. Có "và" trong When → tách AC.
- Then phải **kiểm chứng được**: giá trị cụ thể, mã lỗi, trạng thái, số bản ghi. Không dùng "hợp lý", "nhanh", "thân thiện".
- Mỗi AC chạy được thành ít nhất 1 test case.

## Đủ loại AC
Với mỗi chức năng, kiểm có đủ:
1. Luồng chính (happy path).
2. Dữ liệu sai/thiếu → validation, thông báo lỗi.
3. Không có quyền / không phải chủ dữ liệu → bị chặn (mã lỗi cụ thể).
4. Trạng thái không hợp lệ (đơn đã huỷ, đã thanh toán...) → hành vi gì.
5. Ảnh hưởng chức năng hiện có (regression): cái gì phải giữ nguyên.

## Checklist điểm mơ hồ
Hỏi từng câu; câu nào yêu cầu không trả lời được → điểm mơ hồ, đưa X/Y/Z và chọn theo quy tắc ở dưới.
| Nhóm | Câu hỏi |
|---|---|
| Actor, quyền | Ai được làm? Admin/chủ sở hữu/người cùng tổ chức khác nhau thế nào? |
| Trạng thái | Áp dụng ở trạng thái nào? Chuyển trạng thái nào bị cấm? |
| Giới hạn | Rỗng, 0, âm, tối đa, trùng lặp, ký tự đặc biệt? |
| Thời gian | Múi giờ, hết hạn, ngày nghỉ, cuối tháng? |
| Tiền, số | Làm tròn, tiền tệ, thuế, chia phần? |
| Đồng thời | Hai người cùng sửa, bấm 2 lần, retry → idempotent? |
| Dữ liệu cũ | Bản ghi đã có trước thay đổi xử lý thế nào? Cần backfill? |
| Phản hồi | Thông báo, email, log/audit, ai nhận? |
| Xoá | Xoá mềm hay cứng? Dữ liệu liên quan ra sao? |

## Chọn cách hiểu khi mơ hồ (không hỏi user)
Ưu tiên theo thứ tự: (1) khớp code/KB hiện tại, (2) ít ảnh hưởng dữ liệu và code cũ, (3) **dễ sửa lại nhất nếu sai**, (4) an toàn hơn về quyền. Ghi `Assumption` + lý do; Lead đưa vào "Giả định cần xem lại".

## Phản biện AC (test-designer)
Với mỗi AC: kiểm chứng được không? thiếu loại nào trong 5 loại ở trên? mâu thuẫn AC khác? Đề xuất **AC sửa cụ thể**, không chỉ nêu lỗi.
