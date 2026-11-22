---
name: wireframe
description: Vẽ wireframe ĐEN TRẮNG cho màn hình của task - đơn giản nhưng đủ mọi chức năng và trạng thái (có dữ liệu, rỗng, đang tải, lỗi, không có quyền) - 1 file HTML mỗi màn dùng chung _wf.css / _wf.js, bên trái là trang app có header / footer, bên phải là bảng hướng dẫn xem (vai trò, trường hợp, luồng, ghi chú), không lộ mã nội bộ, các màn link với nhau bấm thử được, có index.html theo luồng. Dùng khi ui-designer làm mockup trong debate để team và client thống nhất luồng, chức năng.
---

# Wireframe đen trắng

Mục tiêu: thống nhất **chức năng và luồng**, không phải giao diện đẹp. Màu, font, component thật do FE lấy từ dự án khi code.

## Quy tắc
1. **Một màn = một file** `docs/agent-tasks/<task-id>/design/mockup-<tên-màn>.html` (App / Module: `docs/product/.../design/`), **link tới `_wf.css` + `_wf.js` dùng chung** cùng thư mục (mục "File dùng chung"), không ảnh, không font, không thư viện ngoài. `<title>` là tên màn (tiếng Việt).
2. **Chỉ đen, trắng, xám**: `#000`, `#fff`, `#666`, `#999`, `#ddd`, `#f2f2f2`. Không màu khác, không icon màu. Ảnh/biểu đồ = khung xám có chữ mô tả.
3. **Màn chia 2 bên** (client xem như app thật, không lẫn ghi chú vào màn):
   ```
   ┌──────── TRANG CỦA APP (main.page) ────────┐ ┌─ HƯỚNG DẪN XEM (aside.guide) ─┐
   │ header: logo · menu · tài khoản            │ │ Màn: tên + 1 câu mô tả         │
   │ nội dung màn (theo trường hợp đang chọn)   │ │ Xem với vai trò: [Khách][...]  │
   │ footer: © đơn vị · liên hệ · ...           │ │ Trường hợp: [Có dữ liệu][Rỗng] │
   └────────────────────────────────────────────┘ │ Đi thử theo luồng ▾ bước x/n   │
                                                   │ Ghi chú màn này: 1. 2. 3.      │
                                                   │ Mục lục · Hiện mã (cho team)   │
                                                   └────────────────────────────────┘
   ```
   - **Trang của app** chỉ chứa những gì người dùng thật thấy, **có header và footer đầy đủ** như app hoàn chỉnh (logo / tên app, menu theo vai trò, tài khoản hoặc Đăng nhập / Đăng ký; footer: bản quyền, liên hệ...).
   - **Mọi thứ để hiểu mockup nằm ở bảng bên phải**, tiêu đề "HƯỚNG DẪN XEM MOCKUP (không phải phần của app)": chọn vai trò, chọn trường hợp, đi theo luồng, ghi chú. Màn hẹp (< 900px) bảng xuống dưới trang. `gap-check` báo thiếu khi mockup không có `aside.guide`.
4. **Đủ chức năng, không lộ mã:** mọi nút, ô nhập, link, bảng, thông báo mà yêu cầu cần. **Không in mã nội bộ** (R-n, AC-n, BR-n, Q-n, P-...) lên trang hay ghi chú: client không hiểu. Gắn mã vào thuộc tính `data-r="R-1"` để team đối chiếu (ô "Hiện mã (cho team)" ở bảng phải bật lên khi cần). `gap-check` báo thiếu khi chữ hiện trên mockup còn mã.
5. **Bấm được như app thật (prototype):** client phải bấm đi hết luồng, không phải đoán.
   - Nút / link sang màn khác: `<a class="btn" href="mockup-<màn>.html">`. Kèm trường hợp đích: `href="mockup-<màn>.html#empty"`.
   - Nút cho kết quả ngay trên màn (lưu lỗi, xoá xong): `href="#error"`, `href="#empty"`... mở đúng trường hợp.
   - Nút dẫn tới màn chưa vẽ / ngoài phạm vi: `<span class="btn off" title="chưa có màn">`.
   - **Đi thử theo luồng** (bảng phải): ô chọn luồng màn này thuộc về ("1 ngày của Cán bộ"...), "Bước x/n ← Trước | Sau →" theo `flows.md` / `workflow.md`. Luồng + vai trò đang chọn đi theo link (`?f=<luồng>&vt=<vai trò>`), sang màn sau vẫn giữ.
   - **`index.html`** cùng thư mục: tên app / task, mỗi luồng ("1 ngày của <vai trò>", F-n) là danh sách link theo thứ tự bước (link kèm `?f=<luồng>`), cuối là danh sách mọi màn. App / Module bắt buộc (`gap-check` kiểm); task từ 2 màn trở lên cũng làm.
   - `gap-check` báo thiếu khi link trỏ tới file không có hoặc `index.html` thiếu màn.
6. **Đủ trường hợp** (chọn ở bảng phải, tên dễ hiểu với client): `Có dữ liệu` · `Rỗng` (ghi rõ nghĩa, vd "Chưa có ai") · `Đang tải` · `Lỗi` · `Không có quyền` · `Điện thoại` (+ trường hợp riêng, vd `Đã giao`). Không áp dụng thì ghi rõ "Không áp dụng vì …".
   - Mỗi trường hợp là 1 `<section class="state">` có `id` cố định để link tới: `normal`, `empty`, `loading`, `error`, `denied`, `mobile` (+ `id` riêng không dấu); nút chọn có `data-s="<id>"`.
   - Phần chỉ một vai trò thấy: `data-role="can-bo truong-phong"` (mã vai trò không dấu); bảng phải có nút "Xem với vai trò". Màn giống nhau với mọi vai trò thì bỏ mục này.
   - **Ghi chú màn này** (bảng phải, danh sách đánh số): hành vi bấm / hiện gì, quy tắc hiển thị, khác biệt trên điện thoại / máy tính. Lời thường, tiếng Việt (từ tiếng Anh thông dụng giữ nguyên), không tên API, không mã kỹ thuật. Chỗ vẽ theo đề xuất chưa được client chốt: ghi "Đang vẽ theo đề xuất, chờ anh/chị xác nhận trong form" + `data-q="Q-n"`.
7. Dữ liệu mẫu giống thật (tên, số tiền, ngày) để client hình dung, không dùng "lorem ipsum".
8. Bố cục bám màn hình hiện có của dự án nếu sửa màn cũ (Scout đã ghi file màn trong CONTEXT.md): giữ vị trí menu, header, vùng nội dung.
9. **Responsive** (config `VIEWPORTS` có chiều rộng < 768, hoặc `docs/product/intake.md` ghi `Responsive: CÓ`): **mọi màn bắt buộc có trường hợp `Điện thoại`** (`data-s=\"mobile\"`, khung 375px), vẽ đúng cách màn co lại: menu → nút ☰, bảng → thẻ hoặc cuộn trong khung, nút chính dễ bấm (≥ 44px), không cuộn ngang. `gap-check.py` báo thiếu nếu không có. Không responsive: chỉ thêm khi màn mobile khác desktop.

## File dùng chung (viết 1 lần, mọi màn link tới, không chép vào từng màn)
Cùng thư mục `design/`: `_wf.css` (khung 2 bên, nút, trường hợp, bảng hướng dẫn) và `_wf.js` (chọn trường hợp, vai trò, luồng, hiện mã). ui-designer tạo **1 lần** bằng cách chép nguyên 2 khối dưới; sửa thì sửa ở đây, không chép lại vào màn. Style riêng của 1 màn (ít dòng) được để `<style>` nhỏ trong màn đó. `board.py report` tự chèn 2 file này khi nhúng mockup vào REPORT.html.

`_wf.css`
```css
/* _wf.css - dùng chung cho mọi mockup: khung 2 bên (trang app | hướng dẫn xem), đen trắng */
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;color:#000;background:#f2f2f2}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:16px;padding:16px;align-items:start}
@media (max-width:900px){.wrap{grid-template-columns:1fr}}
/* ---- trang của app (client xem như app thật) ---- */
.page{background:#fff;border:1px solid #999;min-height:640px;display:flex;flex-direction:column}
.page>header{display:flex;gap:16px;align-items:center;padding:10px 16px;border-bottom:2px solid #000}
.page>header .logo{font-weight:700;margin-right:auto}.page>header a{color:#000}
.page>footer{margin-top:auto;padding:10px 16px;border-top:1px solid #999;font-size:12px;color:#666;display:flex;gap:16px;flex-wrap:wrap}
.state{display:none;padding:16px}.state.on{display:block}
.box{border:1px solid #000;padding:12px;margin:8px 0}
.btn{border:1px solid #000;padding:6px 12px;display:inline-block;background:#fff;color:#000;text-decoration:none;cursor:pointer}
.btn.primary{background:#000;color:#fff}.btn.off{border-style:dashed;color:#999;cursor:not-allowed}
.ph{background:#f2f2f2;border:1px dashed #999;color:#666;padding:20px;text-align:center}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #999;padding:6px;text-align:left}
.mobile{width:375px;max-width:100%;margin:0 auto;border:2px solid #000;min-height:600px}
/* mã truy vết (R-n, AC-n, Q-n): ẩn với client, team bật "Hiện mã" để đối chiếu */
body.codes [data-r]::after{content:" " attr(data-r);font-size:10px;border:1px solid #999;color:#666;padding:0 3px;margin-left:4px}
/* ---- bảng hướng dẫn xem (không phải của app) ---- */
.guide{background:#fff;border:2px dashed #666;padding:12px;font-size:13px;position:sticky;top:16px}
.guide h2{font-size:12px;letter-spacing:.05em;color:#666;margin:0 0 8px}
.guide h3{font-size:13px;margin:12px 0 4px}.guide p{margin:2px 0;color:#666}
.guide button,.guide select{font:inherit;font-size:12px;margin:2px;border:1px solid #999;background:#fff;cursor:pointer;padding:2px 6px}
.guide button.on{background:#000;color:#fff;border-color:#000}.guide a{color:#000}
.guide ol{margin:4px 0;padding-left:18px}.guide li{margin:3px 0}
```

`_wf.js` (màn không có vai trò / luồng thì bỏ mục đó trong bảng hướng dẫn, script tự bỏ qua)
```js
/* _wf.js - dùng chung cho mọi mockup: chọn trường hợp (#hash), vai trò (?vt=), luồng (?f=), hiện mã cho team */
(function(){
var q=new URLSearchParams(location.search),f=document.getElementById('f'),B=document.body;
function go(href){var p=new URLSearchParams();if(f)p.set('f',f.value);if(B.dataset.vt)p.set('vt',B.dataset.vt);var s=p.toString();return s?href+'?'+s:href;}
function links(){document.querySelectorAll('.page a[href]').forEach(function(a){var h=a.getAttribute('href');
if(/\.html(\?|$)/.test(h))a.href=go(h.split('?')[0]);});}
function state(){var id=location.hash.slice(1)||'normal';if(!document.getElementById(id))id='normal';
document.querySelectorAll('.state').forEach(function(x){x.classList.toggle('on',x.id===id)});
document.querySelectorAll('#st button').forEach(function(b){b.classList.toggle('on',b.dataset.s===id)});}
function flow(){if(!f)return;var o=f.options[f.selectedIndex],st=document.getElementById('step');if(st)st.textContent=o.dataset.step||'';
[['prev','data-prev'],['next','data-next']].forEach(function(x){var a=document.getElementById(x[0]),h=o.getAttribute(x[1]);if(!a)return;
if(h){a.href=go(h);a.style.color='';}else{a.removeAttribute('href');a.style.color='#999';}});}
function role(v){if(v)B.dataset.vt=v;document.querySelectorAll('[data-role]').forEach(function(e){e.style.display=e.dataset.role.split(' ').indexOf(v)>=0?'':'none'});
document.querySelectorAll('#vt button').forEach(function(b){b.classList.toggle('on',b.dataset.vt===v)});links();flow();}
if(f){if(q.get('f'))f.value=q.get('f');f.onchange=function(){links();flow();};}
document.querySelectorAll('#st button').forEach(function(b){b.onclick=function(){location.hash=b.dataset.s;};});
document.querySelectorAll('#vt button').forEach(function(b){b.onclick=function(){role(b.dataset.vt);};});
var c=document.getElementById('codes');if(c)c.onchange=function(){B.classList.toggle('codes',this.checked);};
window.addEventListener('hashchange',state);state();
var v0=q.get('vt')||((document.querySelector('#vt button')||{dataset:{}}).dataset.vt);role(v0);
})();
```

## Khung mẫu (1 màn)
Màn chỉ chứa: header, các trường hợp, footer của app + bảng hướng dẫn (mô tả, vai trò, trường hợp, luồng, ghi chú). Không chép CSS / JS.
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trang chủ</title>
<link rel="stylesheet" href="_wf.css"></head><body>
<div class="wrap">
<main class="page">
  <header><span class="logo">vtb506</span><a href="mockup-trang-chu.html">Trang chủ</a>
    <span data-role="khach"><a class="btn" href="mockup-dang-nhap.html">Đăng nhập</a> <a class="btn primary" href="mockup-dang-ky.html">Đăng ký</a></span>
    <span data-role="can-bo truong-phong">Nguyễn Văn A ▾</span></header>

  <section class="state on" id="normal">
    <h1 data-r="R-1">Cây cà phê vtb506</h1>
    <label>Năm <select data-r="R-60"><option>2027</option></select></label>
    <div class="box"><div class="ph">Hình cây: mỗi quả là 1 tài khoản đang hoạt động</div>
      <p data-r="R-1"><b>113 quả</b> = số tài khoản đang hoạt động</p></div>
    <a class="btn primary" href="mockup-cay-ca-nhan.html" data-role="can-bo">Xem cây của tôi</a>
    <a class="btn" href="#error">Tải lại (mất mạng)</a>
    <span class="btn off" title="chưa có màn">Chia sẻ</span>
  </section>
  <section class="state" id="empty"><div class="ph">Năm này chưa có ai tham gia. Cây sẽ có quả khi cán bộ tạo mục tiêu đầu tiên.</div></section>
  <section class="state" id="loading"><div class="ph">Đang tải cây…</div></section>
  <section class="state" id="error"><div class="box">Không tải được cây. <a class="btn" href="#normal">Thử lại</a></div></section>
  <section class="state" id="denied"><div class="box">Không áp dụng: trang chủ ai cũng xem được.</div></section>
  <section class="state" id="mobile"><div class="mobile">… trang ở 375px: menu ☰, cây co theo chiều rộng, nút ≥ 44px …</div></section>

  <footer><span>© 2027 vtb506</span><span>Liên hệ: Phòng Tổng hợp</span><span class="btn off" title="chưa có màn">Hướng dẫn sử dụng</span></footer>
</main>

<aside class="guide">
  <h2>ⓘ HƯỚNG DẪN XEM MOCKUP (không phải phần của app)</h2>
  <h3>Màn: Trang chủ</h3>
  <p>Trang đầu tiên khi mở app, ai cũng xem được.</p>

  <h3>Xem với vai trò</h3>
  <div id="vt"><button data-vt="khach">Khách</button><button data-vt="can-bo">Cán bộ</button><button data-vt="truong-phong">Trưởng phòng</button></div>

  <h3>Trường hợp</h3>
  <div id="st"><button data-s="normal">Có dữ liệu</button><button data-s="empty">Chưa có ai</button><button data-s="loading">Đang tải</button>
  <button data-s="error">Lỗi</button><button data-s="denied">Không có quyền</button><button data-s="mobile">Điện thoại</button></div>

  <h3>Đi thử theo luồng</h3>
  <p>Chọn 1 luồng rồi bấm Sau để đi tiếp như người dùng thật.</p>
  <select id="f"><option value="cb" data-step="1/6" data-prev="" data-next="mockup-dang-nhap.html">1 ngày của Cán bộ</option>
    <option value="tp" data-step="1/7" data-prev="" data-next="mockup-dang-nhap.html">1 ngày của Trưởng phòng</option></select>
  <p>Bước <b id="step"></b> &nbsp; <a id="prev">← Trước</a> | <a id="next">Sau →</a></p>

  <h3>Ghi chú màn này</h3>
  <ol>
    <li data-r="R-1,R-44">Quả không hiện tên, mã, phòng; bấm vào không có phản hồi. Trang không có thông tin nhận ra là ai.</li>
    <li data-r="R-44">Thứ tự quả đổi mỗi ngày, không theo ngày tạo, phòng hay tên.</li>
    <li data-r="R-1">Khách chỉ mở được Trang chủ, Đăng ký, Đăng nhập. Trang khác chuyển về Đăng nhập.</li>
    <li>Máy tính bảng: cây co theo chiều rộng. Máy tính: cây giữa trang, chú giải bên dưới.</li>
  </ol>
  <p><a href="index.html">Mục lục mọi màn</a> · <label><input type="checkbox" id="codes"> Hiện mã (cho team)</label></p>
</aside>
</div>
<script src="_wf.js"></script>
</body></html>
```

## Khung mẫu `index.html`
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Salon Tóc Mây - bản mẫu</title>
<style>body{font:14px/1.6 system-ui,sans-serif;max-width:720px;margin:24px auto;color:#000}a{color:#000}h2{border-bottom:1px solid #999}</style></head><body>
<h1>Salon Tóc Mây - bản mẫu bấm thử</h1>
<p>Bấm vào bước đầu của một luồng rồi bấm các nút trên màn như dùng app thật. Bảng viền đứt bên phải mỗi màn là hướng dẫn xem (vai trò, trường hợp, ghi chú), không phải phần của app.</p>
<h2>1 ngày của Khách</h2>
<ol><li><a href="mockup-chon-dich-vu.html?f=khach">Chọn dịch vụ</a></li><li><a href="mockup-dat-lich.html?f=khach">Chọn giờ, đặt lịch</a></li>
<li><a href="mockup-xac-nhan.html?f=khach">Xác nhận</a></li><li><a href="mockup-lich-cua-toi.html?f=khach">Xem / huỷ lịch</a></li></ol>
<h2>Mọi màn</h2>
<ul><li><a href="mockup-dat-lich.html">Đặt lịch</a> (<a href="mockup-dat-lich.html#empty">rỗng</a>, <a href="mockup-dat-lich.html#error">lỗi</a>)</li></ul>
</body></html>
```

## Trong debate
- Lượt 1: post danh sách màn + đường dẫn file mockup; mỗi màn 1-2 dòng mô tả luồng.
- Lượt WHY: hỏi vì sao vào AC/workflow khi màn hình lộ ra chỗ thiếu ("AC-2 không nói hiện gì khi đơn đã giao?"); trả lời WHY về bố cục, thao tác.
- Phương án đổi → sửa mockup và post lại. Mockup cuối phải khớp phương án đã chốt.
