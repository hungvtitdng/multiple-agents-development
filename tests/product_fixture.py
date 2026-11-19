"""Bộ docs/product đủ (dùng chung cho test_gap_check, test_guard)."""
import os

GOOD = {
    "intake.md": "- Loại app: dat-lich\n- Nền tảng: web\n- Stack FE: React\n- Stack BE: Rails\n- Git remote: không\n",
    "brief.md": "## Ý tưởng gốc\napp đặt lịch cho tiệm tóc\n- B-1: khách đặt lịch online\n- B-2: chủ xem lịch\n",
    "problem.md": "- G-1: giảm gọi điện đặt lịch | Thước đo: 50% lịch qua app\n",
    "questions.md": "| Q | Câu hỏi | Mức | Trạng thái | Trả lời |\n|---|---|---|---|---|\n"
                    "| Q-1 | Huỷ trước bao lâu? | CAO | ĐÃ TRẢ LỜI | 2 giờ |\n"
                    "| Q-2 | Có nhiều chi nhánh? | THẤP | GIẢ ĐỊNH | 1 chi nhánh |\n",
    "coverage.md": "| # | Góc nhìn | Kết luận | Ghi chú / nguồn |\n|---|---|---|---|\n"
                   + "".join(f"| {i} | g{i} | RÕ | R-1 |\n" for i in range(1, 11))
                   + "| 11 | g11 | LOẠI | app nhỏ, không cần |\n| 12 | g12 | CHƯA BIẾT | Q-2 |\n",
    "defaults.md": "| D | Mục | Đề xuất mặc định | Owner chọn | Ghi chú |\n|---|---|---|---|---|\n"
                   "| D-1 | Nhắc lịch | SMS | GIỮ | |\n| D-2 | Đa ngôn ngữ | vi | BỎ | |\n",
    "requirements.md": "| R | Yêu cầu | Nguồn | Vai trò | Màn | AC |\n|---|---|---|---|---|---|\n"
                       "| R-1 | Khách đặt lịch | B-1, G-1 | Khách | S-1 | chọn giờ trống → tạo lịch |\n"
                       "| R-2 | Chủ xem lịch ngày | B-2 | Chủ | S-2 | thấy mọi lịch trong ngày |\n"
                       "| R-3 | Nhắc lịch SMS trước 1 ngày | D-1 | Hệ thống | N/A | job gửi SMS |\n",
    "flows.md": "## F-1: Khách đặt lịch\n| Bước | Ai | Hành động | Nếu lỗi / ngoại lệ |\n|---|---|---|---|\n"
                "| 1 | Khách | chọn giờ | giờ vừa bị đặt → báo chọn giờ khác |\n"
                "## F-2: Chủ xem lịch\n| Bước | Ai | Hành động | Nếu lỗi / ngoại lệ |\n|---|---|---|---|\n"
                "| 1 | Chủ | mở lịch | Không có: chỉ đọc |\n",
    "data.md": "| Dữ liệu | Tạo | Xem | Sửa | Xóa |\n|---|---|---|---|---|\n"
               "| Lịch | Khách S-1 | Chủ S-2 | Khách S-1 | KHÔNG: chỉ huỷ |\n\n"
               "| Dữ liệu | Trạng thái | Vào từ | Ra tới | Ai kích hoạt |\n|---|---|---|---|---|\n"
               "| Lịch | Đã đặt | BẮT ĐẦU | Đã huỷ, Hoàn thành | Khách |\n"
               "| Lịch | Đã huỷ | Đã đặt | KẾT THÚC | Khách |\n| Lịch | Hoàn thành | Đã đặt | KẾT THÚC | Chủ |\n",
    "screens.md": "| S | Màn | Vai trò | Flow | Mockup |\n|---|---|---|---|---|\n"
                  "| S-1 | Đặt lịch | Khách | F-1 | mockup-dat-lich.html |\n"
                  "| S-2 | Lịch ngày | Chủ | F-2 | mockup-lich-ngay.html |\n",
    "design/mockup-dat-lich.html": "<title>Đặt lịch</title>",
    "design/mockup-lich-ngay.html": "<title>Lịch ngày</title>",
    "APP.md": "- Intake: YES\n- Challenger: DONE\n- Gap-check: PASS\n- Owner duyệt: APPROVED\n",
}


def write_product(root, overrides=None, drop=()):
    """Ghi bộ GOOD (+ overrides, bỏ drop) vào <root>/docs/product."""
    for rel, text in {**GOOD, **(overrides or {})}.items():
        if rel in drop:
            continue
        p = os.path.join(root, "docs", "product", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)
