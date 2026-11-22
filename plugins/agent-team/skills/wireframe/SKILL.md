---
name: wireframe
description: Vẽ wireframe ĐEN TRẮNG cho màn hình của task - đơn giản nhưng đủ mọi chức năng và trạng thái (có dữ liệu, rỗng, đang tải, lỗi, không có quyền) - 1 file HTML tự chứa mỗi màn, các màn link với nhau bấm thử được như app thật, có index.html theo luồng. Dùng khi ui-designer làm mockup trong debate để team và client thống nhất luồng, chức năng.
---

# Wireframe đen trắng

Mục tiêu: thống nhất **chức năng và luồng**, không phải giao diện đẹp. Màu, font, component thật do FE lấy từ dự án khi code.

## Quy tắc
1. **Một màn = một file** `docs/agent-tasks/<task-id>/design/mockup-<tên-màn>.html` (App / Module: `docs/product/.../design/`), tự chứa (không ảnh, không font, không thư viện ngoài). `<title>` là tên màn (tiếng Việt).
2. **Chỉ đen, trắng, xám**: `#000`, `#fff`, `#666`, `#999`, `#ddd`, `#f2f2f2`. Không màu khác, không icon màu. Ảnh/biểu đồ = khung xám có chữ mô tả.
3. **Đủ chức năng**: mọi nút, ô nhập, link, bảng, thông báo mà AC cần. Mỗi phần tử gắn nhãn AC nhỏ (vd `AC-2`) để đối chiếu.
4. **Bấm được như app thật (prototype):** client phải bấm đi hết luồng, không phải đoán.
   - Nút / link sang màn khác: `<a class="btn" href="mockup-<màn>.html">`. Kèm trạng thái đích: `href="mockup-<màn>.html#empty"`.
   - Nút cho kết quả ngay trên màn (lưu lỗi, xoá xong): `href="#error"`, `href="#empty"`... mở đúng trạng thái.
   - Nút dẫn tới màn chưa vẽ / ngoài phạm vi: `<span class="btn off">` + chú thích "chưa có màn".
   - **Thanh luồng** dưới header, mỗi luồng màn thuộc về 1 dòng: `Đặt lịch · bước 2/4  ← Trước | Sau →` (link màn trước / sau theo `flows.md` hoặc `workflow.md`).
   - **`index.html`** cùng thư mục: tên app / task, mỗi luồng ("1 ngày của <vai trò>", F-n) là danh sách link theo thứ tự bước, cuối là danh sách mọi màn. App / Module bắt buộc (`gap-check` kiểm); task từ 2 màn trở lên cũng làm.
   - `gap-check` báo thiếu khi link trỏ tới file không có hoặc `index.html` thiếu màn.
5. **Đủ trạng thái**: `Có dữ liệu` · `Rỗng` · `Đang tải` · `Lỗi` · `Không có quyền` (+ trạng thái riêng của task, vd `Đã giao`). Trạng thái không áp dụng thì ghi rõ "Không áp dụng vì …".
   - Chuyển trạng thái bằng **bảng nổi góc dưới phải** (`.viewer`), viền đứt, tiêu đề "XEM TRẠNG THÁI (không phải nút của màn)", có nút Ẩn. **Không** đặt nút trạng thái trong header / vùng nút thao tác của màn.
   - Mỗi trạng thái có `id` cố định để link tới: `normal`, `empty`, `loading`, `error`, `denied`, `mobile` (+ `id` riêng không dấu).
6. **Hành vi ghi bằng chú thích** cạnh phần tử: "Bấm → hỏi xác nhận → lưu; thành công → báo 'Đã lưu'". Viết bằng lời thường, không ghi API / mã kỹ thuật (client đọc).
7. Dữ liệu mẫu giống thật (tên, số tiền, ngày) để client hình dung, không dùng "lorem ipsum".
8. Bố cục bám màn hình hiện có của dự án nếu sửa màn cũ (Scout đã ghi file màn trong CONTEXT.md): giữ vị trí menu, header, vùng nội dung.
9. **Responsive** (config `VIEWPORTS` có chiều rộng < 768, hoặc `docs/product/intake.md` ghi `Responsive: CÓ`): **mọi màn bắt buộc có trạng thái `Mobile`** (`data-s="mobile"`, khung 375px), vẽ đúng cách màn co lại: menu → nút ☰, bảng → thẻ hoặc cuộn trong khung, nút chính dễ bấm (≥ 44px), không cuộn ngang. `gap-check.py` báo thiếu nếu không có. Không responsive: chỉ thêm khi màn mobile khác desktop.

## Khung mẫu (1 màn)
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Đặt lịch</title>
<style>
body{margin:0;font:14px/1.5 system-ui,sans-serif;color:#000;background:#fff}
header{display:flex;gap:16px;align-items:center;padding:8px 16px;border-bottom:2px solid #000}
.flow{font-size:12px;padding:4px 16px;background:#f2f2f2;border-bottom:1px solid #ddd}.flow a{color:#000}
.state{display:none;padding:16px}.state.on{display:block}
.box{border:1px solid #000;padding:12px;margin:8px 0}
.btn{border:1px solid #000;padding:6px 12px;display:inline-block;background:#fff;color:#000;text-decoration:none;cursor:pointer}
.btn.primary{background:#000;color:#fff}.btn.off{border-style:dashed;color:#999;cursor:not-allowed}
.ph{background:#f2f2f2;border:1px dashed #999;color:#666;padding:20px;text-align:center}
.ac{font-size:11px;border:1px solid #999;color:#666;padding:0 4px;margin-left:4px}.note{font-size:12px;color:#666;border-left:3px solid #999;padding-left:8px;margin:4px 0}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #999;padding:6px;text-align:left}
.mobile{width:375px;margin:0 auto;border:2px solid #000;min-height:600px}
.viewer{position:fixed;right:12px;bottom:12px;background:#f2f2f2;border:2px dashed #666;padding:8px;font-size:12px;max-width:300px}
.viewer b{display:block;color:#666;margin-bottom:4px}.viewer button{font-size:12px;margin:2px;border:1px solid #999;background:#fff;cursor:pointer}
.viewer button.on{background:#666;color:#fff}.viewer.min .list{display:none}
</style></head><body>
<header><b>Salon Tóc Mây</b><span>Lịch của tôi</span><span>Tài khoản</span></header>
<div class="flow">Luồng Khách đặt lịch · bước 2/4 &nbsp; <a href="mockup-chon-dich-vu.html">← Trước</a> | <a href="mockup-xac-nhan.html">Sau →</a></div>

<div class="state on" id="normal">
  … màn đầy đủ dữ liệu, nhãn AC …
  <a class="btn primary" href="mockup-xac-nhan.html">Đặt lịch</a><span class="ac">AC-1</span>
  <a class="btn" href="#error">Đặt lịch (giờ đã kín)</a>
  <span class="btn off" title="chưa có màn">Đổi thợ</span>
  <p class="note">Bấm Đặt lịch → sang màn Xác nhận. Giờ đã có người đặt → báo "Giờ này đã kín, chọn giờ khác".</p>
</div>
<div class="state" id="empty">…</div><div class="state" id="loading">…</div>
<div class="state" id="error">…</div><div class="state" id="denied">…</div>
<div class="state" id="mobile"><div class="mobile">… màn ở 375px: ☰ menu, bảng thành thẻ, nút ≥ 44px …</div></div>

<div class="viewer"><b>ⓘ XEM TRẠNG THÁI (không phải nút của màn)</b>
<div class="list"><button data-s="normal">Có dữ liệu</button><button data-s="empty">Rỗng</button>
<button data-s="loading">Đang tải</button><button data-s="error">Lỗi</button><button data-s="denied">Không có quyền</button>
<button data-s="mobile">Mobile</button> · <a href="index.html">Mục lục</a></div>
<button onclick="this.parentNode.classList.toggle('min')">Ẩn / hiện</button></div>
<script>
function show(){var id=location.hash.slice(1)||'normal';if(!document.getElementById(id))id='normal';
document.querySelectorAll('.state').forEach(function(x){x.classList.toggle('on',x.id===id)});
document.querySelectorAll('.viewer button[data-s]').forEach(function(b){b.classList.toggle('on',b.dataset.s===id)});}
document.querySelectorAll('.viewer button[data-s]').forEach(function(b){b.onclick=function(){location.hash=b.dataset.s;};});
window.addEventListener('hashchange',show);show();
</script>
</body></html>
```

## Khung mẫu `index.html`
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Salon Tóc Mây - bản mẫu</title>
<style>body{font:14px/1.6 system-ui,sans-serif;max-width:720px;margin:24px auto;color:#000}a{color:#000}h2{border-bottom:1px solid #999}</style></head><body>
<h1>Salon Tóc Mây - bản mẫu bấm thử</h1>
<p>Bấm vào bước đầu của một luồng rồi bấm các nút trên màn như dùng app thật. Bảng xám góc dưới phải chỉ để xem các trường hợp (rỗng, lỗi...), không phải nút của app.</p>
<h2>1 ngày của Khách</h2>
<ol><li><a href="mockup-chon-dich-vu.html">Chọn dịch vụ</a></li><li><a href="mockup-dat-lich.html">Chọn giờ, đặt lịch</a></li>
<li><a href="mockup-xac-nhan.html">Xác nhận</a></li><li><a href="mockup-lich-cua-toi.html">Xem / huỷ lịch</a></li></ol>
<h2>Mọi màn</h2>
<ul><li><a href="mockup-dat-lich.html">Đặt lịch</a> (<a href="mockup-dat-lich.html#empty">rỗng</a>, <a href="mockup-dat-lich.html#error">lỗi</a>)</li></ul>
</body></html>
```

## Trong debate
- Lượt 1: post danh sách màn + đường dẫn file mockup; mỗi màn 1-2 dòng mô tả luồng.
- Lượt WHY: hỏi vì sao vào AC/workflow khi màn hình lộ ra chỗ thiếu ("AC-2 không nói hiện gì khi đơn đã giao?"); trả lời WHY về bố cục, thao tác.
- Phương án đổi → sửa mockup và post lại. Mockup cuối phải khớp phương án đã chốt.
