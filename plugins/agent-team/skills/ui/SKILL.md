---
name: ui
description: Luật design cho mockup và UI thật - giao diện đẹp, nhất quán, không "mùi AI" - theo design system của dự án; chế độ ADMIN bố cục kiểu Ant Design (sidebar, topbar, nút tài khoản, breadcrumb, thẻ số liệu, thanh lọc, bảng, header chi tiết, form trong drawer); quy trình lập token → làm màn chuẩn → tự chụp ảnh chấm. Dùng mỗi khi ui-designer vẽ mockup (cùng skill wireframe) hoặc frontend-dev dựng / sửa giao diện.
---

# UI: design đẹp, nhất quán

Đọc trước khi vẽ. Thứ tự ưu tiên: file owner đưa trong `docs/product/design-ref/` (màu, font, bố cục màn mẫu) > `design-system.md` > gợi ý dưới đây. `docs/product/ui/design-system.md` là **luật**: màu, font, cỡ, bo góc của dự án thắng mọi gợi ý dưới đây. File này chỉ quyết phần design system để trống.

Một phần ý tưởng (mục 1, 5, 6) phỏng theo skill `frontend-design` của anthropics/skills (Apache 2.0).

## 0. Chọn chế độ
| Chế độ | Khi nào | Bố cục |
|---|---|---|
| `admin` | Trang quản trị, nghiệp vụ nội bộ, nhiều bảng / form / duyệt | Mục 3 (kiểu Ant Design) |
| `app` | Trang người dùng cuối, landing, mobile-first | Mục 2 + 4 |

Ghi chế độ ở đầu `design-system.md` (`- Chế độ UI: admin`). App có cả 2 (vd trang khách + trang quản trị) → ghi chế độ cho từng nhóm màn trong `screens.md`.

## 1. Tránh "mùi AI" (dấu hiệu UI do máy làm)
Không dùng trừ khi design system yêu cầu:
1. Nền kem + chữ serif to + màu đất nung; nền gần đen + 1 màu neon.
2. Mọi thứ là thẻ bo góc giống hệt nhau, cùng 1 bóng xám, gradient trang trí.
3. Nhãn VIẾT HOA giãn chữ phía trên mọi tiêu đề; tô màu 1 từ trong tiêu đề; số thứ tự `01 / 02` khi nội dung không phải trình tự.
4. Chuỗi `A · B · C`, `→` gắn sau mọi nút / link, font monospace cho nhãn nhỏ.
5. Fade / slide cho từng khối khi tải trang, hover nảy trên mọi thẻ. Chuyển động chỉ khi trả lời thao tác (mở, đóng, xác nhận).

## 2. Nền móng (mọi chế độ)
1. **Khoảng cách** chỉ thuộc thang 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48. Trong nhóm nhỏ hơn giữa nhóm (vd 8 trong, 16-24 giữa).
2. **Chữ** tối đa 6 cỡ cho cả app (12 / 14 / 16 / 18-20 / 24 / 30), mỗi màn ≤ 3 cỡ. Phân cấp bằng độ đậm + màu (đen / xám đậm / xám nhạt) trước, cỡ sau. Số liệu `tabular-nums`.
3. **Màu theo vai trò:** 1 màu chính (nút, link, mục đang chọn), 1 màu nhấn cho CTA, 3 mức xám chữ, bộ màu trạng thái (mục 3.6). Nền trắng / xám rất nhạt chiếm phần lớn màn.
4. **Mỗi màn 1 điểm nhìn chính** và **tối đa 1 nút CTA**; nút phụ dạng viền, nút nhẹ dạng link.
5. **Mọi khối thẳng mép trái** với nhau; nội dung căn trái (không căn giữa cả trang).
6. **Đủ trạng thái** mỗi khối dữ liệu: có dữ liệu · rỗng (1 câu giải thích + 1 nút hành động) · đang tải (skeleton đúng hình) · lỗi (nói chuyện gì xảy ra + cách sửa + Thử lại) · không có quyền.
7. **Responsive:** không cuộn ngang ở 375; nút ≥ 44px trên điện thoại; bảng → thẻ hoặc cuộn trong khung; nhiều cột → 1 cột.
8. **Icon 1 bộ duy nhất, dạng nét (outline), không dùng icon tô đặc (filled)** (Ant Design Icons bản `*Outlined` cho `admin`, vd `EditOutlined`, `DeleteOutlined`, `EyeOutlined`; Lucide cho `app`), cùng độ dày nét, cỡ 16 / 20, mọi icon-only có `aria-label` + tooltip. Focus nhìn thấy được, tương phản đạt WCAG AA.

## 3. Chế độ `admin` (bố cục kiểu Ant Design)
Dự án dùng antd → dùng thẳng component antd tương ứng. Mockup HTML → component cùng tên (kebab-case) trong `components/`.

### 3.1 Khung app
```
┌──────────── topbar (cao 64-70, trắng, viền dưới) ─────────────────────────────┐
│ ☰  Logo                         [đổi đơn vị]  🔔3  Nguyễn Văn A (NA)• ▾        │
├──────────────┬────────────────────────────────────────────────────────────────┤
│ sidebar 252  │ ← Quay lại   Tổ chức / Dự án / [DA-012 | Tên dự án ▾]           │
│ (thu 80)     │ ┌ nội dung, nền #f1f3f6 (xám rất nhạt), lề 20, khối cách 16 ┐ │
│ NHÓM MENU    │ │ các panel trắng xếp dọc, full chiều rộng                   │ │
│  ▣ Mục       │ └────────────────────────────────────────────────────────────┘ │
│  ▣ Mục chọn  │                                                                │
└──────────────┴────────────────────────────────────────────────────────────────┘
```
- **Sidebar** (`admin-sidebar`): trắng, viền phải xám nhạt, rộng 252, thu gọn 80 (hover thì mở). Vùng logo cao bằng topbar. Menu **theo nhóm** (tiêu đề nhóm 12px đậm, xám, chữ hoa được phép ở đây vì là nhãn nhóm, có mũi tên thu / mở). Mục: padding 9×10, bo 8-9, chữ 13.5-14, icon 16, cách 10; hover và đang chọn: nền màu chính rất nhạt + chữ màu chính. Mục con thụt vào, viền trái mảnh.
- **Topbar** (`admin-topbar`): cố định, nút ☰ thu sidebar, logo; phải: đổi đơn vị / tổ chức (nếu có), chuông có badge số đỏ, **nút tài khoản**.
- **Nút tài khoản** (`account-menu`): tên + avatar tròn 32-38 (chữ cái đầu, màu theo seed) + chấm online + ▾, bo 8-9. Bấm mở popover rộng ~236, không mũi tên: đầu là avatar + tên + email; mục (icon 16): Hồ sơ của tôi · Thông báo · Bảo mật · ─── · **Đăng xuất** (màu đỏ, cuối cùng).
- **Breadcrumb** (`page-breadcrumb`) đầu vùng nội dung, không nằm trong topbar: nút "← Quay lại" (về cấp cha người dùng có quyền) + các cấp + cấp cuối (có thể có ▾ để đổi qua bản ghi / phân hệ cùng cấp). **Không có H1 riêng**: tiêu đề nằm trong thẻ bảng / header chi tiết. Không thêm nút Back nào khác trên trang.
- **Panel** chung: trắng, viền xám nhạt, bo 10-14, bóng rất nhẹ (`0 1px 2px rgba(16,24,40,.03)`).

### 3.2 Trang danh sách (thứ tự từ trên xuống)
1. **Thẻ số liệu** (`stat-card-grid`, tuỳ chọn): 3-4 thẻ 1 hàng (điện thoại 1 cột, tablet 2). Mỗi thẻ: nhãn 14 xám, số 30 đậm, chip icon 38×38 bo 10 góc phải trên, tô theo tone (Tổng = indigo, Chờ = blue, Đang làm = purple, Xong = green).
2. **Thanh lọc** (`filter-bar`): 1 panel, các ô `flex 1 1 160px` tự xuống dòng, cách 8; phải cùng: **Tìm** (nút chính, icon kính lúp) + **Xoá lọc** (nút viền), rộng ~96. Ô chữ tìm khi Enter; select / ngày tìm ngay khi chọn.
3. **Thẻ bảng** (`table-card`): tiêu đề 16 bên trái, bên phải là nút **Tạo mới** (+, nút chính, theo quyền) hoặc nút đổi dạng danh sách / lưới. Bảng:
   - Khung viền xám nhạt bo 11; header nền `#fafbfc`, chữ xám 12-14 (in hoa được phép ở header bảng), ô padding 12×16, hàng viền `#f4f5f6`, hover `#fafcff`; header dính khi cuộn.
   - Cột: `#` (giữa, 60) → **cột tên** (đậm `MÃ | Tên` hoặc avatar 40 bo 12 + tên đậm + dòng phụ xám, 260-300, sắp xếp được) → các cột dữ liệu (số căn giữa / phải, rỗng ghi `-`) → **Trạng thái** (tag mềm theo tone) → **Thao tác** (cột cuối, căn giữa, ẩn theo quyền): **nút chỉ có icon + tooltip**, không dùng nút chữ.
     - Nút icon 32×32 (điện thoại 44×44), nền trong suốt, bo 8, icon 16 màu chữ phụ; hover nền xám nhạt, icon màu chính; cách nhau 4.
     - Mỗi nút có tooltip (hiện khi hover / focus, nói đúng việc: "Sửa", "Xem chi tiết", "Xoá") + `aria-label` cùng chữ.
     - Thứ tự cố định: Xem → Sửa → (việc riêng) → Xoá cuối cùng. Xoá: icon thùng rác nét màu đỏ.
     - Tối đa 3 nút hiện; nhiều hơn → 2 nút hay dùng + nút `⋯` (tooltip "Thêm") mở menu có icon + chữ.
     - Bấm nút không mở hàng (chặn sự kiện bấm hàng).
     - **Xoá luôn phải xác nhận** (mọi nơi: hàng bảng, header chi tiết, menu `⋯`, xoá hàng loạt): bấm → popconfirm (hàng bảng) hoặc modal (xoá bản ghi lớn / hàng loạt) ghi rõ xoá gì + hệ quả ("Xoá dự án DA-012? Các hạng mục bên trong cũng bị xoá."), nút **Xoá** đỏ + **Huỷ**, focus mặc định ở Huỷ. Xoá xong: toast "Đã xoá …". Mockup có trường hợp hiện hộp xác nhận.
   - Danh sách mã dài: tối đa 6 tag rồi `+N` có tooltip.
   - Bấm hàng → mở trang chi tiết hoặc drawer.
   - Phân trang căn phải: "Hiển thị 1–20 / 134" (xám 12.5) + đổi số dòng / trang.

### 3.3 Trang chi tiết (1 cột, xếp dọc)
1. **Header chi tiết** (`detail-header`), 1 panel padding 16×20, 1 hàng: avatar vuông 42 bo 11 (chữ cái đầu) → tiêu đề 17 + badge trạng thái (pill) / phiên bản → khoảng trống → nút thao tác (cao 34, bo 8; Sửa = viền, Xoá = viền đỏ, Xuất = dropdown) → **tab dạng segmented** (nền xám nhạt bo 9, mục chọn nền trắng) → nút ⌄ mở **lưới thông tin** (3 cột, tablet 2, điện thoại 1; nhãn xám, giá trị đậm 500; đóng mặc định).
2. Thẻ số liệu của bản ghi (tuỳ chọn) → thanh lọc → thẻ bảng các bản ghi con.
- Không dùng 2 cột, không dùng bảng mô tả (Descriptions): thông tin bản ghi nằm trong lưới của header.

### 3.4 Form = drawer bên phải (không phải trang riêng)
- **Form ngắn** (`action-drawer`): rộng 720 (form nhiều trường 960, điện thoại full), header: chip icon 36 bo 9 (nền màu chính nhạt, icon sửa / thêm) + tiêu đề 18 đậm + dòng phụ 12.5 xám + nút đóng. Thân padding 20, lưới 2 cột cách 16 (trường dài `toàn hàng`). Chân dính đáy: trái ghi chú / trạng thái, phải **Huỷ** (viền) + **Lưu** (chính, khoá khi đang lưu).
- **Form dài** (`sectioned-drawer`): chia mục đánh số `01  THÔNG TIN CHUNG` (màu chính, 14 đậm, thu / mở được), mỗi mục 1 panel trắng viền nhạt bo 10 padding 18; chân có "2/4 mục đã đủ" + tag đỏ bo tròn cho mục còn thiếu "Tài chính 1/3".
- Nhãn trên ô, `*` đỏ cho bắt buộc, lỗi dưới ô, lỗi chung là alert đầu form.

### 3.5 Token mặc định `admin` (design system không nói thì dùng)
| Token | Giá trị |
|---|---|
| Chữ chính / phụ / mờ / thân | `#1c1e21` / `#5b6470` / `#8a929b` / `#3f454c` |
| Màu chính (nếu dự án không có màu thương hiệu) | `#1677ff`, đậm `#0958d9`, nền nhạt `#e6f4ff` |
| Nền trang / nền xám nhạt / nền header bảng | `#f1f3f6` / `#f5f6f8` / `#fafbfc` |
| Viền nhạt / viền ô nhập | `#eef0f2` / `#d9d9d9` |
| Nguy hiểm chữ / viền | `#cf1322` / `#ffccc7` |
| Bo: nút / panel / avatar | 8 / 10-14 / 11-12 |
| Nút | cao 34 (điện thoại 44) |

### 3.6 Tone trạng thái (chữ / nền / viền)
| Tone | Chữ | Nền | Viền | Dùng cho |
|---|---|---|---|---|
| grey | `#8a929b` | `#f5f5f5` | `#e0e0e0` | Nháp, tất cả, không rõ |
| blue | `#0958d9` | `#e6f4ff` | `#91caff` | Chờ xử lý, đã giao |
| indigo | `#4f46e5` | `#eef2ff` | `#c7d2fe` | Tổng |
| teal | `#08979c` | `#e6fffb` | `#87e8de` | Đang làm |
| purple | `#531dab` | `#f9f0ff` | `#d3adf7` | Đang duyệt |
| green | `#389e0d` | `#f6ffed` | `#b7eb8f` | Xong, đang hoạt động |
| amber | `#d48806` | `#fffbe6` | `#ffe58f` | Chưa giao, cảnh báo |
| red | `#cf1322` | `#fff1f0` | `#ffa39e` | Ngừng, lỗi, bị từ chối |
- **Tag mềm** bo 6 chữ 500; dạng pill bo 20 padding 5×12 chữ 12 đậm. Trạng thái luôn qua 1 bảng `trạng thái → tone`, không chọn màu từng chỗ.
- **Avatar** chữ cái đầu (2 chữ hoa), màu nền chọn ổn định theo id từ bộ `#1677ff #4f46e5 #722ed1 #16a34a #d48806 #0ea5e9 #db2777 #0891b2`, chữ trắng.

### 3.7 Bảng và thanh lọc: hành vi
- **Chọn nhiều hàng** (checkbox cột đầu) → thanh thao tác hàng loạt hiện ngay trên bảng: "Đã chọn 3 · Duyệt · Xuất · 🗑 Xoá · Bỏ chọn".
- **Cột tên + cột thao tác cố định** (trái / phải) khi bảng cuộn ngang.
- **Chữ dài** cắt `…` + tooltip hiện đủ; hàng cao đều, không xuống dòng tự do.
- **Sắp xếp mặc định** rõ (thường mới nhất trước), mũi tên sort trên header cột sắp được.
- **Giữ trang / lọc / sort** khi vào chi tiết rồi quay lại; **lưu lọc + trang + sort vào URL** (F5, gửi link vẫn giữ).
- **Điện thoại:** thanh lọc thu thành nút "Bộ lọc (2)" (số ô đang lọc) mở drawer, có Áp dụng / Xoá lọc.
- **Rỗng do lọc** khác rỗng do chưa có dữ liệu: "Không có kết quả cho bộ lọc này" + nút **Xoá lọc**.

## 4. Chế độ `app`
- Header gọn (logo trái, menu, tài khoản phải), nội dung `max-w-7xl` lề 16 / 24 / 32, footer.
- Danh sách: lưới thẻ hoặc bảng gọn; form 1 cột rộng ≤ 640, nút cuối form căn phải (điện thoại: xếp dọc, nút chính trên, rộng 100%).
- Dashboard: hàng 3-4 thẻ số (số to, nhãn nhỏ, so với kỳ trước) → 1 biểu đồ chính → danh sách "cần xử lý".
- Được 1 điểm nhấn riêng của thương hiệu (hình minh hoạ, màu nhấn ở hero), phần còn lại tiết chế.

## 4b. Hành vi chung (mọi chế độ)
**Form và phản hồi**
- **Rời form chưa lưu → hỏi** "Bỏ thay đổi chưa lưu?" (Ở lại / Bỏ thay đổi), cả khi bấm ✕, ra ngoài drawer, chuyển trang.
- **Toast** góc trên phải: thành công xanh, tự tắt 3 giây; lỗi đỏ, không tự tắt, có nút đóng.
- **Ô nhập đúng kiểu:** số có dấu chấm phân cách, tiền có `₫` (căn phải), ngày `DD/MM/YYYY` có lịch chọn, danh sách dài (> 7 mục) có ô tìm trong select.
- **Đang xử lý:** nút có spinner + "Đang lưu…", khoá để không bấm 2 lần; tải bảng / khối dùng skeleton.
- **Validate** khi rời ô và khi bấm Lưu, không báo đỏ lúc đang gõ; lỗi tại ô ghi cách sửa ("Nhập email dạng ten@congty.vn").

**Quyền và trạng thái**
- **Không có quyền → ẩn nút.** Chỉ hiện mờ + tooltip lý do khi người dùng cần biết vì sao ("Chỉ sửa được khi ở trạng thái Nháp").
- **Nút theo trạng thái bản ghi:** chỉ hiện việc làm được ở trạng thái đó (Nháp: Gửi duyệt · Chờ duyệt: Duyệt / Trả về), không hiện nút bấm vào báo lỗi.
- **Việc không hoàn tác** (khoá tài khoản, huỷ, thu hồi, xoá) luôn xác nhận như Xoá (mục 3.2).

**Hiển thị dữ liệu**
- **Ngày giờ** `24/11/2026 14:30`; trong 24 giờ hiện "5 phút trước" + tooltip ngày đủ.
- **Số / tiền** căn phải, `tabular-nums`, cùng đơn vị trong 1 cột (ghi đơn vị ở header: "Diện tích (m²)").
- **Giá trị rỗng** luôn hiện `-`, không để trống ô.
- **Người tạo / sửa:** avatar nhỏ + tên, tooltip email.

**Chung**
- **Phím tắt:** Enter lưu form (trừ ô nhiều dòng), Esc đóng drawer / modal (hỏi nếu chưa lưu).
- **Tiêu đề tab trình duyệt** theo màn: "DA-012 · Dự án · <Tên app>".
- **Trang 403 / 404 / 500** có hình nhẹ, 1 câu giải thích, nút "Về trang chủ" / "Thử lại", không để màn trắng.

## 5. Chữ trên giao diện
- Gọi tên theo cách người dùng hiểu, không theo cách hệ thống làm ("Quản lý thông báo", không phải "Cấu hình webhook").
- Nút nói đúng việc xảy ra, giữ cùng tên suốt luồng: nút "Gửi duyệt" → toast "Đã gửi duyệt".
- Lỗi: nói chuyện gì xảy ra + cách sửa, không xin lỗi, không mơ hồ. Rỗng: mời hành động ("Chưa có dự án. Tạo dự án đầu tiên").
- Câu ngắn, viết thường đầu câu, không từ thừa. Dữ liệu mẫu giống thật: tên người Việt, số `1.250.000 ₫`, ngày `24/11/2026`, có cả tên dài để thử tràn chữ.

## 6. Quy trình: lập kế hoạch → màn chuẩn → tự chấm
1. **Kế hoạch (≤ 15 dòng, ghi đầu `design-system.md` hoặc post Lead):** chế độ, 4-6 màu có tên + mã, font + vai trò, bố cục bằng ASCII cho mỗi loại khung trang, 1 điều làm app này khác app mẫu. Tự hỏi: "app tương tự nào cũng ra y vậy không?" → có thì sửa phần đó trước khi vẽ.
2. **Màn chuẩn** mỗi loại khung (danh sách, chi tiết, form, dashboard) + component chung trước; màn khác dùng lại, không tạo bản khác.
3. **Tự chấm bằng ảnh** (Playwright có sẵn, mở file `file://`): chụp mỗi màn ở mọi `VIEWPORTS` × mọi trường hợp, **xem ảnh**, sửa, chụp lại. Ảnh lưu cạnh mockup (`design/shots/<màn>-<rộng>.png`).
4. **Checklist trước khi nộp** (mỗi màn, có / không):
   - [ ] Đúng màu / font / bo góc của design system, không hex viết cứng ngoài theme
   - [ ] Khoảng cách thuộc thang, mọi khối thẳng mép
   - [ ] ≤ 1 CTA, ≤ 3 cỡ chữ, 1 điểm nhìn chính
   - [ ] Đủ 5 trạng thái, chữ lỗi / rỗng có hướng dẫn
   - [ ] 375: không cuộn ngang, nút ≥ 44
   - [ ] Không dấu hiệu nào ở mục 1
   - [ ] `admin`: đúng khung mục 3.1, trạng thái qua bảng tone, thao tác hàng theo quyền
   - [ ] Thao tác hàng là icon nét + tooltip; xoá / việc không hoàn tác có xác nhận
   - [ ] Mục 4b: rời form chưa lưu có hỏi, toast, định dạng ngày / số / rỗng `-`, nút theo quyền + trạng thái
   - [ ] Bỏ bớt 1 thứ trang trí không cần (trước khi ra khỏi nhà, bỏ 1 món phụ kiện)
