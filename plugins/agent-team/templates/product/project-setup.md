# Phiếu khởi động dự án (Dev điền)

> Dev điền trước khi chạy `/agent-team:app`. Chưa chắc → ghi "Để team đề xuất" (Architect đề xuất, đi mục B của form). Không biết → để `TODO`.
> Lead đọc file này ở A0: ô đã điền thì chép sang `intake.md` + `.claude/agent-team.config`, không tạo Q-n `DEV`.
> **Không ghi password, KEY, token.** Env chỉ ghi tên key.

## 1. Dự án
- Tên dự án: TODO
- Git remote: TODO (URL / không có → `PUSH=0`)
- Base branch: TODO (main / develop)
- Repo: TODO (1 repo / nhiều repo: liệt kê, vd `. ../FrontEnd`)

## 2. Tech stack
- BE: TODO (ngôn ngữ + framework + version, vd Ruby 3.3 + Rails 7.2)
- FE: TODO (vd Vue 3 + Vite / Next.js 14 / server-render cùng BE)
- UI lib / CSS: TODO (vd Tailwind, Ant Design)
- Package manager: TODO (vd bundler + pnpm)
- Lint / format: TODO (vd rubocop, eslint + prettier)
- Test unit: TODO (vd rspec / jest / pytest)
- Test E2E: TODO (vd Playwright)

## 3. Database
- Engine + version: TODO (vd MySQL 8.0 / Postgres 16)
- Charset / collation: TODO (MySQL đề xuất `utf8mb4` / `utf8mb4_unicode_ci`)
- Timezone: TODO (vd lưu UTC, hiển thị Asia/Ho_Chi_Minh)
- Tên DB dev / test: TODO (vd `app_development` / `app_test`)
- Migration: TODO (lệnh generator của framework, chạy trong container app)

## 4. Hạ tầng
- Docker compose: TODO (file + tên service app / db, vd `app`, `db`)
- Cache: TODO (Redis / không)
- Queue / job: TODO (Sidekiq / BullMQ / Celery / không)
- Lưu file: TODO (S3 / local / không)
- Email: TODO (SMTP / SES / chưa có)

## 5. Môi trường & deploy
- Env keys: TODO (chỉ tên, vd `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY_BASE`)
- Môi trường: TODO (dev / staging / prod)
- Hosting: TODO (vd AWS ECS, VPS + Docker, Vercel)
- CI/CD: TODO (GitHub Actions / GitLab CI / chưa có)
- Đăng nhập: TODO (session / JWT / SSO Google / không có)

## 6. Quy chuẩn code (chốt trước khi Architect viết architecture / schema)
- Theo dự án mẫu: TODO (đường dẫn `docs/engineering/backend.md`, `frontend.md` của dự án có sẵn → chép nguyên / không có)
- BE nơi đặt logic nghiệp vụ: TODO (vd Service class `<Tên>Service`, controller mỏng)
- BE kiểm quyền: TODO (vd hàm trong `PermissionService` / Laravel Policy / Pundit)
- BE truy cập DB: TODO (vd gọi Model trực tiếp / Repository)
- BE đặt tên lớp: TODO (vd `<Domain>Service`, không tạo lớp lẻ kiểu `Approver`, `WorkingDays`)
- FE state / gọi API: TODO (vd Pinia + composable `useXxxApi` / React Query)
