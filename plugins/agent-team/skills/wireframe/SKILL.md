---
name: wireframe
description: Vẽ wireframe ĐEN TRẮNG cho màn hình của task - đơn giản nhưng đủ mọi chức năng và trạng thái (bình thường, rỗng, đang tải, lỗi, không có quyền) - thành 1 file HTML tự chứa mỗi màn. Dùng khi ui-designer làm mockup trong debate để team và client thống nhất luồng, chức năng.
---

# Wireframe đen trắng

Mục tiêu: thống nhất **chức năng và luồng**, không phải giao diện đẹp. Màu, font, component thật do FE lấy từ dự án khi code.

## Quy tắc
1. **Một màn = một file** `docs/agent-tasks/<task-id>/design/mockup-<tên-màn>.html`, tự chứa (không ảnh, không font, không thư viện ngoài). `<title>` là tên màn (tiếng Việt).
2. **Chỉ đen, trắng, xám**: `#000`, `#fff`, `#666`, `#999`, `#ddd`, `#f2f2f2`. Không màu khác, không icon màu. Ảnh/biểu đồ = khung xám có chữ mô tả.
3. **Đủ chức năng**: mọi nút, ô nhập, link, bảng, thông báo mà AC cần. Mỗi phần tử gắn nhãn AC nhỏ (vd `AC-2`) để đối chiếu.
4. **Đủ trạng thái**, chuyển bằng thanh tab ở đầu trang: `Bình thường` · `Rỗng` · `Đang tải` · `Lỗi` · `Không có quyền` (+ trạng thái riêng của task, vd `Đã giao`). Trạng thái không áp dụng thì ghi rõ "Không áp dụng vì …".
5. **Hành vi ghi bằng chú thích** cạnh phần tử: "Bấm → hỏi xác nhận → gọi POST /…; thành công → toast …".
6. Dữ liệu mẫu giống thật (tên, số tiền, ngày) để client hình dung, không dùng "lorem ipsum".
7. Bố cục bám màn hình hiện có của dự án nếu sửa màn cũ (Scout đã ghi file màn trong CONTEXT.md): giữ vị trí menu, header, vùng nội dung.
8. Màn có bản mobile khác desktop: thêm tab `Mobile` (khung rộng 375px).

## Khung mẫu
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Huỷ một phần đơn hàng</title>
<style>
body{margin:0;font:14px/1.5 system-ui,sans-serif;color:#000;background:#fff}
.tabs{display:flex;gap:4px;padding:8px;border-bottom:2px solid #000;position:sticky;top:0;background:#fff}
.tabs button{border:1px solid #000;background:#fff;padding:4px 10px;cursor:pointer}.tabs button.on{background:#000;color:#fff}
.state{display:none;padding:16px}.state.on{display:block}
.box{border:1px solid #000;padding:12px;margin:8px 0}.btn{border:1px solid #000;padding:6px 12px;display:inline-block;background:#fff}
.btn.primary{background:#000;color:#fff}.ph{background:#f2f2f2;border:1px dashed #999;color:#666;padding:20px;text-align:center}
.ac{font-size:11px;border:1px solid #999;color:#666;padding:0 4px;margin-left:4px}.note{font-size:12px;color:#666;border-left:3px solid #999;padding-left:8px;margin:4px 0}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #999;padding:6px;text-align:left}
</style></head><body>
<div class="tabs"><button class="on" data-s="normal">Bình thường</button><button data-s="empty">Rỗng</button>
<button data-s="loading">Đang tải</button><button data-s="error">Lỗi</button><button data-s="denied">Không có quyền</button></div>
<div class="state on" id="normal">… màn đầy đủ dữ liệu, mọi nút + chú thích hành vi + nhãn AC …</div>
<div class="state" id="empty">…</div><div class="state" id="loading">…</div>
<div class="state" id="error">…</div><div class="state" id="denied">…</div>
<script>document.querySelectorAll('.tabs button').forEach(function(b){b.onclick=function(){
document.querySelectorAll('.tabs button,.state').forEach(function(x){x.classList.remove('on')});
b.classList.add('on');document.getElementById(b.dataset.s).classList.add('on');};});</script>
</body></html>
```

## Trong debate
- Lượt 1: post danh sách màn + đường dẫn file mockup; mỗi màn 1-2 dòng mô tả luồng.
- Lượt WHY: hỏi vì sao vào AC/workflow khi màn hình lộ ra chỗ thiếu ("AC-2 không nói hiện gì khi đơn đã giao?"); trả lời WHY về bố cục, thao tác.
- Phương án đổi → sửa mockup và post lại. Mockup cuối phải khớp phương án đã chốt.
