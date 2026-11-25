import type { TestInfo } from '@playwright/test';

export const widths = (process.env.VIEWPORTS || '1280').split(/\s+/).filter(Boolean).map(Number);

export const authFile = (role: string, w: number) => `e2e/.auth/${role}-${w}.json`;

export const asRole = (role: string) => ({
  storageState: async ({}, use: (s: string) => Promise<void>, info: TestInfo) =>
    use(authFile(role, info.project.use.viewport!.width)),
});
