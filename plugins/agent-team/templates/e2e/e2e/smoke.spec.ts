import { expect, test } from '@playwright/test';
import { loginPath, privatePath, roles } from './project';
import { asRole } from './support/env';
import { expectResponsive, shot } from './support/responsive';

test('smoke: trang đầu mở được, không lỗi JS @responsive', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const res = await page.goto('/');
  expect(res?.status()).toBeLessThan(400);
  await expectResponsive(page);
  await shot(page, 'SMOKE-home');
  expect(errors).toEqual([]);
});

test.describe('đã đăng nhập', () => {
  test.use(asRole(Object.keys(roles)[0]));

  test('smoke: vào trang cần đăng nhập @responsive', async ({ page }) => {
    await page.goto(privatePath);
    await expect(page).not.toHaveURL(new RegExp(loginPath));
    await expectResponsive(page);
    await shot(page, 'SMOKE-private');
  });
});
