#!/bin/bash
# Cron/launchd: regenerate data.json từ GitHub → push nếu đổi. Chỉ repo này.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
REPO="/Volumes/Works/rikkeisoft/w3-pr-tracking-tables"
LOG="$REPO/tools/refresh.log"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%F %T') ==="
  gh auth switch --user nguyenducbien-art >/dev/null 2>&1
  git fetch -q origin main && git reset -q --hard origin/main   # repo bot-owned: luôn sạch
  python3 tools/fetch_build.py data.json
  rc=$?
  if [ "$rc" -eq 2 ]; then echo "no change → skip push"; exit 0; fi
  if [ "$rc" -ne 0 ]; then echo "fetch_build ERROR rc=$rc"; exit 1; fi
  git add data.json
  git -c user.name="biennguyen" -c user.email="biennguyen131311@gmail.com" \
      commit -q -m "auto-refresh data $(date '+%F %H:%M')"
  git push -q origin main && echo "pushed"
} >> "$LOG" 2>&1
