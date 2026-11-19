# Catalog: mặc định theo loại app

Mục đích: bù phần owner **không nghĩ tới**. BA chép mục vào `docs/product/defaults.md`, owner chỉ chọn GIỮ / BỎ / KHÁC.

| File | Dùng khi |
|---|---|
| `chung.md` | Mọi app (luôn nạp) |
| `quan-ly-noi-bo.md` | CRM, nhân sự, kho, chấm công, duyệt đơn nội bộ |
| `dat-lich.md` | Spa, salon, phòng khám, sân thể thao, lịch hẹn |

## Mỗi mục có
| Cột | Ý nghĩa |
|---|---|
| Mục | Tính năng / quy tắc |
| Vì sao hay thiếu | Lý do owner hay quên |
| Câu hỏi tình huống | Hỏi bằng tình huống cụ thể, không hỏi trừu tượng |
| Lựa chọn | 2-4 lựa chọn, lựa chọn đầu là đề xuất mặc định (dùng thẳng cho AskUserQuestion) |

## Thêm loại app mới
1. Tạo `<loai-app>.md` (tên không dấu, gạch nối), đúng 4 cột trên.
2. Thêm 1 dòng vào bảng đầu file này.
3. Gặp thiếu sót thật ở dự án (GAP, bài học) thuộc loại app → thêm mục vào file catalog tương ứng, để lần sau hỏi sớm.
