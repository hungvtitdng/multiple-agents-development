---
name: test-automation
description: Nguyên tắc chuyển test case thành test tự động cho mọi framework test - chọn tầng test, đặt tên theo AC, dữ liệu, thời gian, gọi ngoài, assert, chạy trên DB riêng của task, ghi bằng chứng PASS/FAIL. Quy ước công cụ của dự án nằm ở docs/testing/automation-guide.md. Dùng khi test-executor viết và chạy test.
---

# Test tự động từ test case

## 0. Đọc hướng dẫn riêng của dự án trước
`docs/testing/automation-guide.md`: framework test, thư mục, cách tạo dữ liệu (factory/fixture), helper đóng băng thời gian, cách mock gọi ngoài, lệnh chạy, file mẫu nên bắt chước. Đọc thêm `docs/testing/cases/<task-id>.md`.
- Chưa có hoặc thiếu mục nào → tìm 1-2 file test cùng loại trong repo làm mẫu, làm theo nguyên tắc dưới, ghi **"Đề xuất bổ sung automation-guide.md"** trong kết quả.

## 1. Quy ước viết (mọi framework)
- Tên test chứa ID: `AC-2 TC-5: <hành vi>`. Một test = một hành vi.
- Chọn **tầng rẻ nhất đủ chứng minh**: logic thuần → unit; API/quyền → test tầng request/API; luồng người dùng quan trọng → E2E.
- **Phân quyền luôn test ở tầng API/request**, không chỉ test giao diện ẩn nút.
- Dữ liệu tự tạo trong test, không dựa dữ liệu có sẵn. Test độc lập, không phụ thuộc thứ tự chạy.
- Thời gian: đóng băng/giả lập, không chờ cố định (`sleep`).
- Gọi ngoài (HTTP, mail, queue, bên thứ ba): giả lập, và kiểm có được gọi đúng tham số.
- E2E: chọn phần tử theo vai trò/nhãn/test-id ổn định, chờ theo điều kiện hiển thị.
- Assert kết quả cụ thể (mã lỗi, giá trị, số bản ghi, trạng thái). Test phải **fail được** nếu bỏ phần code mới.

## 1b. E2E trình duyệt (Playwright) + responsive
Task có UI: E2E có ảnh bằng chứng ở **mọi chiều rộng** trong config `VIEWPORTS`. Dự án chưa có Playwright → chép khung chuẩn `.claude/agent-team/e2e-template/` (bảng dưới), chỉ sửa `e2e/project.ts`, ghi vào `automation-guide.md`. Dự án đã có E2E → không ghi đè, dùng khung chuẩn làm mẫu khi sửa.

**Chạy nhanh (bắt buộc, E2E chậm thì cả pool chờ):**
1. **Luồng đầy đủ chỉ chạy ở chiều rộng lớn nhất.** Chiều rộng nhỏ hơn chỉ chạy test gắn tag `@responsive` (không cuộn ngang, menu ☰, nút ≥ 44, chụp ảnh trạng thái). Không lặp cả bộ test ở mọi chiều rộng.
2. **Song song theo chiều rộng:** `workers` = số chiều rộng, `fullyParallel: false` (song song giữa project, tuần tự trong project). Dữ liệu seed tách theo chiều rộng (vd mã người dùng có hậu tố `W375`); reset chỉ xoá / tạo lại dữ liệu của chiều rộng đó, **không** xoá cả bảng dùng chung (`sessions`, `cache`, `jobs`...).
3. **Đăng nhập 1 lần** mỗi vai trò × mỗi chiều rộng trong project `setup`, lưu `storageState`, test dùng lại. Chỉ test về chính màn đăng nhập mới đi qua form.
4. **Reset ít nhất có thể:** file chỉ đọc → reset ở `beforeAll`; file có ghi dữ liệu → `beforeEach`. Reset bằng 1 lệnh gọn (1 tiến trình, không khởi động framework nhiều lần trong 1 lần reset).
4b. **Reset / seed từ E2E:** gọi `sh -c "$APP_EXEC php <script>"` (lệnh `e2e` truyền sẵn `APP_EXEC` = đúng container + thư mục + DB của task, chạy được cả `CLONE_MODE=container` lẫn `schema`). Không ghi cứng tên container.
5. **Server app phục vụ song song:** `APP_START_CMD` không dùng server 1 luồng (PHP `php -S` → thêm `PHP_CLI_SERVER_WORKERS=8`; Rails puma ≥ 2 thread; Node không chạy dev server có HMR). Build FE 1 lần trước, không build lại mỗi test.
6. **Ít E2E:** logic / validate / quyền kiểm bằng test BE; E2E chỉ luồng chính + `@responsive`. Mỗi spec gắn tag module (`test.describe('… @m6', …)`).
7. **Chạy đúng phạm vi:** trong task chỉ chạy spec đã sửa + `--grep @m<n>` của module; sửa lỗi thì `--last-failed`; dev tự chạy thêm `--max-failures=1`. **Toàn bộ E2E chỉ ở M-E2E** (và trước demo).
8. **Không build FE mỗi lần chạy:** `APP_START_CMD` chỉ build khi file FE đổi (vd so hash `resources/` với file đánh dấu trong `public/build/`), không thì dùng bản đã build.
- Đo thời gian trước / sau khi sửa E2E, ghi vào TASK.md. Không thêm `waitForTimeout`; chờ bằng `expect(...).toBeVisible()` / `waitForURL`.

**Khung chuẩn: `.claude/agent-team/e2e-template/` (hook sync chép từ `templates/e2e/` của plugin mỗi phiên)** (đã chạy thật, sửa ở đây thì sửa template, không chép code vào skill):
| File | Làm gì | Dự án sửa? |
|---|---|---|
| `playwright.config.ts` | quy tắc 1-3: workers theo chiều rộng, `@responsive`, project `setup`, timeout 30s / 5s, trace khi lỗi, video tắt | không |
| `e2e/project.ts` | trang login, ô nhập, mật khẩu, tài khoản mỗi vai trò (`{w}` = chiều rộng, vd `CB01W{w}`), `resetCmd` | **có (M-0)** |
| `e2e/auth.setup.ts` | đăng nhập 1 lần × vai trò × chiều rộng → `e2e/.auth/` | không |
| `e2e/support/env.ts` | `widths`, `asRole('admin')` cho `test.use(...)` | không |
| `e2e/support/db.ts` | `reset(...)` / `inApp(cmd)` qua `$APP_EXEC` (quy tắc 4b) | không |
| `e2e/support/responsive.ts` | `shot()` ảnh bằng chứng, `expectResponsive()` | không |
| `e2e/smoke.spec.ts` | smoke M-0: trang đầu + trang cần đăng nhập, mọi chiều rộng | không |

Test mẫu (`@responsive` → chạy ở mọi chiều rộng; không tag → chỉ chiều rộng lớn nhất):
```ts
import { test, expect } from '@playwright/test';
import { shot, expectResponsive } from './support/responsive';

test('AC-2 TC-2: huỷ đơn @responsive', async ({ page }) => {
  await page.goto('/orders');
  const cancel = page.getByRole('button', { name: 'Huỷ' }).first();
  await expectResponsive(page, cancel);
  await shot(page, 'TC-2-normal');
  await cancel.click();
  await expect(page.getByText('Đã huỷ')).toBeVisible();
  await shot(page, 'TC-2-done');
});
```
- Mỗi trạng thái của mockup (rỗng, đang tải, lỗi, không có quyền) có ít nhất 1 ảnh, tên `<TC>-<trạng thái>`, trong test `@responsive` (hook kiểm có ảnh ở mọi chiều rộng).
- Hành vi khác theo chiều rộng (menu ☰): `test.skip(page.viewportSize()!.width >= 768, 'chỉ màn nhỏ')`.
- Dữ liệu E2E tạo qua API / seed của dự án trên DB riêng của task, không phụ thuộc dữ liệu có sẵn.

## 2. Chạy
- Trên DB riêng của task: `.claude/agent-team/agent-db.sh test <task-id> <phạm vi test>`.
- E2E: `.claude/agent-team/agent-db.sh e2e <task-id> [tham số cho E2E_CMD]`: chạy app (`APP_START_CMD`) trên clone, chạy `E2E_CMD` trên máy với `BASE_URL`, `VIEWPORTS`, `EVIDENCE_DIR=docs/testing/evidence/<task-id>/`, rồi tắt app.
- Chạy test mới trước, sau đó nhóm test liên quan để bắt regression.
- Lúc pass lúc fail: chạy lại 1 lần; vẫn chập chờn → ghi `FAIL` kèm "flaky", không ghi PASS.

## 3. Ghi kết quả
Mỗi test case một dòng trong `docs/testing/test-report.md`:
`| <task-id> | AC-n | <tên test> | PASS/FAIL/BLOCKED/NOT RUN | <lệnh + dòng kết quả làm bằng chứng> |`
- E2E: tên test ghi kèm chiều rộng đã chạy (`TC-2 (375, 768, 1280)`), cột bằng chứng thêm đường dẫn ảnh. Fail ở 1 chiều rộng = `FAIL`.
- `BLOCKED`: không chạy được vì môi trường/dữ liệu, ghi lý do.
- `FAIL` do code: bước tái hiện ngắn, `file:dòng` nghi ngờ, @dev cần sửa.
