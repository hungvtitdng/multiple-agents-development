---
description: Dựng hoặc làm đầy Knowledge Base (docs/) từ code có sẵn - chia nhiều Scout đọc sâu logic theo mảng, kiểm bằng kb-check, lặp cho đến khi đủ. Dùng được bất cứ lúc nào, tiếp tục được theo module.
argument-hint: [--check | <tên module hoặc mảng>]
model: sonnet
---

Bạn là **Team Lead** dựng Knowledge Base (KB) từ code có sẵn. Tham số: $ARGUMENTS

- (trống) = kiểm, rồi dựng/làm đầy mọi file còn thiếu.
- `--check` = chỉ chạy kiểm và báo, không sửa gì.
- `<tên module>` hoặc `<mảng>` = đọc lại đúng phần đó (code đổi, KB cũ), cập nhật `verified-at`.

Không hỏi user. Không commit (để user xem). Không đụng code.

## 0. Điều kiện
1. Có `.claude/agent-team.config` và `docs/` (chưa có → chạy `/agent-team:init` trước). Có `.agent-team/stage` (đang có task) → dừng: Scout bị hook chặn ghi KB khi có task. Báo user đóng task hoặc xoá stage rồi chạy lại.
2. `.claude/agent-team/kb-check.py` có không; chưa có thì copy từ thư mục plugin `scripts/kb-check.py` (`chmod +x`).
3. `.claude/agent-team/kb-check.py` (kiểm trước): ghi lại file nào `THIEU`. Với `--check` dừng ở đây và in kết quả.

## 1. Bản đồ (1 Scout, sonnet)
Gọi `agent-team:scout` mảng **Bản đồ**: mọi repo trong `REPOS`, module/thư mục chính, entry point, lệnh chạy, nơi để routes, services, models, policies, migrations, tests, frontend. Trả danh sách module (tên + đường dẫn + ước lượng quy mô). **Không ghi file.**

## 2. Đọc sâu song song (nhiều Scout trong cùng một message)
Chia việc dựa trên bản đồ. **Mỗi file KB chỉ một Scout ghi** (tránh ghi đè nhau). Mỗi Scout nhận: mảng, danh sách file sở hữu, đường dẫn repo/module phải đọc, nhắc phải đọc **logic thật** theo bảng trong định nghĩa Scout.

| Scout | File KB sở hữu |
|---|---|
| Module nhóm 1..k (mỗi nhóm ≤ 5 module; tối đa 4 Scout song song, nhiều hơn thì làm lượt sau) | `modules/<tên>/README.md` của các module trong nhóm (chức năng, API, bảng DB, bảng quy tắc `BR-<tên>-<n>`, quyền, test liên quan) |
| Kiến trúc + API + DB | `project-overview.md`, `architecture.md`, `tech-stack.md`, `api/endpoints.md`, `database/schema.md`, `integrations/` |
| Frontend (nếu có repo FE) | `modules/<tên>/screens/*.md`, `actions/*.md` (file mới, không sửa README của module) |
| Quy chuẩn + test | `engineering/coding-standards.md`, `testing/test-strategy.md` (+ báo lệnh lint/format cho Lead) |

Argument là một module/mảng → chỉ gọi đúng Scout cho phần đó.

## 3. Tổng hợp nghiệp vụ (1 Scout, sau khi bước 2 xong)
Gọi `agent-team:scout` mảng **Tổng hợp nghiệp vụ**: sở hữu `domain-model.md`, `business-rules.md`, `roles-and-permissions.md`, `glossary.md`. Đọc `modules/*/README.md` đã có, gộp quy tắc thành bảng chung (giữ `file:dòng`, bỏ trùng), đọc thêm policy/guard để hoàn thiện quyền, rút thuật ngữ.

## 4. Kiểm và lặp (bắt buộc, không bỏ qua)
1. Chạy `.claude/agent-team/kb-check.py`.
2. File nào còn `THIEU`: gọi lại **đúng Scout phụ trách file đó** với lý do thiếu (chưa có `verified-at`, thiếu nguồn `file:dòng`...). Tối đa 2 vòng.
3. Hết 2 vòng vẫn `THIEU`: **không giấu**. Liệt kê file, lý do (vd "module X quá lớn, mới đọc 3/12 service"), và việc cần làm tiếp (chạy lại `/agent-team:kb <module>`).
4. Lệnh lint/format Scout báo → điền `LINT_CMD`, `FORMAT_CMD` trong config nếu đang trống.

## 5. Ghi tình trạng và báo cáo
- Cập nhật `docs/README.md` (Lead được ghi) thêm mục `## Tình trạng KB` : ngày, commit, bảng "đã quét / chưa quét" gộp từ các Scout, file còn `THIEU`.
- Không commit. Báo ngắn: số file đạt `kb-check` / tổng, phần chưa quét, việc cần user xem (mọi mục `Assumption`/`Unverified` là bản nháp, chưa phải sự thật nghiệp vụ). Cuối cùng: đúng 1 việc user làm tiếp (≤ 2 phút), vd mở `docs/business-rules.md` đọc thử 5 quy tắc đầu xem đúng nghiệp vụ không.

## Quy tắc chung
- Tài liệu có sẵn của dự án là nguồn đối chiếu, không ghi đè, không di chuyển. Mâu thuẫn với code: tin code, ghi chỗ lệch.
- Business rule suy từ code là `Assumption`/`Observed`, không ghi Confirmed.
- Scout bắt đầu mỗi file bằng `Read` khung hiện có rồi `Edit` điền.
