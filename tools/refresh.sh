#!/bin/bash
# Làm mới dữ liệu PR-tracking (launchd cron mỗi 5' + chạy tay được).
# REFRESH — CHỈ Sprint 15 (sprint đang active):
#   - fetch_build_s15.py    → data-s15.json     (Sprint 15, PR qua gh)
#   - fetch_plan_s15.py     → s15-status.json   (Sprint 15 phân công — Backlog assignee)
#   - fetch_routes_s15.py   → routes-s15.json   (Sprint 15 route React per-sprint — git nhánh per-sprint)
# ĐÔNG LẠNH: Sprint 12 (data-s12.json) + Sprint 13 (data.json) từ 2026-08-11,
#            Sprint 14 (data-s14.json + screens-s14.json) từ 2026-08-25 — KHÔNG refresh nữa
#   → carry-forward blob cũ từ refs/heads/data để trang s12/index/s14 vẫn đọc bản chốt cuối.
# Đẩy vào nhánh `data` bằng git plumbing → KHÔNG checkout, KHÔNG build Pages → không chạm rate-limit.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# git fetch repo code (private, SSH host-alias github-w3, key không passphrase) chạy được non-interactive:
# ConnectTimeout=20 để ssh treo (máy thrash / mạng chập) fail nhanh thay vì chờ ~2' TCP timeout.
# Các fetch script dùng os.environ.setdefault → kế thừa đúng biến này (không tự override).
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=20 -o ServerAliveInterval=10 -o ServerAliveCountMax=2 -i $HOME/.ssh/id_ed25519_w3"
REPO="/Volumes/Works/rikkeisoft/w3-pr-tracking-tables"
LOG="$REPO/tools/refresh.log"
cd "$REPO" || exit 1
{
  echo "=== $(date '+%F %T') ==="
  gh auth switch --user nguyenducbien-art >/dev/null 2>&1
  # Máy này là nguồn commit duy nhất → KHÔNG kéo commit về (no fetch/merge/reset trên repo tracking).
  python3 tools/fetch_build_s15.py   data-s15.json;     rc15=$?
  python3 tools/fetch_plan_s15.py    s15-status.json;   rcPl=$?
  python3 tools/fetch_routes_s15.py  routes-s15.json;   rcRt=$?
  # rc: 0=đổi, 2=không đổi, khác=lỗi.
  # QUAN TRỌNG: fetch lỗi (rc=1) KHÔNG chặn push nữa. Mỗi fetch script khi lỗi KHÔNG ghi đè file
  # output → file trên đĩa vẫn là bản TỐT lần trước → carry-forward. Chỉ cảnh báo.
  # (Bug cũ: 1 fetch ssh-timeout → exit 1 → bỏ qua push cả s15 đã fetch thành công → web đứng.)
  changed=0
  for pair in "s15:$rc15" "plan15:$rcPl" "routes15:$rcRt"; do
    n=${pair%:*}; rc=${pair#*:}
    if [ "$rc" -eq 0 ]; then changed=1
    elif [ "$rc" -ne 2 ]; then echo "→ CẢNH BÁO fetch $n lỗi (rc=$rc) — giữ bản cũ trên đĩa, vẫn push phần khác"; fi
  done
  if [ "$changed" -eq 0 ]; then echo "→ Không file nào đổi (hoặc chỉ lỗi tạm) — khỏi push."; exit 0; fi

  # Dựng tree cho nhánh `data`. mktree cần entries sort theo tên (byte):
  #   'data-s12' < 'data-s14' < 'data-s15' < 'data.json' < 'routes-s15' < 's15-status' < 'screens-s14'
  # s12 + s13 + s14 = ĐÔNG LẠNH → carry-forward blob cũ từ refs/heads/data.
  B15=$(git hash-object -w data-s15.json)
  BRT=$(git hash-object -w routes-s15.json)
  BPL=$(git hash-object -w s15-status.json)
  B12=$(git rev-parse refs/heads/data:data-s12.json)     # frozen (Sprint 12)
  B13=$(git rev-parse refs/heads/data:data.json)          # frozen (Sprint 13)
  B14=$(git rev-parse refs/heads/data:data-s14.json)      # frozen (Sprint 14)
  BSC=$(git rev-parse refs/heads/data:screens-s14.json)   # frozen (Sprint 14 screen list)
  TREE=$(printf '100644 blob %s\tdata-s12.json\n100644 blob %s\tdata-s14.json\n100644 blob %s\tdata-s15.json\n100644 blob %s\tdata.json\n100644 blob %s\troutes-s15.json\n100644 blob %s\ts15-status.json\n100644 blob %s\tscreens-s14.json\n' \
                "$B12" "$B14" "$B15" "$B13" "$BRT" "$BPL" "$BSC" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="nguyenducbien-art@users.noreply.github.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh s15 only (rc s15=$rc15 plan=$rcPl routes=$rcRt) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (chỉ s15; s12/s13/s14 đông lạnh, KHÔNG build Pages). Web tươi ~5p." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
