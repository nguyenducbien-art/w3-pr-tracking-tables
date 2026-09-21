#!/bin/bash
# Làm mới dữ liệu PR-tracking (launchd cron mỗi 5' + chạy tay được).
# REFRESH — CHỈ Sprint 18 (active, từ 21/09/2026):
#   - fetch_build_s18.py    → data-s18.json     (Sprint 18 = PR created >= 21/09, qua gh)
# ĐÔNG LẠNH: Sprint 17 (data-s17.json, PR 07/09–20/09) từ 2026-09-21 09:5x theo yêu cầu user
#            (lúc đông lạnh còn ~21 PR OPEN → page s17 giữ trạng thái chốt, không cập nhật merge/review nữa)
#   → chạy tay `REFRESH_S17=1 tools/refresh.sh` nếu cần fetch lại s17.
#            Sprint 12 (data-s12.json) + Sprint 13 (data.json) từ 2026-08-11,
#            Sprint 14 (data-s14.json + screens-s14.json) từ 2026-08-25,
#            Sprint 15+16 (data-s15.json + s15-status.json + routes-s15.json) từ 2026-09-21
#            (sprint chốt 06/09; data-s15.json đã fetch lại 1 lần với chặn trên UNTIL=06/09) — KHÔNG refresh nữa
#   → chạy tay `REFRESH_S15=1 tools/refresh.sh` nếu cần fetch lại s15 (vd đổi mốc cắt).
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
  python3 tools/fetch_build_s18.py   data-s18.json;     rc18=$?
  # s17 đông lạnh (21/09); REFRESH_S17=1 (chạy tay) thì fetch lại.
  if [ "${REFRESH_S17:-0}" = "1" ]; then
    python3 tools/fetch_build_s17.py data-s17.json;     rc17=$?
  else
    rc17=2
  fi
  # s15 đông lạnh; REFRESH_S15=1 (chạy tay) thì fetch lại — dùng khi đổi luật/mốc cắt của page s15.
  if [ "${REFRESH_S15:-0}" = "1" ]; then
    python3 tools/fetch_build_s15.py data-s15.json;     rc15=$?
  else
    rc15=2
  fi
  # rc: 0=đổi, 2=không đổi, khác=lỗi.
  # QUAN TRỌNG: fetch lỗi (rc=1) KHÔNG chặn push nữa. Mỗi fetch script khi lỗi KHÔNG ghi đè file
  # output → file trên đĩa vẫn là bản TỐT lần trước → carry-forward. Chỉ cảnh báo.
  # (Bug cũ: 1 fetch ssh-timeout → exit 1 → bỏ qua push cả s15 đã fetch thành công → web đứng.)
  changed=0
  for pair in "s18:$rc18" "s17:$rc17" "s15:$rc15"; do
    n=${pair%:*}; rc=${pair#*:}
    if [ "$rc" -eq 0 ]; then changed=1
    elif [ "$rc" -ne 2 ]; then echo "→ CẢNH BÁO fetch $n lỗi (rc=$rc) — giữ bản cũ trên đĩa, vẫn push phần khác"; fi
  done
  if [ "$changed" -eq 0 ]; then echo "→ Không file nào đổi (hoặc chỉ lỗi tạm) — khỏi push."; exit 0; fi

  # Dựng tree cho nhánh `data`. mktree cần entries sort theo tên (byte):
  #   'data-s12' < 'data-s14' < 'data-s15' < 'data-s17' < 'data-s18' < 'data.json' < 'routes-s15' < 's15-status' < 'screens-s14'
  #   ('-' = 0x2D < '.' = 0x2E → mọi 'data-*' đứng trước 'data.json')
  # s12 + s13 + s14 + s15 + s17 = ĐÔNG LẠNH → carry-forward blob cũ từ refs/heads/data.
  B18=$(git hash-object -w data-s18.json)
  if [ "${REFRESH_S17:-0}" = "1" ]; then
    B17=$(git hash-object -w data-s17.json)               # fetch lại (chạy tay)
  else
    B17=$(git rev-parse refs/heads/data:data-s17.json)     # frozen (Sprint 17)
  fi
  if [ "${REFRESH_S15:-0}" = "1" ]; then
    B15=$(git hash-object -w data-s15.json)               # fetch lại (chạy tay)
  else
    B15=$(git rev-parse refs/heads/data:data-s15.json)     # frozen (Sprint 15+16)
  fi
  BRT=$(git rev-parse refs/heads/data:routes-s15.json)     # frozen (route React S15)
  BPL=$(git rev-parse refs/heads/data:s15-status.json)     # frozen (phân công S15 — Backlog)
  B12=$(git rev-parse refs/heads/data:data-s12.json)     # frozen (Sprint 12)
  B13=$(git rev-parse refs/heads/data:data.json)          # frozen (Sprint 13)
  B14=$(git rev-parse refs/heads/data:data-s14.json)      # frozen (Sprint 14)
  BSC=$(git rev-parse refs/heads/data:screens-s14.json)   # frozen (Sprint 14 screen list)
  TREE=$(printf '100644 blob %s\tdata-s12.json\n100644 blob %s\tdata-s14.json\n100644 blob %s\tdata-s15.json\n100644 blob %s\tdata-s17.json\n100644 blob %s\tdata-s18.json\n100644 blob %s\tdata.json\n100644 blob %s\troutes-s15.json\n100644 blob %s\ts15-status.json\n100644 blob %s\tscreens-s14.json\n' \
                "$B12" "$B14" "$B15" "$B17" "$B18" "$B13" "$BRT" "$BPL" "$BSC" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="nguyenducbien-art@users.noreply.github.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh s18 only (rc s18=$rc18 s17=$rc17 s15=$rc15) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (chỉ s18; s12/s13/s14/s15/s17 đông lạnh, KHÔNG build Pages). Web tươi ~5p." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
