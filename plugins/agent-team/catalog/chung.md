# Mặc định cho mọi app

| Mục | Vì sao hay thiếu | Câu hỏi tình huống | Lựa chọn |
|---|---|---|---|
| Đăng nhập | Owner coi là hiển nhiên, không nói cách nào | Người dùng đăng nhập bằng gì? | Email + mật khẩu · Google/SSO · Số điện thoại + OTP · Không cần đăng nhập |
| Quên / đổi mật khẩu | Chỉ nghĩ tới đăng nhập thành công | Người dùng quên mật khẩu thì sao? | Gửi link đặt lại qua email · Admin đặt lại · Không hỗ trợ |
| Đăng ký tài khoản | Không rõ ai tạo tài khoản | Ai tạo tài khoản cho người dùng? | Tự đăng ký · Admin tạo và mời · Cả hai |
| Phân quyền theo vai trò | Chỉ nghĩ tới 1 loại người dùng | Có người chỉ được xem mà không được sửa không? | Có, theo vai trò · Mọi người như nhau |
| Khoá / vô hiệu tài khoản | Quên người nghỉ việc, vi phạm | Nhân viên nghỉ việc thì tài khoản sao? | Khoá, giữ dữ liệu · Xoá hẳn · Chuyển dữ liệu cho người khác |
| Hồ sơ cá nhân | Hiển nhiên nên không nói | Người dùng tự sửa thông tin nào? | Tên, ảnh, mật khẩu · Chỉ mật khẩu · Không sửa |
| Xoá dữ liệu | Không nghĩ tới xoá nhầm | Xoá nhầm 1 bản ghi thì sao? | Xoá mềm, khôi phục được · Xoá hẳn có hỏi xác nhận · Không cho xoá |
| Lịch sử thay đổi | Chỉ cần khi có tranh chấp | Cần biết ai sửa gì, lúc nào không? | Có, mọi dữ liệu quan trọng · Chỉ vài loại · Không |
| Tìm kiếm, lọc, phân trang | Lúc đầu dữ liệu ít | Danh sách có 5.000 dòng thì tìm thế nào? | Tìm + lọc + phân trang · Chỉ phân trang |
| Thông báo | Nghĩ người dùng tự vào xem | Có việc mới thì báo người liên quan bằng gì? | Trong app · Email · Push điện thoại · Không |
| Xuất / nhập dữ liệu | Quên dữ liệu cũ đang nằm ở Excel | Dữ liệu cũ đang ở đâu, cần đưa vào không? | Nhập từ Excel + xuất Excel · Chỉ xuất · Không |
| Báo cáo / thống kê | Owner nghĩ tới sau khi dùng | Cuối tháng muốn xem số liệu gì? | Màn thống kê cơ bản · Xuất Excel để tự làm · Không |
| Trang quản trị | Quên người vận hành | Ai quản lý danh mục, cấu hình, người dùng? | Có trang admin · Sửa trực tiếp DB (không đề xuất) |
| Trạng thái rỗng / lỗi / đang tải | Mockup thường chỉ vẽ lúc có dữ liệu | Lần đầu chưa có dữ liệu, màn hình hiện gì? | Hướng dẫn + nút tạo mới · Chỉ ghi "Chưa có dữ liệu" |
| Bấm 2 lần / gửi trùng | Không ai nghĩ tới | Mạng chậm, người dùng bấm Lưu 2 lần thì sao? | Chặn trùng, chỉ tạo 1 · Cho phép |
| Hai người sửa cùng lúc | Hiếm nên bị quên | Hai người cùng sửa 1 bản ghi thì sao? | Người sau được báo dữ liệu đã đổi · Người sau ghi đè |
| Đa ngôn ngữ | Nghĩ chỉ có 1 thị trường | Có người dùng nước ngoài không? | Chỉ tiếng Việt · Việt + Anh |
| Responsive / mobile | Chỉ nghĩ dùng trên máy tính | Nhân viên / khách mở app trên điện thoại thì sao? | Co giãn đủ điện thoại, tablet, máy tính (375 / 768 / 1280px) · Chỉ máy tính · App mobile riêng |
| Sao lưu, khôi phục | Chỉ nghĩ tới khi mất dữ liệu | Mất dữ liệu thì chấp nhận mất tối đa bao lâu? | Sao lưu hằng ngày · Hằng giờ · Không cần |
| Dữ liệu cá nhân nhạy cảm | Không biết luật bảo vệ dữ liệu | App có lưu CCCD, lương, sức khoẻ, số tài khoản không? | Có, cần mã hoá + giới hạn người xem · Không |
| Nhật ký hệ thống | Chỉ cần khi có sự cố | Lỗi xảy ra thì ai biết, xem ở đâu? | Ghi log + báo admin · Chỉ ghi log |
