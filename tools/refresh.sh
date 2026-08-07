#!/bin/bash
# Làm mới dữ liệu PR-tracking (launchd cron mỗi 5' + chạy tay được).
#   1) fetch_build.py        → data.json         (Sprint 13, PR qua gh)
#   2) fetch_build_s12.py    → data-s12.json     (Sprint 12, PR qua gh)
#   3) fetch_build_s14.py    → data-s14.json     (Sprint 14, PR qua gh)
#   4) fetch_screens_s14.py  → screens-s14.json  (Sprint 14 tiến độ migrate/test — git r20260727 + Backlog)
# Đẩy CẢ 4 file vào nhánh `data` bằng git plumbing → KHÔNG checkout, KHÔNG build Pages
# (index/s12/s14 fetch data từ raw nhánh data) → không bao giờ chạm rate-limit Pages.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# git fetch repo code (private, SSH host-alias github-w3, key không passphrase) chạy được non-interactive:
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME/.ssh/id_ed25519_w3"
REPO="/Volumes/Works/rikkeisoft/w3-pr-tracking-tables"
LOG="$REPO/tools/refresh.log"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%F %T') ==="
  gh auth switch --user nguyenducbien-art >/dev/null 2>&1
  # Máy này là nguồn commit duy nhất → KHÔNG kéo commit về (no fetch/merge/reset trên repo tracking).
  python3 tools/fetch_build.py       data.json;         rc13=$?
  python3 tools/fetch_build_s12.py   data-s12.json;     rc12=$?
  python3 tools/fetch_build_s14.py   data-s14.json;     rcPR=$?
  python3 tools/fetch_screens_s14.py screens-s14.json;  rcSc=$?
  # rc: 0=đổi, 2=không đổi, khác=lỗi
  for pair in "s13:$rc13" "s12:$rc12" "s14:$rcPR" "screens:$rcSc"; do
    n=${pair%:*}; rc=${pair#*:}
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then echo "→ LỖI fetch $n (rc=$rc)"; exit 1; fi
  done
  if [ "$rc13" -eq 2 ] && [ "$rc12" -eq 2 ] && [ "$rcPR" -eq 2 ] && [ "$rcSc" -eq 2 ]; then
    echo "→ Không sprint nào đổi, khỏi push."; exit 0; fi

  # Dựng tree cho nhánh `data`. mktree cần entries sort theo tên (byte):
  #   'data-s12.json' < 'data-s14.json' < 'data.json' < 'screens-s14.json'
  B12=$(git hash-object -w data-s12.json)
  B14=$(git hash-object -w data-s14.json)
  B13=$(git hash-object -w data.json)
  BSC=$(git hash-object -w screens-s14.json)
  TREE=$(printf '100644 blob %s\tdata-s12.json\n100644 blob %s\tdata-s14.json\n100644 blob %s\tdata.json\n100644 blob %s\tscreens-s14.json\n' \
                "$B12" "$B14" "$B13" "$BSC" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="nguyenducbien-art@users.noreply.github.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh s12+s13+s14 (rc $rc12/$rc13/$rcPR/$rcSc) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (s12+s13+s14, KHÔNG build Pages). Web tươi ~5p (cache raw 300s)." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
