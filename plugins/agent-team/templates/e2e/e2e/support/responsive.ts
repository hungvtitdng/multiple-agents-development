import { expect, Locator, Page } from '@playwright/test';
import * as path from 'node:path';

export async function shot(page: Page, name: string) {
  const w = page.viewportSize()!.width;
  await page.screenshot({ path: path.join(process.env.EVIDENCE_DIR || 'test-results', `${name}-${w}.png`), fullPage: true });
}

export async function expectResponsive(page: Page, primary?: Locator) {
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(over, 'trang bị cuộn ngang').toBeLessThanOrEqual(0);
  if (primary && page.viewportSize()!.width < 768) {
    await expect(primary).toBeInViewport();
    const box = (await primary.boundingBox())!;
    expect(Math.min(box.width, box.height), 'nút chính < 44px').toBeGreaterThanOrEqual(44);
  }
}
