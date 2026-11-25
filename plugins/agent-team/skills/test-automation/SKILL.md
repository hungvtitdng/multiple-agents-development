---
name: test-automation
description: Nguyên tắc chuyển test case thành test tự động cho mọi framework test - chọn tầng test, đặt tên theo AC, dữ liệu, thời gian, gọi ngoài, assert, chạy trên DB clone, ghi bằng chứng PASS/FAIL. Quy ước công cụ của dự án nằm ở docs/testing/automation-guide.md. Dùng khi test-executor viết và chạy test.
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
Task có UI: E2E có ảnh bằng chứng ở **mọi chiều rộng** trong config `VIEWPORTS`. Dự án chưa có Playwright → dựng theo khung dưới (thư mục E2E theo `TEST_PATHS`, vd `e2e/`), ghi vào `automation-guide.md`.

**Chạy nhanh (bắt buộc, E2E chậm thì cả pool chờ):**
1. **Luồng đầy đủ chỉ chạy ở chiều rộng lớn nhất.** Chiều rộng nhỏ hơn chỉ chạy test gắn tag `@responsive` (không cuộn ngang, menu ☰, nút ≥ 44, chụp ảnh trạng thái). Không lặp cả bộ test ở mọi chiều rộng.
2. **Song song theo chiều rộng:** `workers` = số chiều rộng, `fullyParallel: false` (song song giữa project, tuần tự trong project). Dữ liệu seed tách theo chiều rộng (vd mã người dùng có hậu tố `W375`); reset chỉ xoá / tạo lại dữ liệu của chiều rộng đó, **không** xoá cả bảng dùng chung (`sessions`, `cache`, `jobs`...).
3. **Đăng nhập 1 lần** mỗi vai trò × mỗi chiều rộng trong project `setup`, lưu `storageState`, test dùng lại. Chỉ test về chính màn đăng nhập mới đi qua form.
4. **Reset ít nhất có thể:** file chỉ đọc → reset ở `beforeAll`; file có ghi dữ liệu → `beforeEach`. Reset bằng 1 lệnh gọn (1 tiến trình, không khởi động framework nhiều lần trong 1 lần reset).
5. **Server app phục vụ song song:** `APP_START_CMD` không dùng server 1 luồng (PHP `php -S` → thêm `PHP_CLI_SERVER_WORKERS=8`; Rails puma ≥ 2 thread; Node không chạy dev server có HMR). Build FE 1 lần trước, không build lại mỗi test.
6. **Ít E2E:** logic / validate / quyền kiểm bằng test BE; E2E chỉ luồng chính + `@responsive`. Mỗi spec gắn tag module (`test.describe('… @m6', …)`).
7. **Chạy đúng phạm vi:** trong task chỉ chạy spec đã sửa + `--grep @m<n>` của module; sửa lỗi thì `--last-failed`; dev tự chạy thêm `--max-failures=1`. **Toàn bộ E2E chỉ ở M-E2E** (và trước demo).
8. **Không build FE mỗi lần chạy:** `APP_START_CMD` chỉ build khi file FE đổi (vd so hash `resources/` với file đánh dấu trong `public/build/`), không thì dùng bản đã build.
- Đo thời gian trước / sau khi sửa E2E, ghi vào TASK.md. Không thêm `waitForTimeout`; chờ bằng `expect(...).toBeVisible()` / `waitForURL`.

`playwright.config.ts`:
```ts
import { defineConfig } from '@playwright/test';
const widths = (process.env.VIEWPORTS || '1280').split(/\s+/).filter(Boolean).map(Number);
const full = Math.max(...widths);
const vp = (w: number) => ({ viewport: { width: w, height: w < 768 ? 812 : 900 }, isMobile: w < 768, hasTouch: w < 768 });
export default defineConfig({
  testDir: 'e2e',
  retries: 0,
  workers: widths.length,
  fullyParallel: false,
  use: { baseURL: process.env.BASE_URL, trace: 'retain-on-failure', video: 'off' },
  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    ...widths.map((w) => ({
      name: `vp-${w}`,
      dependencies: ['setup'],
      grep: w === full ? undefined : /@responsive/,
      use: vp(w),
    })),
  ],
});
```

`e2e/auth.setup.ts` (đăng nhập 1 lần, lưu phiên theo vai trò × chiều rộng):
```ts
import { test as setup } from '@playwright/test';
const widths = (process.env.VIEWPORTS || '1280').split(/\s+/).filter(Boolean);
const roles = { 'can-bo': 'CB01', 'truong-phong': 'TP01', admin: 'AD01' };
for (const w of widths) for (const [role, code] of Object.entries(roles)) {
  setup(`login ${role} ${w}`, async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Mã cán bộ').fill(`${code}W${w}`);
    await page.getByLabel('Mật khẩu').fill(process.env.E2E_PASSWORD || 'Matkhau1');
    await page.getByRole('button', { name: 'Đăng nhập' }).click();
    await page.waitForURL((u) => !u.pathname.startsWith('/login'));
    await page.context().storageState({ path: `e2e/.auth/${role}-${w}.json` });
  });
}
```
Test dùng phiên: `test.use({ storageState: ({}, use, info) => use(`e2e/.auth/can-bo-${info.project.use.viewport!.width}.json`) })` (hoặc helper `asRole('can-bo')`). `e2e/.auth/` vào `.gitignore`.

`e2e/support/responsive.ts`: chụp ảnh bằng chứng + kiểm responsive:
```ts
import { expect, Locator, Page } from '@playwright/test';
import * as path from 'path';

// Ảnh: <EVIDENCE_DIR>/<TC>-<trạng thái>-<rộng>.png (guard kiểm đủ mỗi chiều rộng)
export async function shot(page: Page, name: string) {
  const w = page.viewportSize()!.width;
  await page.screenshot({ path: path.join(process.env.EVIDENCE_DIR || 'test-results', `${name}-${w}.png`), fullPage: true });
}

// Không cuộn ngang; < 768px: nút chính nhìn thấy và >= 44px
export async function expectResponsive(page: Page, primary?: Locator) {
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(over, 'trang bị cuộn ngang').toBeLessThanOrEqual(0);
  if (primary && page.viewportSize()!.width < 768) {
    await expect(primary).toBeInViewport();
    const box = (await primary.boundingBox())!;
    expect(Math.min(box.width, box.height), 'nút chính < 44px').toBeGreaterThanOrEqual(44);
  }
}
```

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
- Dữ liệu E2E tạo qua API / seed của dự án trên DB clone, không phụ thuộc dữ liệu có sẵn.

## 2. Chạy
- Trên DB clone: `.claude/agent-team/agent-db-clone.sh test <task-id> <phạm vi test>`.
- E2E: `.claude/agent-team/agent-db-clone.sh e2e <task-id> [tham số cho E2E_CMD]`: chạy app (`APP_START_CMD`) trên clone, chạy `E2E_CMD` trên máy với `BASE_URL`, `VIEWPORTS`, `EVIDENCE_DIR=docs/testing/evidence/<task-id>/`, rồi tắt app.
- Chạy test mới trước, sau đó nhóm test liên quan để bắt regression.
- Lúc pass lúc fail: chạy lại 1 lần; vẫn chập chờn → ghi `FAIL` kèm "flaky", không ghi PASS.

## 3. Ghi kết quả
Mỗi test case một dòng trong `docs/testing/test-report.md`:
`| <task-id> | AC-n | <tên test> | PASS/FAIL/BLOCKED/NOT RUN | <lệnh + dòng kết quả làm bằng chứng> |`
- E2E: tên test ghi kèm chiều rộng đã chạy (`TC-2 (375, 768, 1280)`), cột bằng chứng thêm đường dẫn ảnh. Fail ở 1 chiều rộng = `FAIL`.
- `BLOCKED`: không chạy được vì môi trường/dữ liệu, ghi lý do.
- `FAIL` do code: bước tái hiện ngắn, `file:dòng` nghi ngờ, @dev cần sửa.
