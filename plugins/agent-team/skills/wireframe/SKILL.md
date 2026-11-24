---
name: wireframe
description: Vẽ mockup DESIGN FULL (đúng màu, font, component của design system, HTML + Tailwind + Web Components dùng lại được ở mọi stack) cho màn hình của task - đủ mọi chức năng và trạng thái (có dữ liệu, rỗng, đang tải, lỗi, không có quyền) - 1 file HTML mỗi màn dùng chung _wf.css / _wf.js + components/*.js, mở bằng double-click (file://) không cần server, bên trái là trang app có header / footer, bên phải là bảng hướng dẫn xem (vai trò, trường hợp, luồng, ghi chú), không lộ mã nội bộ, các màn link với nhau bấm thử được, có index.html theo luồng. Dùng khi ui-designer làm mockup trong debate để team và client thống nhất luồng, chức năng.
---

# Mockup design full

Đọc skill `agent-team:ui` trước (luật design, chế độ `admin` / `app`, tự chấm bằng ảnh); skill này lo cấu trúc file. Mục tiêu: owner duyệt **cả chức năng, luồng lẫn giao diện** trên đúng bản sẽ nhận. FE chỉ **chuyển** mockup sang code (chép class, đổi cú pháp template), không tự thiết kế.

## Quy tắc
1. **Một màn = một file** `docs/agent-tasks/<task-id>/design/mockup-<tên-màn>.html` (App / Module: `docs/product/.../design/`), link tới file dùng chung cùng thư mục: `_wf.css` + `_wf.js` (bảng hướng dẫn, trường hợp), `assets/tailwind.js` + `assets/theme.js`, `components/*.js`, `data/*.js`. Không `fetch`, không server: client mở thư mục bằng double-click. `<title>` là tên màn (tiếng Việt).
2. **Design full theo `docs/product/ui/design-system.md`**: màu, font, cỡ chữ, khoảng cách, bo góc, bóng, component đúng như app thật, căn lề chuẩn, đủ responsive. Style bằng class Tailwind dùng token của `theme.js` (`bg-primary`, `text-muted-foreground`...), không màu viết cứng. Ảnh / biểu đồ: vẽ thật bằng SVG / HTML, hoặc ảnh trong `assets/`.
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
   - Nút / link sang màn khác: `<a href="mockup-<màn>.html" class="…">`. Kèm trường hợp đích: `href="mockup-<màn>.html#empty"`.
   - Nút cho kết quả ngay trên màn (lưu lỗi, xoá xong): `href="#error"`, `href="#empty"`... mở đúng trường hợp.
   - Nút dẫn tới màn chưa vẽ / ngoài phạm vi: `<a class="off …" title="chưa có màn">`.
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

## Component dùng lại được ở mọi stack (Blade, React, Vue, ERB, Django...)
Mỗi phần lặp lại (header, menu, bảng, form, badge, rỗng / lỗi...) là **Web Component** trong `components/<tên>.js`, render vào light DOM (`innerHTML`, không shadow DOM) để class Tailwind áp được. FE chuyển sang stack thật: bỏ vỏ `customElements.define`, giữ HTML + class, đổi cú pháp biến / `if` / vòng lặp (`<app-header active="idp">` → Blade `<x-app-header active="idp" />`, React `<AppHeader active="idp" />`).
1. **1 component = 1 file**, tên kebab-case trùng tên component trong code thật.
2. **Props chỉ là thuộc tính chữ**, tên trùng props / trường trong contract (`status="cho_duyet"`, `data-field="full_name"` trên ô nhập / cột bảng).
3. **Trong template chỉ có in biến, `if`, vòng lặp**, không logic khác.
4. **Dữ liệu mẫu tách riêng** `data/<màn hoặc model>.js` (`window.DATA = {...}`), component đọc từ đó, không viết cứng trong component.
5. **Không thư viện JS khác** (jQuery, Alpine...): chỉ Tailwind + Web Components thuần.

**Màn chuẩn trước:** 1 `ui-designer` làm `assets/theme.js` + mọi component chung + **màn chuẩn cho mỗi loại khung trang** (danh sách, form, chi tiết, dashboard nếu có), đủ trạng thái × `VIEWPORTS`. Sau đó N `ui-designer` song song làm các màn còn lại theo nhóm, **dùng lại component + bố cục của màn chuẩn**, thiếu component → báo người làm màn chuẩn thêm (không tự tạo bản khác). Mỗi màn ghi loại khung trong `screens.md`.

`assets/tailwind.js`: tải 1 lần, cùng major version với Tailwind của dự án (không có thì dùng v4), vd `curl -sL https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.1.11/dist/index.global.js -o assets/tailwind.js` (chạy offline).

`assets/theme.js` (token từ design system, FE chép sang theme / biến CSS của dự án):
```js
document.write(`<style type="text/tailwindcss">
@theme { --color-primary:#005992; --color-primary-foreground:#fff; --color-brand:#D71049;
  --color-muted-foreground:#5F6B76; --color-border:#D6E4EE; --font-sans:'Be Vietnam Pro',system-ui,sans-serif; --radius-lg:.5rem; }
</style>`)
```

`components/app-header.js`:
```js
customElements.define('app-header', class extends HTMLElement {
  connectedCallback() {
    const active = this.getAttribute('active'), u = window.DATA?.user
    this.innerHTML = `
<header class="flex h-14 items-center gap-4 border-b border-border bg-white px-4 md:px-8">
  <a href="mockup-trang-chu.html" class="mr-auto font-bold text-primary">Cây Cafe</a>
  <a href="mockup-idp-cua-toi.html" class="${active === 'idp' ? 'font-semibold text-primary' : 'text-foreground'}">IDP của tôi</a>
  ${u ? `<span data-role="can-bo truong-phong" class="text-sm">${u.name}</span>` : ''}
</header>`
  }
})
```

## File dùng chung bảng hướng dẫn (viết 1 lần, mọi màn link tới, không chép vào từng màn)
Cùng thư mục `design/`: `_wf.css` (khung 2 bên, trường hợp, bảng hướng dẫn; **không** style trang app, trang app dùng Tailwind) và `_wf.js` (chọn trường hợp, vai trò, luồng, hiện mã). ui-designer tạo **1 lần** bằng cách chép nguyên 2 khối dưới; sửa thì sửa ở đây, không chép lại vào màn. Style riêng của 1 màn (ít dòng) được để `<style>` nhỏ trong màn đó. `board.py report` tự chèn 2 file này khi nhúng mockup vào REPORT.html.

`_wf.css`
```css
/* _wf.css - dùng chung cho mọi mockup: khung 2 bên (trang app | hướng dẫn xem); trang app style bằng Tailwind */
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;color:#000;background:#f2f2f2}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:16px;padding:16px;align-items:start}
@media (max-width:900px){.wrap{grid-template-columns:1fr}}
/* ---- trang của app (client xem như app thật) ---- */
.page{background:#fff;border:1px solid #ddd;min-height:640px;display:flex;flex-direction:column}
.state{display:none}.state.on{display:block}
.off{opacity:.5;cursor:not-allowed}
.mobile{width:375px;max-width:100%;margin:0 auto;border:8px solid #222;border-radius:24px;min-height:640px;overflow:hidden}
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
Màn chỉ chứa: component header / footer, các trường hợp + bảng hướng dẫn (mô tả, vai trò, trường hợp, luồng, ghi chú). Không chép CSS / JS / component. Ví dụ dưới rút gọn: màn thật style đầy đủ bằng Tailwind theo design system.
```html
<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trang chủ</title>
<script src="assets/tailwind.js"></script><script src="assets/theme.js"></script>
<script src="data/trang-chu.js"></script><script src="components/app-header.js"></script><script src="components/app-footer.js"></script>
<script src="components/empty-state.js"></script><script src="components/error-state.js"></script>
<link rel="stylesheet" href="_wf.css"></head><body>
<div class="wrap">
<main class="page">
  <app-header active="home"></app-header>

  <section class="state on mx-auto w-full max-w-7xl p-4 md:p-8" id="normal">
    <h1 class="text-xl font-bold text-primary md:text-2xl" data-r="R-1">Cây cà phê vtb506</h1>
    <label class="mt-4 flex items-center gap-2 text-sm font-medium">Năm
      <select class="h-9 rounded-md border border-input px-3" data-field="year" data-r="R-60"><option>2027</option></select></label>
    <div class="mt-6 rounded-lg border border-border p-6">
      <svg viewBox="0 0 400 240" class="mx-auto w-full max-w-md" role="img" aria-label="Cây cà phê">…</svg>
      <p class="mt-4 text-center" data-r="R-1"><b>113 quả</b> = số tài khoản đang hoạt động</p></div>
    <div class="mt-6 flex flex-col gap-2 md:flex-row md:justify-end">
      <a class="off inline-flex h-11 items-center justify-center rounded-md border border-input px-4 text-sm md:h-9" title="chưa có màn">Chia sẻ</a>
      <a class="inline-flex h-11 items-center justify-center rounded-md bg-brand px-4 text-sm font-medium text-white md:h-9" href="mockup-cay-ca-nhan.html" data-role="can-bo">Xem cây của tôi</a></div>
  </section>
  <section class="state p-8" id="empty"><empty-state title="Năm này chưa có ai tham gia" text="Cây sẽ có quả khi cán bộ tạo mục tiêu đầu tiên."></empty-state></section>
  <section class="state p-8" id="loading"><div class="h-64 animate-pulse rounded-lg bg-muted"></div></section>
  <section class="state p-8" id="error"><error-state text="Không tải được cây." retry="#normal"></error-state></section>
  <section class="state p-8" id="denied"><p class="text-muted-foreground">Không áp dụng: trang chủ ai cũng xem được.</p></section>
  <section class="state" id="mobile"><div class="mobile"><app-header active="home"></app-header><div class="p-4">… cùng nội dung ở 375px: menu ☰, nút ≥ 44px xếp dọc …</div></div></section>

  <app-footer></app-footer>
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
