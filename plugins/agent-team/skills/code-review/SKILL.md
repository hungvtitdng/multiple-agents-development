---
name: code-review
description: Quy trình review diff chung cho mọi stack - thứ tự đọc, nhóm lỗi cần soi, đối chiếu bài học, chấm mức và viết issue. Mẫu tìm lỗi theo framework của dự án nằm ở docs/engineering/review-checklist.md. Dùng khi code-reviewer review hoặc review lại sau khi dev sửa.
---

# Review diff

## 0. Đọc checklist riêng của dự án trước
`docs/engineering/review-checklist.md` (gồm mục "Mẫu tìm lỗi theo stack"), `docs/engineering/coding-standards.md` (chung) và `backend.md` / `frontend.md` theo phần diff.
- Chưa có mẫu cho nhóm lỗi nào → suy từ code dự án, làm theo nguyên tắc dưới, ghi **"Đề xuất bổ sung review-checklist.md"** trong kết quả (Architect cập nhật khi đóng task).

## 0b. Đọc lại KB của phần bị diff chạm tới
Từ `git diff --stat` suy ra module / endpoint / bảng / hành động bị đổi, rồi đọc **đúng các file KB đó** (không đọc cả `docs/`):
| Diff đổi | Đọc | Soi |
|---|---|---|
| Logic nghiệp vụ | `docs/modules/<module>.md`, `docs/business-rules.md` | code có trái `BR-n` nào không, thiếu rule nào |
| Trạng thái, quan hệ | `docs/domain-model.md` | chuyển trạng thái ngoài sơ đồ, quan hệ sai |
| Controller / route / policy | `docs/permission-matrix.md` | vai trò nào được làm gì, có khớp không |
| Endpoint | `docs/api/` | request, response, mã lỗi |
| Migration / model | `docs/database/` | cột, kiểu, ràng buộc, index |
Không có file KB cho phần bị đổi → issue High "thiếu KB cho <phần>". Code và KB lệch nhau: xác định bên nào đúng theo AC + phương án chốt trong TASK.md; KB sai thì ghi `KB SAI: <file>`.

## 1. Thứ tự (dừng sớm ở lỗi nặng, không sa vào style)
1. `git diff --stat --merge-base <nhánh gốc>` + `git status --short` từng repo (task chưa commit tới khi review xong; file mới `??` đọc trực tiếp): file nào đổi, có file ngoài phạm vi task không.
2. **Đúng yêu cầu**: mỗi AC có code tương ứng chưa; code không trái KB đã đọc ở mục 0b (business rule, trạng thái, quyền, API, schema).
3. **Sai logic / mất dữ liệu**: rẽ nhánh, giá trị rỗng, transaction, lỗi bị nuốt.
4. **Quyền**: hành động mới kiểm quyền và giới hạn theo chủ sở hữu/tenant như hành động cũ.
5. **Hiệu năng**: truy vấn trong vòng lặp (N+1), list không phân trang, cột lọc/sắp xếp mới thiếu index, tải dữ liệu thừa.
6. **Bảo trì**: lặp code, abstraction/option thừa, sửa code cũ không cần, đúng `coding-standards.md`. **Hàm mới trùng nghĩa** hàm đã có: đọc `docs/functions/<model>.md` của model bị chạm, so cột Ý nghĩa.
7. **Test**: logic mới có test, test fail được nếu bỏ code.
8. **KB khớp code** (kể cả chỉ mục hàm `docs/functions/`: hàm public thêm / đổi / xoá phải sửa dòng trong cùng commit), commit message một dòng `[role] task-id: mô tả`.

## 2. Nhóm lỗi hay sót (tìm bằng mẫu trong review-checklist.md của dự án)
| Nhóm | Dấu hiệu |
|---|---|
| N+1 | Vòng lặp truy cập quan hệ/gọi query bên trong |
| Thiếu phân trang | Endpoint/list trả toàn bộ bản ghi |
| Nuốt lỗi | Bắt lỗi rồi bỏ qua, trả giá trị rỗng |
| Debug sót | Câu lệnh debug, log tạm, TODO mới |
| State giao diện thiếu | Không xử lý loading / rỗng / lỗi, không dọn dẹp khi unmount |
| Cấu hình cứng | Số/chuỗi/URL viết cứng thay vì config |

## 3. Bài học cũ
Đối chiếu diff với bài `Active` trong mục "Bài học" của CONTEXT.md và `docs/LESSONS.md`. Vi phạm "Cách tránh" = **High**, ghi "LẶP LẠI bài học <task>".

## 4. Viết issue
`[Mức] file:dòng | vấn đề (dẫn mã quy tắc nếu có: BE-n / FE-n / BR-n) | tác động | đề xuất sửa cụ thể`
- **Critical**: sai dữ liệu/tiền, mất dữ liệu, N+1 trên list chính, lỗ hổng quyền, trái business rule / quyền trong KB.
- **High**: thiếu phân trang list, thiếu test cho logic chính, KB không khớp, **hàm mới trùng nghĩa hàm có sẵn**, **thiếu / sai dòng chỉ mục hàm**, lặp lỗi cũ, thay đổi ngoài phạm vi đáng kể.
- **Medium**: vi phạm quy chuẩn ảnh hưởng bảo trì, xử lý lỗi chưa đủ.
- **Low**: đặt tên, comment, style nhỏ.
Gộp issue giống nhau thành 1 dòng nhiều vị trí. Không viết lời khen dài.

## 5. Review lại
Chỉ xem lại issue mình đã báo, tại đúng `file:dòng` đã báo (lần sửa không có commit riêng). Không mở issue mới ở phần không đổi, trừ Critical.
