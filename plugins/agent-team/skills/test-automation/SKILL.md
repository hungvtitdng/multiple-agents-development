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
Task có UI: E2E chạy ở **mọi chiều rộng** trong config `VIEWPORTS`, chụp ảnh làm bằng chứng. Dự án chưa có Playwright → dựng theo khung dưới (thư mục E2E theo `TEST_PATHS`, vd `e2e/`), ghi vào `automation-guide.md`.

`playwright.config.ts`: mỗi chiều rộng là 1 project `vp-<rộng>`:
```ts
import { defineConfig } from '@playwright/test';
const widths = (process.env.VIEWPORTS || '1280').split(/\s+/).filter(Boolean).map(Number);
export default defineConfig({
  testDir: 'e2e',
  retries: 0,
  use: { baseURL: process.env.BASE_URL, trace: 'retain-on-failure' },
  projects: widths.map((w) => ({
    name: `vp-${w}`,
    use: { viewport: { width: w, height: w < 768 ? 812 : 900 }, isMobile: w < 768, hasTouch: w < 768 },
  })),
});
```

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

Test mẫu (1 test chạy lặp ở mọi chiều rộng):
```ts
import { test, expect } from '@playwright/test';
import { shot, expectResponsive } from './support/responsive';

test('AC-2 TC-2: huỷ đơn', async ({ page }) => {
  await page.goto('/orders');
  const cancel = page.getByRole('button', { name: 'Huỷ' }).first();
  await expectResponsive(page, cancel);
  await shot(page, 'TC-2-normal');
  await cancel.click();
  await expect(page.getByText('Đã huỷ')).toBeVisible();
  await shot(page, 'TC-2-done');
});
```
- Mỗi trạng thái của wireframe (rỗng, đang tải, lỗi, không có quyền) có ít nhất 1 ảnh, tên `<TC>-<trạng thái>`.
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
