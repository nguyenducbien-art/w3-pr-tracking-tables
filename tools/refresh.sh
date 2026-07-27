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
  # Chạy fetch cho CẢ Sprint 13 (data.json) lẫn Sprint 14 (data-s14.json).
  python3 tools/fetch_build.py data.json;         rc13=$?
  python3 tools/fetch_build_s14.py data-s14.json; rc14=$?
  # rc: 0=đổi, 2=không đổi, khác=lỗi
  if [ "$rc13" -ne 0 ] && [ "$rc13" -ne 2 ]; then echo "→ LỖI fetch_build s13 (rc=$rc13)"; exit 1; fi
  if [ "$rc14" -ne 0 ] && [ "$rc14" -ne 2 ]; then echo "→ LỖI fetch_build s14 (rc=$rc14)"; exit 1; fi
  if [ "$rc13" -eq 2 ] && [ "$rc14" -eq 2 ]; then echo "→ Cả 2 sprint không đổi, khỏi push."; exit 0; fi
  # Đẩy CẢ 2 file vào nhánh `data` bằng plumbing (KHÔNG checkout, KHÔNG đụng main, KHÔNG build Pages).
  # mktree cần entries sort theo tên: 'data-s14.json' < 'data.json' (vì '-' 0x2D < '.' 0x2E).
  B13=$(git hash-object -w data.json)
  B14=$(git hash-object -w data-s14.json)
  TREE=$(printf '100644 blob %s\tdata-s14.json\n100644 blob %s\tdata.json\n' "$B14" "$B13" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="biennguyen131311@gmail.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh data s13+s14 $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (s13+s14, KHÔNG build Pages). Web tươi ~5p (cache raw 300s)." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
