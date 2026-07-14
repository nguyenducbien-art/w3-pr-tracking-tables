#!/bin/bash
# Cron/launchd: regenerate data.json từ GitHub → push nếu đổi. Chỉ repo này.
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
  if [ "$rc" -eq 2 ]; then echo "no change → skip push"; exit 0; fi
  if [ "$rc" -ne 0 ]; then echo "fetch_build ERROR rc=$rc"; exit 1; fi
  # CHỈ commit đúng data.json (path-scoped) — bỏ qua MỌI file khác dù đang modified/staged.
  git -c user.name="biennguyen" -c user.email="biennguyen131311@gmail.com" \
      commit -q -m "auto-refresh data $(date '+%F %H:%M')" -- data.json
  git push -q origin main 2>/dev/null && echo "pushed" || echo "  push fail (kiểm tra tay)"
} >> "$LOG" 2>&1
