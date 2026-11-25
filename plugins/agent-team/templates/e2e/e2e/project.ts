export const loginPath = '/login';
export const privatePath = '/dashboard';
export const fields = {
  user: 'input[name="email"]',
  password: 'input[name="password"]',
  submit: 'button[type="submit"]',
};
export const password = process.env.E2E_PASSWORD ?? 'password';
export const roles: Record<string, string> = {
  admin: 'admin@example.com',
};
export const resetCmd = 'php artisan db:seed --class=E2eSeeder --force';
