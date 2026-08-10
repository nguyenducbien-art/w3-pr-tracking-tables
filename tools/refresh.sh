#!/bin/bash
# Làm mới dữ liệu — CHỈ Sprint 15 (launchd cron mỗi 5' + chạy tay được).
#   1) fetch_build_s15.py → data-s15.json    (Sprint 15 PR, qua gh)
#   2) fetch_plan_s15.py  → s15-status.json  (Sprint 15 phân công: assignee 親/テスト実施 từ Backlog)
# Sprint 12/13/14 = ĐÔNG LẠNH (2026-08-10): KHÔNG refresh nữa, carry-forward blob cũ để trang
# index/s12/s14 vẫn đọc bản chốt cuối. Đẩy nhánh `data` bằng plumbing → KHÔNG build Pages.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME/.ssh/id_ed25519_w3"
REPO="/Volumes/Works/rikkeisoft/w3-pr-tracking-tables"
LOG="$REPO/tools/refresh.log"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%F %T') ==="
  gh auth switch --user nguyenducbien-art >/dev/null 2>&1
  python3 tools/fetch_build_s15.py data-s15.json;   rc15=$?
  python3 tools/fetch_plan_s15.py  s15-status.json; rcPl=$?
  # rc: 0=đổi, 2=không đổi, khác=lỗi
  for pair in "s15:$rc15" "plan15:$rcPl"; do
    n=${pair%:*}; rc=${pair#*:}
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then echo "→ LỖI fetch $n (rc=$rc)"; exit 1; fi
  done
  if [ "$rc15" -eq 2 ] && [ "$rcPl" -eq 2 ]; then echo "→ s15 không đổi, khỏi push."; exit 0; fi

  # Tree nhánh `data`: s15 (mới) + 4 file ĐÔNG LẠNH carry-forward từ refs/heads/data.
  # sort byte: 'data-s12' < 'data-s14' < 'data-s15' < 'data.json' < 's15-status' < 'screens-s14'
  B15=$(git hash-object -w data-s15.json)
  BPL=$(git hash-object -w s15-status.json)
  F12=$(git rev-parse refs/heads/data:data-s12.json)      # frozen
  F14=$(git rev-parse refs/heads/data:data-s14.json)      # frozen
  F13=$(git rev-parse refs/heads/data:data.json)          # frozen (s13)
  FSC=$(git rev-parse refs/heads/data:screens-s14.json)   # frozen (s14 screens)
  TREE=$(printf '100644 blob %s\tdata-s12.json\n100644 blob %s\tdata-s14.json\n100644 blob %s\tdata-s15.json\n100644 blob %s\tdata.json\n100644 blob %s\ts15-status.json\n100644 blob %s\tscreens-s14.json\n' \
                "$F12" "$F14" "$B15" "$F13" "$BPL" "$FSC" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="nguyenducbien-art@users.noreply.github.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh s15 only (PR rc=$rc15, plan rc=$rcPl) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (chỉ s15, KHÔNG build Pages). Web tươi ~5p (cache raw 300s)." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
