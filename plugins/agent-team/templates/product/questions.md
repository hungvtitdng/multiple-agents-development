# Sổ câu hỏi

> Lead ghi. Mọi điểm mơ hồ thành 1 dòng, không "ngầm hiểu".
> - **Đề xuất của team**: 1 best solution (OWNER: BA đề xuất, DEV: Architect đề xuất), bắt buộc. **Vì sao**: 1 câu.
> - **Câu OWNER viết cho người không biết kỹ thuật, về nghiệp vụ.** Câu hỏi = tình huống có người + số liệu + hỏi có / không. Đề xuất = quy tắc + người dùng thấy gì. Vì sao = **giải thích** (bắt buộc với OWNER): vì sao phải quyết, chọn khác thì sao. Không mã nội bộ (R-, F-, AC-, Q-...), không từ kỹ thuật (API, status, role, database...): `owner-form.py build` từ chối.
>   - Sai: "R-3: cho phép cancel booking khi status = PENDING?"
>   - Đúng: Câu hỏi "Chị Lan đặt lịch 9h sáng mai, tối nay chị muốn huỷ. Chị có được tự huỷ trên app không?" · Đề xuất "Được huỷ miễn phí nếu còn hơn 2 tiếng. Chị bấm Huỷ, thấy 'Đã huỷ', tiệm nhận tin báo." · Vì sao "Huỷ sát giờ thì thợ ngồi không; không cho huỷ thì lễ tân phải huỷ hộ qua điện thoại."
> - **Ai trả lời**: `OWNER` (nghiệp vụ, quy tắc, tiền, quyền) → form mục A · `DEV` (stack, hosting, git, hạ tầng) → form mục B. Cùng 1 file, không hỏi ngay.
> - **Mức**: `CAO` (sai thì làm lại nhiều) / `THẤP`.
> - **Trạng thái**: `MỞ` · `CHỜ OWNER` / `CHỜ DEV` (đã gửi form) · `ĐÃ TRẢ LỜI` · `GIẢ ĐỊNH` (chỉ mức THẤP).
> - **Nhóm** (bắt buộc với OWNER): vị trí trong hành trình, form xếp theo số đầu: `1. Tổng quan`, `2. Vai trò & quyền`, `3. F-1 Đặt lịch`... Câu trong luồng ghi theo thứ tự bước. Mỗi luồng F-n có ít nhất 1 câu (câu xác nhận luồng).
> - **Màn**: `S-n` có mockup (bắt buộc khi Nhóm có F-n). Form in tên màn + file mockup.
> Gap-check: câu `CAO` chưa `ĐÃ TRẢ LỜI` thì không qua cổng. Form: `.claude/agent-team/owner-form.py build`, nhập lại: `owner-form.py import <file>`.

| Q | Câu hỏi | Đề xuất của team | Vì sao | Mức | Ai trả lời | Trạng thái | Trả lời | Nhóm | Màn |
|---|---|---|---|---|---|---|---|---|---|
