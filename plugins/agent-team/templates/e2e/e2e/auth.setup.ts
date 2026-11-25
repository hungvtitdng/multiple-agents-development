import { test as setup } from '@playwright/test';
import { fields, loginPath, password, privatePath, roles } from './project';
import { authFile, widths } from './support/env';

for (const w of widths) {
  for (const [role, user] of Object.entries(roles)) {
    setup(`đăng nhập ${role} ${w}`, async ({ page }) => {
      await page.goto(loginPath);
      await page.locator(fields.user).fill(user.replace('{w}', String(w)));
      await page.locator(fields.password).fill(password);
      await page.locator(fields.submit).click();
      await page.waitForURL((u) => !u.pathname.startsWith(loginPath));
      await page.goto(privatePath);
      await page.context().storageState({ path: authFile(role, w) });
    });
  }
}
