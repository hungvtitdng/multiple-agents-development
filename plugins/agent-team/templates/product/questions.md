# Sổ câu hỏi

> Lead ghi. Mọi điểm mơ hồ thành 1 dòng, không "ngầm hiểu".
> - **Đề xuất của team**: 1 best solution (OWNER: BA đề xuất, DEV: Architect đề xuất), bắt buộc. **Vì sao**: 1 câu.
> - **Câu OWNER viết cho người không biết kỹ thuật, ngắn, đi thẳng vào điều cần quyết.** Câu hỏi = 1 câu hỏi quy tắc (≤ 25 từ), không kể chuyện tên người / số liệu, gộp câu cùng ý; viết tiếng Việt, từ tiếng Anh thông dụng (app, email, Excel, OTP, responsive, Admin...) giữ nguyên, không dịch. Đề xuất = quy tắc + người dùng thấy gì (≤ 40 từ). Vì sao = **giải thích** 1 câu (bắt buộc với OWNER, ≤ 30 từ). Owner đọc 1 lần là hiểu, trả lời được bằng OK hoặc 1 câu. Không mã nội bộ (R-, F-, AC-, Q-...), không từ kỹ thuật (API, status, role, database...): `owner-form.py build` từ chối (kể cả câu quá dài).
>   - Sai (mã kỹ thuật): "R-3: cho phép cancel booking khi status = PENDING?"
>   - Sai (dài, kể chuyện): "Anh Nam đã xong 6/10 mục tiêu năm 2027... cây của anh Nam có lên cấp chỉ theo số mục tiêu không?"
>   - Đúng: Câu hỏi "Khách có được tự huỷ lịch trên app không?" · Đề xuất "Được huỷ nếu còn hơn 2 tiếng; khách bấm Huỷ, tiệm nhận tin báo." · Vì sao "Huỷ sát giờ thì thợ ngồi không; không cho huỷ thì lễ tân phải huỷ hộ."
> - **Ai trả lời**: `OWNER` (nghiệp vụ, quy tắc, tiền, quyền) → form mục A · `DEV` (stack, hosting, git, hạ tầng) → form mục B. Cùng 1 file, không hỏi ngay.
> - **Mức**: `CAO` (sai thì làm lại nhiều) / `THẤP`.
> - **Trạng thái**: `MỞ` · `CHỜ OWNER` / `CHỜ DEV` (đã gửi form) · `ĐÃ TRẢ LỜI` · `GIẢ ĐỊNH` (chỉ mức THẤP).
> - **Nhóm** (bắt buộc với OWNER): vị trí trong hành trình, form xếp theo số đầu: `1. Tổng quan`, `2. Vai trò & quyền`, `3. F-1 Đặt lịch`... Câu trong luồng ghi theo thứ tự bước. Mỗi luồng F-n có ít nhất 1 câu (câu xác nhận luồng).
> - **Màn**: `S-n` có mockup (bắt buộc khi Nhóm có F-n). Form in tên màn + file mockup.
> Gap-check: câu `CAO` chưa `ĐÃ TRẢ LỜI` thì không qua cổng. Form: `.claude/agent-team/owner-form.py build`, nhập lại: `owner-form.py import <file>`.

| Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái | Trả lời | Nhóm | Màn |
|---|---|---|---|---|---|---|---|---|---|
