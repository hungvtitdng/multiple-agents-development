> **Ví dụ cho dự án Rails + JS/TS**, không thuộc plugin. Dùng làm nội dung nháp khi điền file KB tương ứng của dự án (xem `examples/rails-js/README.md`).


# Security review: tìm nhanh, xác nhận kỹ

Chạy grep trên **phần diff** trước (`git diff <nhánh gốc>...HEAD --name-only`), sau đó mới mở rộng ra caller. Mỗi kết quả grep chỉ là ứng viên: xác nhận theo "kỷ luật xác nhận" trong agent security (ai bị ảnh hưởng, tài nguyên nào, hậu quả gì).

## Rails
| Grep | Kiểm tra |
|---|---|
| `permit!`, `params.to_unsafe_h` | Mass assignment toàn bộ params → High |
| `.permit(` có `:role`, `:admin`, `:user_id`, `:org_id`, `:price`, `:status` | User tự nâng quyền / đổi chủ / đổi giá |
| `find(params[:id])`, `find_by(id: params` | Có scope theo current_user/tenant không (`current_user.orders.find`)? Thiếu = **IDOR** |
| `where("..#{`, `order(params`, `pluck(params`, `.joins("..#{` | SQL injection / sắp xếp theo cột tuỳ ý |
| `html_safe`, `raw(`, `<%==`, `render inline:` | XSS / template injection |
| `send(params`, `public_send(params`, `constantize`, `safe_constantize` | Gọi method/class tuỳ ý |
| `redirect_to params`, `redirect_to request.referer` | Open redirect (cần `allow_other_host: false` hoặc allowlist) |
| `skip_before_action :verify_authenticity_token`, `protect_from_forgery` bị tắt | CSRF trên endpoint dùng cookie |
| `skip_before_action :authenticate`, `skip_authorization`, thiếu `authorize`/policy ở action mới | RBAC parity: mọi action cùng controller phải check như nhau |
| `YAML.load`, `Marshal.load`, `JSON.load` trên input | Deserialization không an toàn (dùng `safe_load`) |
| `system(`, `` ` ``, `Open3`, `IO.popen`, `open(` với input | Command injection / mở URL tuỳ ý (SSRF) |
| `send_file`, `File.join(.., params`, ActiveStorage/CarrierWave | Path traversal, kiểu file, dung lượng, nơi lưu, ai tải được |
| `Rails.logger`, `logger.info` với params/user | Log lộ token, mật khẩu, PII; `filter_parameters` có đủ không |
| Job/worker mới (`perform`) | Có kiểm lại tenant/quyền trong job không (job chạy ngoài request) |
| `rescue => e` trả `e.message` ra response | Lộ thông tin nội bộ |

Công cụ (nếu project có): `bundle exec brakeman -q --no-pager`, `bundle exec bundle-audit check`. Kết quả công cụ cũng phải xác nhận lại, không chép nguyên.

## Frontend JS/TS
| Grep | Kiểm tra |
|---|---|
| `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `insertAdjacentHTML` | XSS: dữ liệu có từ user không, đã sanitize chưa |
| `localStorage`/`sessionStorage` chứa token | Lộ token qua XSS |
| `window.location =`, `href={` với dữ liệu ngoài | Open redirect, `javascript:` URL |
| Ẩn nút theo quyền ở FE | Backend có chặn tương ứng không (FE ẩn ≠ bảo mật) |
| `console.log` dữ liệu user | Lộ PII trên máy người dùng |
| `npm audit` / `yarn audit` | Gói có CVE mức cao trong dependency mới thêm |

## Duyệt solution (trước khi code)
Hỏi đúng 4 câu cho phương án đã chốt: (1) kiểm quyền ở **API và tầng data**? (2) có chỗ nào dữ liệu tenant/chủ sở hữu khác có thể lọt (query, cache key, job, export)? (3) API trả field thừa? (4) dữ liệu nhạy cảm đi vào log/queue/bên thứ ba?

## Mức độ
- **Critical**: không cần đăng nhập vẫn đọc/ghi dữ liệu người khác, RCE, SQLi, lộ secret.
- **High**: user đăng nhập truy cập dữ liệu/hành động của người/tenant khác (IDOR, thiếu authorize), mass assignment quyền, XSS lưu trữ.
- **Medium**: cần điều kiện khó, lộ thông tin hạn chế, thiếu rate limit ở endpoint nhạy cảm.
- **Low**: phòng thủ chiều sâu, cấu hình nên có.
