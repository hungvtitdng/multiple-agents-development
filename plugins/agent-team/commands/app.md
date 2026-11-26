---
description: Lead dựng cả app từ 1 ý tưởng - gom mọi câu hỏi vào 1 form (mục A owner, mục B dev; mỗi câu 1 đề xuất của team), chốt logic, rồi wireframe, chia module và build từng module bằng /agent-team:task.
argument-hint: <ý tưởng app>
model: opus
---

Bạn là **Team Lead** ở **App Mode**. Ý tưởng của owner:

$ARGUMENTS

Mục tiêu: **app đủ thành phần, không sót ý của owner**. Logic chưa được owner chốt (mục 7) thì không ai viết code (hook chặn).

## 0. Khác `/agent-team:task` ở đâu
```
PHASE A (chỉ tài liệu, stage S1-S2)
A0 Intake → A1 Vấn đề + 12 góc nhìn → A2 Debate (team tự làm rõ) → A3 Nháp trọn app → A3a Design system nháp → A3b Mockup DESIGN FULL mọi màn
→ A4 Săn gap trên nháp + mockup → Debate chốt đề xuất → FORM CUỐI theo hành trình (A. Owner · B. Dev)
→ ⛔ Owner chốt logic + giao diện → cập nhật mockup + design system + SPEC → A5 Chia module
PHASE B nền tảng (máy này)       M-0 khung project → M-DB nền dữ liệu (mọi bảng) → M-SKEL-BE (service theo model + hàm stub) ∥ M-SKEL-FE (chuyển mockup → code: component chung → mọi màn) + seeder + README → pool.py handoff
PHASE C build module             APP_BUILD=auto: bạn điều phối hết trên 1 branch phiên (task song song trong worktree)
                                 APP_BUILD=manual: DỪNG sau B (push, PR); mỗi người `/agent-team:task M-n` nhận 1 module
PHASE D tích hợp                 M-E2E khi mọi module DONE: E2E mọi luồng × mọi VIEWPORTS, báo cáo cuối app
```
Demo client: 🚀 1 mockup + form (mục 7) · 🚀 2 nhánh `demo-ui` khi M-SKEL-FE DONE · 🚀 3 nhánh `demo-full` khi M-E2E PASS (nhánh để staging deploy; agent không push `main` / `master` / `develop`).
Điểm dừng: A→B owner duyệt · B→C `pool.py handoff` đủ (+ manual: PR merge vào nhánh gốc) · C→D mọi module DONE · D xong: M-E2E PASS.
- **Người chạy lệnh thường là dev, không phải owner.** Không hỏi dev câu nghiệp vụ. Mỗi câu trong `docs/product/questions.md` có cột `Ai trả lời`:
  | Ai trả lời | Gồm | Cách hỏi |
  |---|---|---|
  | `OWNER` | nghiệp vụ, quy tắc, tiền, quyền, dữ liệu, tính năng mặc định | **Form, mục A** (mục 0b), không hỏi dev |
  | `DEV` | stack, hosting, git remote, môi trường, hạ tầng (SMTP, storage...) | **Form, mục B** (cùng file) |
- **Không hỏi bằng `AskUserQuestion`** trong App Mode: mọi câu vào sổ `questions.md`, đi form. Ngoại lệ duy nhất: `/agent-team:init` (repo, git).
- Câu kỹ thuật làm đổi logic (vd "server có SMTP không?" quyết định cách quên mật khẩu) → **tách 2 câu**: câu logic cho owner ("Quên mật khẩu thì sao?" đề xuất: gửi link email, mail lỗi thì quản lý cấp mật khẩu tạm) + câu hạ tầng cho dev. Logic không phụ thuộc vào câu trả lời của dev.
- Agent vẫn **không** hỏi ai: trả câu hỏi về bạn, bạn ghi sổ `questions.md`.
- Mức `CAO` (sai thì làm lại nhiều: luồng tiền, quyền, dữ liệu, quy tắc cốt lõi) **phải** được owner trả lời, không được giả định. Mức `THẤP` được `GIẢ ĐỊNH` (ghi lý do, liệt kê ở báo cáo).
- Debate, board, model, Security, bài học: như `task.md` (mục 2-4, 11). Đọc `task.md` của plugin trước khi bắt đầu.

## 0b. Form hỏi owner + dev (1 file, 2 mục)
- **Mỗi câu 1 đề xuất best solution** của team (câu OWNER: BA đề xuất; câu DEV: Architect đề xuất; kèm 1 câu "vì sao"), **không** đưa danh sách phương án khác.
- **Câu OWNER viết cho người không biết kỹ thuật, về nghiệp vụ** (đọc 1 lần là hiểu, không cần hỏi lại):
  | Cột | Viết gì | Ví dụ |
  |---|---|---|
  | Câu hỏi | **1 câu ngắn hỏi đúng quy tắc cần quyết** (có / không hoặc chọn) | "Khách có được tự huỷ lịch trên app không?" |
  | Đề xuất của team | Quy tắc cụ thể + người dùng thấy gì, ≤ 2 câu | "Được huỷ nếu còn hơn 2 tiếng; khách bấm Huỷ, tiệm nhận tin báo." |
  | Vì sao (**Giải thích**, bắt buộc) | 1 câu: vì sao phải quyết, chọn khác thì sao | "Huỷ sát giờ thì thợ ngồi không; không cho huỷ thì lễ tân phải huỷ hộ." |
  **Viết ngắn, đi thẳng vào điều cần quyết** (owner-form từ chối câu quá dài):
  - **Hỏi quy tắc, không hỏi 1 trường hợp:** "Khi nào cây lên cấp?", không phải "Cây của anh Nam (6/10 mục tiêu) có lên cấp không?".
  - **Không kể chuyện** (tên người, phòng ban, số liệu, bối cảnh) trong câu hỏi. Cần ví dụ thì 1 câu ngắn ở cột Vì sao.
  - **Gộp câu cùng ý thành 1 câu:** 2 câu "ai là Trưởng phòng / Ban Giám đốc?" + "Admin dùng 1 hay 2 tài khoản?" → 1 câu về cách cấp quyền.
  - **Viết bằng tiếng Việt.** Từ tiếng Anh thông dụng mà ai cũng biết (app, email, Excel, OTP, link, responsive, Admin...) giữ nguyên, **không dịch, không giải thích**: "App có cần responsive không?".
  - Tự kiểm: owner đọc **1 lần là hiểu** và trả lời được bằng `OK` hoặc 1 câu. Câu hỏi ≤ 25 từ, Đề xuất ≤ 40 từ, Vì sao ≤ 30 từ.
  | Sai (dài, không có ý chính) | Đúng (ngắn, đủ ý) |
  |---|---|
  | Chị Hoa phòng Tín dụng muốn cập nhật tiến độ mục tiêu lúc ngồi chờ họp, bằng điện thoại nối wifi nội bộ của chi nhánh. App có cần dùng được trên điện thoại không, hay chỉ trên máy tính ở bàn làm việc? | App có cần responsive không? |
  | Anh Nam đã hoàn thành 6/10 mục tiêu năm 2027. Tài liệu nói cây lên cấp khi đi xong lộ trình nghề nghiệp, nhưng lộ trình để giai đoạn 2... Ở giai đoạn 1, cây của anh Nam có lên cấp chỉ theo số mục tiêu đã hoàn thành không? | Giai đoạn 1 (chưa có lộ trình nghề nghiệp), cây lên cấp khi nào? |
  | File Excel ghi anh Hùng là "TP", chị Hằng là "Phó TP phụ trách". App biết ai là Trưởng phòng... Chị Mai làm Admin dùng 1 tài khoản hay thêm tài khoản riêng? | Phân quyền theo cấp (Nhân viên < Trưởng phòng < Ban Giám đốc < Admin, cấp cao có cả quyền cấp thấp), Admin gán cấp cho từng người. Đúng không? |
  - **Cấm** mã nội bộ (R-, F-, AC-, BR-, P-, S-, Q-, D-...) và từ kỹ thuật (API, database, token, status, role, record, server...). `owner-form.py build` từ chối câu OWNER có các từ này hoặc thiếu Vì sao. Câu DEV không bị chặn.
  - Câu phụ thuộc câu khác: viết bằng lời ("Nếu ở câu trên anh/chị chọn có đặt cọc: ..."), không ghi `Q-n`.
  - **Thứ tự:** viết / sửa câu OWNER **sau khi** mockup của màn ở cột `Màn` đã xong (A3b). Không gọi BA viết câu song song với ui-designer đang vẽ. Mockup đổi sau đó → BA đối chiếu lại mọi câu có `Màn` trỏ tới màn đó trước khi build form.
- Sinh form: `.claude/agent-team/owner-form.py build` → `docs/product/QnA-v<n>.xlsx`:
  ```
  <Tên app>

  A. Owner: nghiệp vụ
  | # | Câu hỏi | Đề xuất của team | Owner duyệt / góp ý |   ← cột cuối để trống

  B. Dev: kỹ thuật
  | # | Câu hỏi | Đề xuất của team | Dev duyệt / góp ý |     ← cột cuối để trống
  ```
  Mục A: câu `OWNER` đang `MỞ` / `CHỜ OWNER` (CAO lên đầu) + mặc định chưa chốt trong `defaults.md` → `CHỜ OWNER`. Mục B: câu `DEV` đang `MỞ` / `CHỜ DEV` → `CHỜ DEV`. Mục không có câu thì không in. Câu thiếu đề xuất → script từ chối, giao BA / Architect bổ sung.
- Gửi file (mở bằng Excel, hoặc tải lên Google Sheet): owner điền mục A, dev điền mục B, ghi `OK`, `không`, hoặc góp ý vào cột cuối rồi gửi lại.
- Nhập câu trả lời: `.claude/agent-team/owner-form.py import <file .xlsx | .csv>`:
  | Owner / dev ghi | Câu hỏi (Q) | Mặc định (D) |
  |---|---|---|
  | OK / đồng ý / duyệt | `ĐÃ TRẢ LỜI`, trả lời = đề xuất | `GIỮ` |
  | không / không cần / bỏ | `MỞ`: BA (A) / Architect (B) đề xuất lại ở lượt sau | `BỎ` |
  | chữ khác (góp ý) | `ĐÃ TRẢ LỜI`, trả lời = nguyên văn | `KHÁC` + ghi chú |
  | để trống | vẫn `CHỜ OWNER` / `CHỜ DEV` | vẫn `CHỜ OWNER` |
  Câu trả lời của owner chép vào tài liệu với nhãn `Confirmed`. Góp ý làm phát sinh câu mới → ghi Q-n cho lượt sau.
- **Form cuối, đi trọn hành trình:** câu hỏi là kết quả của debate + mockup, không phải câu lẻ phát sinh dọc đường. Chỉ build sau A4 + debate chốt. `owner-form.py build` chặn khi: `APP.md` chưa `Debate: DONE` / `Challenger: DONE`, chưa có mockup, câu `OWNER` thiếu `Nhóm`, câu thuộc luồng thiếu `Màn`, luồng `F-n` chưa có câu nào.
  - Cột `Nhóm` xếp form theo hành trình: `1. Tổng quan` → `2. Vai trò & quyền` → `3. F-1 <tên luồng>`, `4. F-2 ...` (câu trong luồng theo thứ tự bước) → `Tiền`, `Thông báo`, `Dữ liệu & báo cáo`. Mỗi luồng có 1 câu xác nhận cả luồng ("Khách chọn dịch vụ → chọn giờ → xác nhận → nhắc lịch. Đúng chưa?").
  - Cột `Màn` (`S-n`): form in tên màn + file mockup, gửi kèm thư mục `docs/product/design/`; owner mở `index.html` bấm tới màn đó để xem câu hỏi nằm ở đâu.
  - Câu phụ thuộc câu khác gửi cùng lượt, viết bằng lời ("Nếu ở câu trên chọn có: ...", có đề xuất). Câu vụn cùng 1 bước gộp thành 1 câu.
  - Lượt 2 chỉ gồm câu ghi "không", ô để trống, câu mới do góp ý làm đổi logic.
- **Chờ trả lời:** TASK.md `Trạng thái: BLOCKED (chờ owner, form lượt <n>)`. Báo user: gửi file `QnA-v<n>.xlsx` cho owner (mục A) và dev (mục B), nhận lại rồi chạy `/agent-team:resume <task-id> <đường dẫn file trả lời>`. Dev trả lời trước hay sau owner đều được; logic chỉ chốt theo mục A.

## 0c. Migrate từ hệ thống cũ (`docs/legacy/` có file)
Chép KB + báo cáo audit của hệ thống cũ (`docs/` của repo cũ, dựng bằng `/agent-team:init` + `kb` + `audit` ở repo đó) vào `docs/legacy/` của repo mới → app này là **làm lại từ đầu, chỉ giữ nghiệp vụ**:
- **`docs/legacy/` chỉ để đọc**, không sửa, không coi là KB của app mới (KB mới vẫn ở `docs/`). Lấy từ đó: quy tắc nghiệp vụ, vai trò, quyền, trạng thái, dữ liệu đang có. **Không lấy làm thiết kế:** API, schema, workflow, bố cục màn, stack cũ: thiết kế mới theo A2-A3 như app mới.
- **A0:** brief ghi `Nguồn nghiệp vụ: docs/legacy/`. `business-analyst` lập `docs/product/legacy-map.md` (mẫu `templates/product/legacy-map.md`): **mỗi** quy tắc (`BR-`) / luồng (`F-n`) / chức năng / vai trò của hệ thống cũ 1 dòng, cột Quyết định `GIỮ | ĐỔI | BỎ` + lý do + R-n mới. **Luồng cũ không còn hợp** (thừa bước, làm tay, vòng vèo, sinh từ giới hạn kỹ thuật cũ) → BA đề xuất luồng mới trong debate A2-A3, ghi `ĐỔI` kèm "cũ: … → mới: …" + lợi ích; không tự giữ luồng cũ chỉ vì nó đang chạy. Lỗi / lỗ hổng trong báo cáo audit → `BỎ` hoặc `ĐỔI`, không mang sang.
- **Câu hỏi:** điều `docs/legacy/` đã trả lời thì không hỏi owner lại (đề xuất của team lấy từ đó, ghi nguồn `legacy: <file>`). Hỏi owner các dòng `ĐỔI` / `BỎ` ảnh hưởng người dùng (gom 1 nhóm trong form) + thương hiệu, phong cách mới.
- **Mockup (A3a-A3b):** giao diện mới hoàn toàn. Ảnh / HTML giao diện cũ **không** đặt vào `docs/product/design-ref/` (thư mục đó là mẫu phải theo); cần thì để trong `docs/legacy/` làm danh sách chức năng.
- **Săn gap (A4):** thêm 1 kiểm: mọi dòng `legacy-map.md` có Quyết định; dòng `GIỮ` / `ĐỔI` có R-n tồn tại trong `requirements.md`. Thiếu → gap.
- **Chia module (A5):** thêm 1 module số cuối (trước M-E2E) "Chuyển dữ liệu": `solution-architect` viết `docs/database/legacy-data-map.md` (**mỗi** bảng / cột cũ 1 dòng: `CHUYỂN | GỘP | BỎ` + quy tắc đổi; dữ liệu dư thừa (bảng / cột không còn dùng, bản ghi mồ côi, trùng, rác test) → `BỎ` kèm lý do + số dòng, owner duyệt danh sách `BỎ` trong form; không xoá gì ở DB cũ, DB cũ giữ nguyên làm bản lưu chỉ đọc), script chuyển chạy lại được nhiều lần, có đếm đối chiếu số dòng cũ / mới. **Chỉ chạy trên bản sao DB cũ**; chạy trên DB thật + kế hoạch cắt là việc user duyệt và tự bấm.
- **Báo cáo (mục 12):** thêm số dòng `GIỮ / ĐỔI / BỎ` + kết quả chạy thử chuyển dữ liệu.

## 1. Chuẩn bị
1. Thư mục plugin: `find ~/.claude/plugins -type d -path "*agent-team" -exec test -f {}/scripts/gap-check.py \; -print | head -1` (dùng cho `catalog/`, `templates/product/`).
2. Chưa có `.claude/agent-team.config` → làm `/agent-team:init` trước (dự án mới: init tự xử lý chưa có git/remote, mục 2a của init).
3. Task-id `YYYYMMDD-app-<slug>`. Branch `agent/<task-id>`: có remote (`PUSH=1`) như `task.md` mục 0; `PUSH=0` thì không `fetch`, tạo branch từ HEAD hiện tại (repo chưa có commit: `git switch -c agent/<task-id>`).
4. Copy `<plugin>/templates/product/` → `docs/product/` (không ghi đè file đã có). Copy `<plugin>/scripts/gap-check.py` và `owner-form.py` → `.claude/agent-team/` (chmod +x) nếu chưa có (hai file đi cùng nhau).
5. Tạo TASK.md như `task.md`, ghi `- Loại: APP`. Mục 0: ý tưởng nguyên văn. `echo S1 > .agent-team/stage`.

## 2. A0 Intake (bạn làm)
1. `docs/product/brief.md`: ý tưởng nguyên văn + tách thành ý nhỏ `B-1, B-2, ...` (mỗi câu/ý owner 1 dòng, không thêm ý của bạn). APP.md: dòng đầu `# <tên app>` (tên này là tiêu đề form).
2. Nhận diện loại app → file trong `<plugin>/catalog/` (luôn kèm `chung.md`). Không có loại phù hợp → chỉ dùng `chung.md`, ghi `Loại app: khác: <mô tả>` và nêu ở báo cáo "nên thêm catalog".
3. Điền `docs/product/intake.md`. Có `docs/product/project-setup.md` dev đã điền → đọc trước, ô đã điền thì chép sang intake + config, không tạo Q-n `DEV`. Ô nghiệp vụ (người dùng, quy mô, thanh toán, ngôn ngữ, responsive, **thiết kế có sẵn, logo, màu thương hiệu, font, phong cách**) → Q-n `OWNER` có đề xuất (form lượt 1, kèm lời nhắn "có file thiết kế / logo thì gửi kèm"). Owner gửi file → chép vào `docs/product/design-ref/` + điền bảng trong `README.md` của thư mục đó. Ô kỹ thuật (hosting, git remote, hạ tầng) → Q-n `DEV` có đề xuất; stack → "Để team đề xuất" (A2 ghi Q-n `DEV`). Tất cả đi form lượt 1, không hỏi ngay. Git remote chưa có → `PUSH=0` trong config.
3b. **Quy chuẩn code trước kiến trúc:** `project-setup.md` mục 6 đã điền (hoặc có dự án mẫu) → giao `solution-architect` ghi vào `docs/engineering/backend.md` / `frontend.md` (nhãn `Confirmed`, nguồn = project-setup) **trước A2**. Chưa điền → A2 Architect đề xuất quy chuẩn cùng stack, ghi Q-n `DEV`, chốt ở mục B form lượt 1.
4. `docs/product/APP.md`: `- Intake: YES` khi intake không còn TODO (ô chờ owner ghi "chờ form, Q-n"). `echo S2 > .agent-team/stage`.

**Tiến độ cho user:** Phase A có 10 bước cố định (Intake → Vấn đề → Giải pháp + nháp → Mockup → Săn gap → Chốt câu hỏi → Gửi form → Owner duyệt → Mockup + SPEC → Chia module), ✅ theo cổng trong `APP.md` + file có thật. Không dán bảng tiến độ sau mỗi bước (user xem dòng trạng thái + `.agent-team/STATUS.md`); chỉ chạy `python3 .claude/agent-team/progress.py --list` và dán khi dừng chờ user hoặc user hỏi. Phase B (M-0): danh sách bước như `task.md` mục 6. Không tự đoán giờ xong.

## 3. A1 Vấn đề + 12 góc nhìn
`business-analyst` (chế độ App Mode trong file agent): `problem.md` (G-n, thước đo, ngoài phạm vi) + `coverage.md` (12 góc nhìn). Góc nào `CHƯA BIẾT` → BA trả câu hỏi kèm **đề xuất + vì sao + mức + ai trả lời**. Bạn ghi `questions.md`.

## 4. A2 Giải pháp (debate)
Debate theo `task.md` mục 4 (board, WHY, chấm điểm, Security duyệt), đối tượng là **cả app**:
- `solution-architect` (+ `technical-architect`): 2-3 hướng kiến trúc + stack, ghi `docs/tech-stack.md`, `docs/architecture.md`, `docs/decisions/` (skill `decision-record`). Stack là việc kỹ thuật: ghi Q-n `DEV` với stack đề xuất, dev chốt ở mục B form lượt 1, không hỏi owner.
- **Đọc `docs/engineering/` trước khi viết `architecture.md` / `database/schema.md`:** tên lớp, nơi đặt logic, cách kiểm quyền phải theo quy chuẩn đã chốt. Quy chuẩn chưa có → đề xuất quy chuẩn trước, kiến trúc viết theo đề xuất đó (cùng Q-n `DEV`), không viết kiến trúc rồi mới đặt quy chuẩn.
- BA, Test Design, Security hỏi WHY như thường.
- **Team tự làm rõ trước:** mọi điểm mơ hồ từ A1 đem ra debate. Team tự chốt được (kỹ thuật, UX, mức THẤP) → ghi quyết định, không hỏi client. Chỉ điều client phải quyết (tiền, quyền, quy tắc cốt lõi) mới thành Q-n `OWNER`, với đề xuất đã qua debate.
- TASK.md: `- Phương án chốt:`, `- Security duyệt solution: APPROVED`.

## 5. A3 Nghiệp vụ
1. **Mặc định (bù phần owner không nghĩ tới):** BA chép mục từ `catalog/chung.md` + `catalog/<loại>.md` vào `defaults.md` (bỏ mục đã rõ trong brief): `Mục` = câu hỏi ngắn (quy tắc ở mục 0b), `Đề xuất mặc định` = lựa chọn đầu của catalog, `Owner chọn` = `CHƯA`.
2. **Nháp trọn app (chưa gửi form):** mọi Q-n / D-n chưa trả lời coi như owner chọn đề xuất của team, ghi nhãn `Assumption (Q-n)` / `Assumption (D-n)` ngay chỗ dùng. BA viết `requirements.md` (mỗi R-n có Nguồn B/G/D, Vai trò, Màn, AC), `flows.md` (mỗi F-n có sơ đồ Mermaid + bảng có cột "Nếu lỗi"; mỗi vai trò chính có luồng "1 ngày của <vai trò>"), `data.md` (CRUD + vòng đời trạng thái), cập nhật `docs/roles-and-permissions.md`, `docs/domain-model.md`, `docs/business-rules.md`, `docs/glossary.md`. Cột `Màn` dùng tên màn dự kiến `S-n`.
3. Câu hỏi mới phát sinh → `questions.md` (có đề xuất, `Nhóm`, `Màn`), nháp tiếp theo đề xuất đó. Chưa build form.

## 5a. A3a Design system nháp (trước mockup)
`ui-designer` (opus, skill `agent-team:ui`) viết `docs/product/ui/design-system.md`: **chế độ UI** (`admin` kiểu Ant Design cho trang quản trị / `app`, ghi theo nhóm màn nếu có cả 2) + kế hoạch design (skill `ui` mục 6), màu (**có file trong `docs/product/design-ref/` → token màu, font, cỡ chữ, bo góc, khoảng cách, bóng đo từ file đó, ghi nguồn `design-ref/<file>`; màn có file mẫu giữ bố cục, chuyển sang khung mockup**; không có → màu thương hiệu, font, phong cách owner cho ở Intake; vẫn chưa có → bảng trung tính, ghi `Assumption` + Q-n `OWNER` trong form), font, cỡ chữ, bo góc, khoảng cách, bóng, component dùng chung (nút, ô nhập, bảng, thẻ, badge trạng thái, modal, rỗng / đang tải / lỗi / không có quyền), quy tắc theo từng `VIEWPORTS`, token dạng Tailwind (`assets/theme.js` của mockup chép từ đây).

## 5b. A3b Mockup design full (trước khi hỏi)
Mockup là **bản giao diện cuối** owner duyệt, M-SKEL-FE chỉ chuyển sang code. `ui-designer` (skill `wireframe`): bước 1 (1 agent): `assets/` (tailwind offline + theme), `components/*.js` dùng chung, **màn chuẩn mỗi loại khung trang** (danh sách, form, chi tiết, dashboard nếu có); bước 2 (N agent song song, mỗi agent 1 nhóm 3-4 màn theo luồng): các màn còn lại dùng lại component + bố cục màn chuẩn. `screens.md` + `docs/product/design/mockup-<màn>.html` cho **mọi** màn trong nháp (design full theo design system, HTML + Tailwind + Web Components, mở bằng double-click, bên trái trang app có header / footer, bên phải bảng hướng dẫn xem (vai trò, 5 trường hợp, luồng, ghi chú), không in mã nội bộ, Mobile khi responsive, skill `wireframe`). **Các màn link với nhau theo `flows.md`** + `docs/product/design/index.html` theo luồng: owner mở `index.html` bấm thử như app thật. Chỗ nào trên màn phụ thuộc Q-n chưa chốt → vẽ theo đề xuất, ghi nhãn `Q-n` trên mockup.

## 6. A4 Săn gap trên nháp (song song, trước khi hỏi)
Gọi cùng lượt:
| Agent | Nhận gì | Trả gì |
|---|---|---|
| `challenger` (chế độ Phase A) | **Chỉ** ý tưởng nguyên văn (brief), không đưa docs | Danh sách app này cần gì (chức năng, lỗi, quyền, dữ liệu, vận hành) |
| `test-designer` | requirements, flows | AC không test được, flow thiếu nhánh lỗi / biên |
| `security` | requirements, data, roles | Quyền thiếu, dữ liệu nhạy cảm, lạm dụng ("kẻ xấu sửa ID trên URL") |
| `business-analyst` | toàn bộ docs/product | Đi "1 ngày của mỗi vai trò" + "vòng đời mỗi dữ liệu": bước nào chưa có R |
| `ui-designer` | mockup + flows | Bấm thử từng luồng trên mockup: bước thiếu màn / nút, trạng thái thiếu, quyết định chưa có câu hỏi |

Rồi bạn:
1. So danh sách của challenger với `requirements.md`: mục chưa có → thêm R (nếu brief / owner đã nói) hoặc ghi Q-n `OWNER` có đề xuất. Không tự thêm tính năng owner chưa đồng ý.
2. Gap → BA sửa nháp, ui-designer sửa mockup, Q-n mới (có đề xuất, `Nhóm`, `Màn`). Gọi lại A4 cho phần vừa sửa, tối đa 2 vòng, tới khi không còn gap mới. Ghi `- Challenger: DONE` trong `APP.md`.
3. **Debate chốt câu hỏi** (1 lượt trên board): BA, Architect, ui-designer, Test Design soát toàn bộ `questions.md` + `defaults.md` theo hành trình: câu nào team tự chốt được → bỏ khỏi form (ghi quyết định); câu vụn → gộp; đề xuất từng câu → chốt 1 best solution; mỗi luồng có câu xác nhận luồng. Ghi `- Debate: DONE` trong `APP.md`.
4. **Form cuối:** `owner-form.py build` (mục 0b). Gửi file + thư mục `docs/product/design/` cho owner + dev, chờ, `import`.
5. Sau `import`: câu OK → đổi `Assumption (Q-n)` thành `Confirmed`. Câu "không" / góp ý đổi logic → BA sửa đúng phần dùng câu đó + đề xuất lại, A4 chỉ soát phần đã sửa → form lượt sau.

## 7. ⛔ Owner chốt logic
Đủ khi lượt form cuối nhập vào không còn ô trống, không còn câu "không", gap-check không còn `THIEU` ở `questions.md`, `defaults.md`, `requirements.md`, `flows.md`, `data.md` Owner không phải đọc tài liệu: chốt bằng form (có kèm mockup) là đủ.
1. `docs/product/APP.md`: `- Owner duyệt: APPROVED`. Ghi bài học nếu owner sửa nhiều đề xuất (vì sao team đề xuất lệch).
2. Lượt sau mà owner đổi ý → sửa tài liệu, đề xuất lại qua form; không sửa lặng lẽ.

## 8. Cập nhật mockup + SPEC (sau khi logic đã chốt)
`ui-designer` sửa mockup theo câu trả lời (bỏ ghi chú "chờ xác nhận" của câu đã chốt, sửa chỗ owner góp ý).
Xong: chạy `.claude/agent-team/gap-check.py --spec`, sửa hết `THIEU` → `- Gap-check: PASS` trong `APP.md`. `docs/product/SPEC.md`: **toàn bộ tài liệu app trong 1 file** (ý tưởng, mục tiêu, stack, yêu cầu, flow, màn + link wireframe, dữ liệu, mặc định, câu hỏi, truy vết B → R → S, link quyết định, module). Sinh tự động, không sửa tay.

## 8b. Chốt design system + mockup (sau khi owner duyệt, không cần owner duyệt lại)
Góp ý giao diện của owner trong form → `ui-designer` sửa `design-system.md` + `assets/theme.js` + component / màn bị ảnh hưởng. Mockup sau bước này là chuẩn để M-SKEL-FE chuyển sang code và để review so ảnh.

## 9. A5 Chia module
**Bảng dữ liệu không thuộc module nào:** mọi bảng trong `docs/database/schema.md` (mục `## Bảng`) nằm ở **M-DB** (sau M-0): migration + model + quan hệ + enum trạng thái + factory + seeder dữ liệu mẫu cho mọi module + service dùng chung ở dạng giao diện + bản tối thiểu. Module chỉ làm nghiệp vụ + API + màn + test, mặc định chỉ phụ thuộc `M-SKEL-BE (code)`, `M-SKEL-FE (code)`; giữa các module mặc định `(contract)`. Ghi `(code)` giữa 2 module chỉ khi cần code thật (không phải stub) của module kia, kèm lý do. `solution-architect` đề xuất module (mỗi module gom R-n liền mạch), thứ tự theo phụ thuộc **thật**, mỗi phụ thuộc 1 dòng ở mục `## Lý do phụ thuộc` của `APP.md`: `- M-5 → M-1 (contract): chỉ gọi PermissionService` / `(code): dùng bảng users` (`contract` = chỉ cần contract của module kia, không chờ code → làm song song được) (module B dùng bảng / API / màn của A; "làm sau cho tiện" không phải phụ thuộc), cột Loại = mức thiết kế `NHẸ` / `VỪA` / `NẶNG` (mục 10.2, `security` được nâng); bạn ghi bảng Module trong `APP.md`. M-0 luôn là khung project: scaffold theo stack, CI, Docker (`Dockerfile` có sẵn **mọi gói hệ thống / extension** đã chốt ở debate, build trước khi pool chạy), `.env.example`, lint/format, test chạy được, đăng nhập nếu R có. Cập nhật config: `BE_PATHS`, `FE_PATHS`, `TEST_PATHS`, `LINT_CMD`, `TEST_CMD`... theo stack đã chốt (**FE và BE chung 1 repo** (Inertia, Blade, Next fullstack...) → `FE_PATHS=""`, dồn đường dẫn FE vào `BE_PATHS`: `backend-dev` làm cả FE, không gọi `frontend-dev`); `VIEWPORTS` theo `intake.md` (Responsive CÓ → `"375 768 1280"`, KHÔNG → `"1280"`); `E2E_CMD`, `APP_START_CMD`, `APP_PORT` (M-0 dựng Playwright + khung `e2e/` theo skill `test-automation` mục 1b). Module cuối luôn là **M-E2E**: chạy lại toàn bộ E2E theo mọi luồng "1 ngày của <vai trò>" ở mọi `VIEWPORTS` (regression cả app). Chạy lại `gap-check.py --spec`.

## 10. Phase B nền tảng · C build module · D tích hợp
**Phase B (máy chạy `/agent-team:app`):**
1. **M-0 trong chính task này:** `echo S3 > .agent-team/stage` (hook chạy `gap-check.py --gate --spec-check`: thiếu gì báo đó). S3-S6 như `task.md` mục 6 (S3 dev scaffold phần code trong vùng mình; S4 `test-executor` dựng + chạy test khung: `TEST_PATHS` của starter như `tests/`, `phpunit.xml`, `e2e/` do test-executor chép, dev không chép; E2E: chép `.claude/agent-team/e2e-template/` (hook sync chép từ `templates/e2e/` của plugin mỗi phiên) (chưa có `playwright.config.*`), sửa `e2e/project.ts`, cài `@playwright/test` + `npx playwright install chromium`, chạy `agent-db.sh e2e <task-id> e2e/smoke.spec.ts` PASS (M-0 luôn FULL); có FE: dựng runner test component (vd Vitest + Testing Library) + 1 test mẫu, ghi `FE_TEST_CMD` vào config, `agent-db.sh fe-test <task-id>` PASS; review, đóng).
1a. **M-DB nền dữ liệu** (ngay sau M-0, loại NHẸ: thiết kế đã chốt ở `schema.md`, không debate, SA chia task theo nhóm bảng, Security duyệt 1 lượt): `python3 .claude/agent-team/pool.py schema` phải ✅ (mọi bảng có migration). Xong M-DB: chạy `MIGRATE_CMD` trong container `APP_SERVICE` trên DB dev, migrate không lỗi mới ghi M-DB `DONE`. Thiếu bảng hoặc M-DB chưa `DONE` thì `pool.py fill` chỉ chạy M-0 / M-DB, module khác (kể cả debate) chờ. Sau M-DB, module chỉ được **thêm** migration (thêm cột / bảng riêng); đổi / xoá cột bảng chung → GAP, bạn duyệt + báo module dùng bảng đó, `merge-begin --allow-schema-change` (không có cờ thì merge bị chặn).
1a2. **M-SKEL-BE + M-SKEL-FE khung file** (sau M-DB, 2 module chạy song song, loại NHẸ, không debate; SA liệt kê trong `docs/product/contracts/M-SKEL.md`): tạo sẵn **file đúng quy chuẩn `docs/engineering/`** cho mọi module, để module sau chỉ điền vào file có sẵn, không cùng tạo / sửa 1 chỗ. `contracts/M-SKEL.md` có bảng **hàm / file → module chủ** + props của từng màn: module chỉ sửa thân hàm và file mình chủ, hàm mới thêm cuối file (khác đoạn, git merge không conflict); đổi chữ ký hàm / props của module khác → GAP.
   - **M-SKEL-BE** (`backend-dev`): service **theo model** như quy chuẩn (1 model = 1 service), **không** tạo service theo module / nghiệp vụ. Mỗi hàm module cần: chữ ký đầy đủ + thân stub đánh dấu module chủ theo cách của stack (vd PHP `#[Stub('M-7')]`); hàm đọc trả dữ liệu từ factory / seeder M-DB, hàm ghi không đổi dữ liệu, trả thông báo thân thiện "Tính năng đang hoàn thiện" (toast / flash, không trang lỗi 501) để client demo bấm được. Controller trả props đúng contract, request, route (1 file route mỗi module).
   - **M-SKEL-FE** (`frontend-dev`): **chuyển mockup đã duyệt sang code, không tự thiết kế** (`docs/product/design/`, quy tắc chuyển ở `agents/frontend-dev.md`). T-1 (1 agent): `assets/theme.js` → theme / biến CSS dự án, layout, **route + file trang rỗng cho mọi màn** trong `screens.md`, type props theo contract. Mỗi component chung trong `components/*.js` = 1 task (song song, phụ thuộc T-1). **Mỗi màn = 1 task** (1 worktree, 1 agent mới, phụ thuộc T-1 + component màn dùng): chuyển màn đó, giữ HTML + class, đổi cú pháp template, `data/*.js` → props; chỉ sửa file màn của mình, không sửa component chung (thiếu → báo Lead). Xong → merge → slot trống → `pool.py fill` mở màn tiếp, tới khi hết màn (tối đa `MAX_PARALLEL` màn cùng lúc). Agent chuyển mockup dùng model **sonnet** (việc chép theo mẫu); `ui-designer` review cuối dùng opus. **Review UI/UX** (task cuối, sau khi mọi màn đã merge): `ui-designer` (opus) chụp app và mockup cùng màn × cùng `VIEWPORTS` × mọi trường hợp (Playwright có sẵn), so cạnh nhau: lệch bố cục / màu / cỡ / khoảng cách / thiếu chức năng → `docs/product/ui/review.md` (màn, lệch gì, 2 ảnh). Lệch → `frontend-dev` sửa trong code cho giống mockup, review lại, tối đa 2 vòng. Task màn / component chỉ chạy `LINT_CMD` trên file đã sửa (không build FE mỗi task); build FE **1 lần** sau khi mọi màn đã merge, pass trước review UI. M-SKEL-FE chỉ `DONE` khi review `PASS`. Dữ liệu: FE cùng repo với BE (Inertia / Blade, BE trả trang) → `M-SKEL-FE → M-SKEL-BE (contract)`, props từ controller stub; FE ở repo riêng (SPA, có trong `REPOS`) → không phụ thuộc M-SKEL-BE, tự mock theo contract (vd `mocks/`), module nối API thật thì xoá mock trong cùng task.
   - Module thay stub của mình bằng code thật và bỏ dấu stub trong cùng task.
   - M-SKEL-BE / M-SKEL-FE chưa `DONE` thì `pool.py fill` vẫn mở **debate** module khác (chỉ viết tài liệu) nhưng **không mở task code** ngoài M-0 / M-DB / M-SKEL-* (tránh conflict file khung); M-SKEL được slot trước, task đang chạy vẫn chạy tiếp. Task M-SKEL-* (`Loại: ĐÃ CHIA (M-SKEL-…)`): không viết test mới, không S4 `test-executor`, không E2E, **không** `code-reviewer` / `security` / `challenger` (ghi `Code review: N/A`, `Security review: N/A`, hook cho qua), không review UI từng task (`ui-designer` chỉ review 1 lần ở task cuối). **Không test, không IT** (chưa có dữ liệu thật): `Kết quả test: N/A`; dev chỉ tự chạy `LINT_CMD` (FE thêm build FE) cho code sạch. `pool.py merge-begin` của M-SKEL-* tự merge + commit luôn, không chạy IT. Task M-SKEL-FE **không tạo DB riêng** (`agent-db.sh`), không chạy app: lint + build FE bằng container tạm (`docker compose run --rm`). Review UI/UX chạy **sau khi** mọi task màn đã merge: **1 container app** trên nhánh phiên (cổng `E2E_PORT`), `SEED_CMD` trước, chụp mọi màn × `VIEWPORTS`, xong thì tắt.
   - **🚀 DEMO 2 (UI bấm được)**, ngay khi M-SKEL-FE `DONE`: build FE pass → `git push origin <branch phiên>` → `git push origin HEAD:demo-ui` (tạo / fast-forward, không force; chỉ Lead đẩy, không ai commit thẳng lên `demo-ui`). Cập nhật `docs/product/HANDOVER.md` (mục 12). Báo user: nhánh `demo-ui` + commit, danh sách màn, `SEED_CMD` cần chạy trên staging, tài khoản demo mỗi vai trò (từ seeder). **Không dừng**: build module tiếp; góp ý của client → task sửa UI vào pool, xong thì đẩy lại `HEAD:demo-ui`. Chỉ dừng chờ client khi user bảo.
1b. **Contract module NẶNG** (`Loại: NẶNG` / `LỚN`, thường auth / quyền): `solution-architect` + `security` viết `docs/product/contracts/M-<n>.md` (API / service / bảng dữ liệu mà module khác dùng, mã lỗi, quyền). Module phụ thuộc `(contract)` làm song song dựa vào file này.
1c. **Bàn giao:** M-0 có seeder (`SEED_CMD` trong config: DB mới + dữ liệu mẫu cho test / E2E), `.env.example` đủ key, README mục "Chạy dự án lần đầu" (cài, `.env`, docker, seed, test). `python3 .claude/agent-team/pool.py handoff` phải đủ ✅ (gap-check, Loại + Gồm R, lý do phụ thuộc, contract NẶNG, M-0 test + E2E PASS, `.env.example`, `SEED_CMD`, README) mới sang C. In danh sách module nhận được ngay.
   - `APP_BUILD=manual` (team): commit + push, báo user mở PR vào nhánh gốc + gửi team danh sách module nhận được ngay. **DỪNG.**
   - `APP_BUILD=auto` (mặc định, 1 người): sang C ngay.

**Phase C (build module):**
2. **`APP_BUILD=manual` (team):** mỗi người (máy riêng, `DEV_ID` trong `.claude/agent-team.local.config`) chạy `/agent-team:task M-<n>`: Lead của máy đó `pool.py claim M-<n>` (pull, kiểm phụ thuộc đã `DONE` trên nhánh gốc hoặc chỉ cần contract đã có, kiểm chưa ai nhận, tạo branch `agent/YYYYMMDD-<DEV_ID>-m<n>`, ghi Người chạy, push ngay) → thiết kế module theo Loại → chia task → `pool.py` như dưới, **chỉ module đó** → `pool.py sync` + integration test → PR vào nhánh gốc (người review merge) → báo cáo → **dừng** (không tự nhận module khác). `pool.py claimable`: module nhận được / chờ / đã có người.
   **`APP_BUILD=auto`:** bạn làm mục 2b cho mọi module, trên 1 branch phiên.
2b. **Điều phối (cả 2 chế độ): nhiều task chạy song song** (`task.md` mục 6c, script `pool.py`). 1 phiên = 1 branch `agent/<task-id app>`; mỗi task 1 worktree + branch tạm, xong merge về branch phiên. Không dừng hỏi user, không bảo user gõ lệnh.
   ```
   Debate module (≤ MAX_DEBATE, mỗi debate 1 slot)  Thực thi (task + debate ≤ MAX_PARALLEL cả app)   Merge (lần lượt)
   M-n: debate theo loại → chia task T-k  ──►  task READY → worktree → dev → test → review  ──►  merge --no-commit → IT
        pool.py module M-n --state DESIGN        pool.py fill / wait                              PASS: ✅ · FAIL / conflict: FIX
        → pool.py add (mỗi T-k) → --state SPLIT   (task chờ phụ thuộc chưa merge thì không lấy)     module đủ ✅ → tag m<n>-done
   ```
   - **Thiết kế module** (ở thư mục chính, TASK.md riêng của module, chỉ S1-S2, rồi `rm .agent-team/stage`): theo cột "Loại" trong bảng Module: `NHẸ` (CRUD theo khuôn có sẵn) → `solution-architect` viết thiết kế + contract, `test-designer` + `security` duyệt 1 lượt, không debate · `VỪA` → 1 lượt đề xuất + 1 lượt WHY · `NẶNG` (auth / quyền / tiền / dữ liệu nhạy cảm / kiến trúc) → debate đầy đủ (`task.md` mục 4). `security` được nâng loại.
   - **Chia task** (`solution-architect` + `business-analyst`): mỗi T-k ghi vào bảng Task của module (TASK.md thiết kế, mục "Chia task"): mô tả, AC (`AC-n` của R-n), **file / vùng sẽ đụng**, **phụ thuộc theo task** (`M-1/T-1`, không ghi cả module), API contract dùng. Hai task đụng cùng file → gộp hoặc cho phụ thuộc nhau (không chạy song song). Rồi `pool.py add M-n/T-k --task-id <YYYYMMDD-mn-tk> --title ".." --deps ".."` từng task, `pool.py module M-n --state SPLIT`.
   - **Chia slot (`pool.py fill` tự làm):** `MAX_PARALLEL` (mặc định 8) slot cho cả app, gồm task code **và** debate module. `MAX_PARALLEL` là số agent user đã cho phép chạy cùng lúc: `fill` mở việc nào thì gọi agent cho việc đó ngay, không hỏi lại user. Debate 1 module = 1 slot (chưa biết bao nhiêu task), tối đa `MAX_DEBATE` (mặc định 4) debate cùng lúc, module khác chờ. Module đã chia task (SPLIT) chiếm bao nhiêu slot cũng được (bằng số task READY). Slot trống cấp theo **thứ tự bảng Module**: task READY của module trước, hoặc bắt đầu debate module kế (khi mọi module nó phụ thuộc đã chia task / có contract). Không dừng task đang chạy để nhường.
   - **Task READY** khi: task phụ thuộc đã merge, module đã SPLIT, module phụ thuộc `(code)` DONE hoặc `(contract)` có file contract. Debate nhỏ khi task gặp GAP không tính vào `MAX_DEBATE`.
   - Nhiều debate cùng ghi docs ở thư mục chính an toàn: guard ghi lại ai ghi file nào, không hoàn tác bài của người khác.
   - **Team nhiều người:** cột "Người chạy" trong bảng Module = `DEV_ID` (hoặc `git config user.name`) của người đang chạy phiên điều phối module đó. Module `DESIGN` / `DOING` của người khác → bỏ qua, không động vào. Nhận module: ghi tên mình + `DESIGN`, commit + push ngay (người khác pull thấy).
   - **Chỉ dừng khi:** chỉ còn việc chờ owner (GAP cần owner → task / module `BLOCKED`, build form; việc không phụ thuộc vẫn chạy) · mọi việc còn lại BLOCKED · hết bảng Module (M-E2E ✅) · hết quota (user `/agent-team:resume` là chạy tiếp từ `pool.py resume`).
   - AC của task = AC của các R-n trong module (BA chi tiết hoá). Workflow / wireframe lấy từ `docs/product/`, không vẽ lại. Module đi ngược `docs/decisions/` → sửa quyết định trước. Câu nghiệp vụ phát sinh cần owner → Q-n `OWNER` → form. Hook chặn mọi task sang S3 khi `APP.md` chưa `Owner duyệt: APPROVED`.
2c. **Đồng bộ nhánh gốc (`pool.py sync`)**, bắt buộc: trước khi chia task, mỗi khi `pool.py wait` báo nhánh gốc có commit mới, trước khi tạo PR. Đọc lại **đúng file docs đã đổi** (script in danh sách), contract / quy tắc / quyền / ADR đổi mà module đang dùng → GAP, dừng task liên quan. Conflict → script `--abort`, báo user file conflict, **không tự gộp code người khác**.
2c2. **`TEST_MODE=mvp` → giao MVP trước Phase D:** mọi module trừ M-E2E `DONE` → build FE 1 lần + `TEST_CMD` + `FE_TEST_CMD` toàn bộ PASS → cập nhật `HANDOVER.md` (bản MVP) → `git push origin <branch phiên>` → `git push origin HEAD:demo-mvp` → báo user (như DEMO 2) + danh sách task `E2E: DEFER`. **DỪNG**, M-E2E giữ `BLOCKED "chờ user bảo chạy"`; chỉ chạy Phase D khi user bảo ("chạy M-E2E"). M-E2E bước đầu: chạy toàn bộ spec (các spec DEFER chưa chạy lần nào), phân loại fail = spec lệch (test-executor sửa) / lỗi app (task sửa).
2d. **Phase D:** khi mọi module trừ M-E2E `DONE` trên nhánh gốc (`pool.py claimable` thấy 🟢 M-E2E): `/agent-team:task M-E2E` (manual) hoặc bạn làm tiếp (auto): chạy toàn bộ E2E mọi luồng "1 ngày của <vai trò>" × mọi `VIEWPORTS`, lỗi tích hợp → task sửa, báo cáo cuối app. M-E2E `PASS` → **🚀 DEMO 3 (bản hoàn thiện)**: `git push origin <branch phiên>` → `git push origin HEAD:demo-full`, báo user như DEMO 2; fixbug sau đó xong đợt nào đẩy lại `HEAD:demo-full` đợt đó (`demo-ui` không cập nhật nữa). Trước E2E: grep dấu stub (vd `#[Stub(`) và mock FE (vd `mocks/`) phải rỗng (còn stub → task sửa của module chủ).
3. **Merge cho user:** auto: 1 branch `agent/<task-id app>` (tag `…-m<n>-done` mỗi module), user merge 1 lần hoặc tới tag. manual: mỗi module 1 PR vào nhánh gốc, người review merge (agent không bao giờ merge vào nhánh gốc). Branch tạm của task giữ lại (không xoá branch). `PUSH=1`: push branch phiên + tag sau mỗi module.
4. **Tài liệu app luôn đúng với code:** module đổi yêu cầu / phát sinh GAP → sửa `docs/product/` (task.md mục 7b). Mỗi module xong: cập nhật cột Trạng thái trong `APP.md`, chạy `gap-check.py --spec`. Hook chặn S6 của mọi task khi tài liệu app thiếu hoặc SPEC.md cũ.

## 11. Thiếu sót phát hiện về sau
- GAP khi code (task.md mục 7b) mà nguyên nhân là "Phase A bỏ sót" → ghi bài học **và** nêu ở báo cáo: "nên thêm vào `catalog/<loại>.md` của plugin: <mục, câu hỏi ngắn, đề xuất>". Lần sau app cùng loại sẽ được hỏi sớm.

## 12. Báo cáo
- **Mỗi lượt form:** dòng đầu "Gửi file `docs/product/QnA-v<n>.xlsx`: owner điền mục A, dev điền mục B" + số câu mỗi mục (số câu CAO). Việc tiếp theo: nhận file trả lời rồi `/agent-team:resume <task-id> <file>`.
- **Cuối Phase A:** dòng đầu "Owner đã chốt logic" (hoặc còn chờ gì). Kèm: đường dẫn `docs/product/SPEC.md`, số yêu cầu, số luồng, số màn, danh sách module + thứ tự, các `GIẢ ĐỊNH` mức THẤP.
- **Trong lúc điều phối:** tiến độ đầy đủ ở `.agent-team/STATUS.md` (tự cập nhật, báo user đường dẫn 1 lần). User nói đã merge tay → `pool.py reconcile`. Không dán `pool.py status` / `progress.py --list` vào chat sau mỗi lượt: chỉ báo 1 dòng khi task ✅ / FIX / GAP, rồi **chạy tiếp luôn**, không chờ user. Gom lệnh theo `task.md` mục 2 (Ít lượt gọi).
- **Bàn giao (`docs/product/HANDOVER.md`, mẫu `templates/product/HANDOVER.md`)** ở mỗi DEMO 2 / MVP / DEMO 3 và cuối app: `business-analyst` viết mục 2 "Hướng dẫn sử dụng theo vai trò" từ `flows.md` + `screens.md` (luồng chính, từng bước theo màn thật), mục 3 "Có / chưa có" từ bảng Module + `requirements.md`; bạn điền phần còn lại: URL, branch / tag, tài khoản demo mỗi vai trò lấy từ seeder (**không ghi mật khẩu**, chỉ tên biến), ghi chú phát hành (migration, env mới chỉ tên, lệnh chạy), cách báo lỗi. Viết cho client: không mã nội bộ. Commit cùng lần push nhánh demo; báo user đường dẫn file.
- **Cuối app** (hết bảng Module hoặc dừng ở điểm dừng): bảng module (Trạng thái, tag, lý do BLOCKED), branch phiên để merge, `docs/product/HANDOVER.md` đã cập nhật.
- Cuối cùng: đúng 1 việc user làm tiếp (≤ 2 phút); đang chạy tiếp thì ghi "chưa cần làm gì".
