import { defineConfig } from '@playwright/test';
import { widths } from './e2e/support/env';

const full = Math.max(...widths);
const vp = (w: number) => ({ viewport: { width: w, height: w < 768 ? 812 : 900 }, isMobile: w < 768, hasTouch: w < 768 });

export default defineConfig({
  testDir: 'e2e',
  retries: 0,
  workers: widths.length,
  fullyParallel: false,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: 'list',
  use: { baseURL: process.env.BASE_URL, trace: 'retain-on-failure', video: 'off', screenshot: 'only-on-failure' },
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
