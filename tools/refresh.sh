#!/bin/bash
# Update Table A Sprint 13 data NGAY: regenerate data.json từ GitHub → push nếu đổi.
# Dùng cho cả cron (launchd) lẫn chạy tay (in kết quả ra màn hình + ghi log).
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO="/Volumes/Works/rikkeisoft/w3-pr-tracking-tables"
LOG="$REPO/tools/refresh.log"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%F %T') ==="
  gh auth switch --user nguyenducbien-art >/dev/null 2>&1
  # Máy này là nguồn code + commit duy nhất → KHÔNG kéo commit về (no fetch/merge/reset).
  python3 tools/fetch_build.py data.json
  rc=$?
  if [ "$rc" -eq 2 ]; then echo "→ Không có thay đổi, khỏi push."; exit 0; fi
  if [ "$rc" -ne 0 ]; then echo "→ LỖI fetch_build (rc=$rc)"; exit 1; fi
  # Đẩy data.json vào nhánh `data` bằng plumbing — KHÔNG checkout, KHÔNG đụng main,
  # KHÔNG trigger Pages build (Pages chỉ build khi `main` đổi) → không bao giờ chạm rate-limit.
  BLOB=$(git hash-object -w data.json)
  TREE=$(printf '100644 blob %s\tdata.json\n' "$BLOB" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="biennguyen131311@gmail.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh data $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (KHÔNG build Pages). Web tươi trong ~5p (cache raw 300s)." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
