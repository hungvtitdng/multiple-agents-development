<!-- Mẫu bài post lên board (board.py post), ≤ 15 dòng. Điểm chấm KHÔNG post: chỉ trả riêng về Lead. Xong lượt: board.py done --role <role> --body "<≤ 5 dòng>" rồi kết thúc ngay (không chờ Lead). -->
**Role:** <role>  **Task:** <task-id>  **Lượt:** S2-R2  **Gọi:** @role-a @role-b

## Ý kiến theo từng phương án
- **A:** ủng hộ / phản đối. Rủi ro cụ thể (file, màn hình, query, số liệu). Đề xuất.
- **B:** ...

## WHY (lượt hỏi: ≥ 2; dòng trống ngăn cách)
WHY @<role>: <vì sao ...?>

## Trả lời / biểu quyết WHY
RE WHY-<n>: <trả lời + bằng chứng>
AGREE WHY-<n>
DISAGREE WHY-<n>: <vì sao ...?>

## @ cần trả lời
- @<role>: ...

## Assumption
- <điều chưa chắc> → chọn <cách> vì <lý do>

## Kết luận
<1-2 dòng>

---
<!-- Mẫu GAP: dev/test-executor trả về Lead khi thiếu thông tin. Không tự đoán, không code phần này. -->
**GAP** · Role: <role> · Task: <task-id> · Phần bị dừng: <file/màn hình/AC>
- Thiếu gì: <câu hỏi cụ thể>
- Gặp ở đâu: <file:dòng / AC-n / test case>
- Vì sao ảnh hưởng: <sai dữ liệu, sai quyền, không test được...>
- Hướng thấy được: X (ưu/nhược) · Y (ưu/nhược)
- Loại (gợi ý): nghiệp vụ/AC · thiết kế/contract · quyền/dữ liệu nhạy cảm
- Phần khác vẫn làm tiếp: <có/không, phần nào>

---
<!-- Mẫu HỎI LEAD: mọi role trả về Lead khi thiếu thông tin để làm tiếp. Không tự quét repo, không tự đoán. -->
**HỎI LEAD** · Role: <role> · Task: <task-id>
- Cần gì: <câu hỏi / file / quy tắc cụ thể>
- Đã tìm ở: <CONTEXT, KB file nào, graphify gì> → không có
- Để làm gì: <bước nào đang chờ>

