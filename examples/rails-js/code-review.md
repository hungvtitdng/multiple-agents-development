> **Ví dụ cho dự án Rails + JS/TS**, không thuộc plugin. Dùng làm nội dung nháp khi điền file KB tương ứng của dự án (xem `examples/rails-js/README.md`).


# Review diff

## Thứ tự (dừng sớm ở lỗi nặng, không sa vào style)
1. `git diff --stat <nhánh gốc>...HEAD` mỗi repo: file nào đổi, có file ngoài phạm vi task không.
2. **Đúng yêu cầu**: mỗi AC có code tương ứng chưa.
3. **Sai logic / mất dữ liệu**: điều kiện rẽ nhánh, nil/empty, transaction, xử lý lỗi bị nuốt.
4. **Quyền**: action mới có kiểm quyền và scope theo user/tenant như action cũ không.
5. **Hiệu năng**: N+1, thiếu pagination, query trong vòng lặp, thiếu index cho cột lọc mới.
6. **Bảo trì**: lặp code, abstraction thừa, sửa code cũ không cần, đúng `docs/engineering/`.
7. **Test**: có test cho logic mới, test fail được nếu bỏ code.
8. **KB khớp code**, commit message một dòng `[role] task-id: mô tả`.

## Grep gợi ý (trên file trong diff)
| Tìm | Nghi vấn |
|---|---|
| `.each do` / `.map` có gọi association bên trong (`x.user.name`) | N+1 → cần `includes`/`preload` |
| `.all` / `where(` trả JSON list không `page`/`limit`/`per` | Thiếu pagination |
| `.count` trong vòng lặp, `.find` trong vòng lặp | N+1 |
| Cột mới dùng trong `where`/`order` | Có index không |
| `rescue nil`, `rescue => e` rỗng | Nuốt lỗi |
| `TODO`, `binding.pry`, `byebug`, `console.log`, `debugger` | Sót debug |
| `useEffect` không cleanup, fetch không xử lý lỗi/loading | FE thiếu state lỗi/rỗng |

## Bài học cũ
Đối chiếu diff với các bài `Active` trong mục "Bài học" của CONTEXT.md và `docs/LESSONS.md`. Vi phạm "Cách tránh" = **High**, ghi "LẶP LẠI bài học <task>".

## Viết issue
`[Mức] file:dòng | vấn đề | tác động | đề xuất sửa (cụ thể)`
- **Critical**: sai dữ liệu/tiền, mất dữ liệu, N+1 trên list chính, lỗ hổng quyền.
- **High**: thiếu pagination list, thiếu test cho logic chính, KB không khớp, lặp lỗi cũ, ngoài phạm vi đáng kể.
- **Medium**: vi phạm quy chuẩn ảnh hưởng bảo trì, xử lý lỗi chưa đủ.
- **Low**: đặt tên, comment, style nhỏ.
Gộp issue giống nhau thành 1 dòng liệt kê nhiều vị trí. Không ghi lời khen dài.

## Review lại
Chỉ xem lại issue mình đã báo, trên phần diff mới (`git diff <commit đã review>..HEAD`). Không mở issue mới ở phần không đổi, trừ Critical.
