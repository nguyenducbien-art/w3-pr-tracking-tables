#!/bin/bash
# Làm mới dữ liệu Sprint 14 (chạy bởi launchd cron mỗi 5' + chạy tay được).
#   1) fetch_build_s14.py    → data-s14.json     (PR tracking, qua gh)
#   2) fetch_screens_s14.py  → screens-s14.json  (điều tra tiến độ migrate 27 màn từ code r20260727)
# Đẩy CẢ 2 file (+ data.json Sprint 13 ĐÔNG LẠNH, không refresh nữa) vào nhánh `data`
# bằng git plumbing → KHÔNG checkout, KHÔNG build Pages, không chạm rate-limit.
# (Cron Sprint 13 đã bỏ 2026-07-30 — data.json giữ nguyên bản chốt cuối để trang s13 không vỡ.)
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
  python3 tools/fetch_build_s14.py   data-s14.json;    rcPR=$?
  python3 tools/fetch_screens_s14.py screens-s14.json; rcSc=$?
  # rc: 0=đổi, 2=không đổi, khác=lỗi
  if [ "$rcPR" -ne 0 ] && [ "$rcPR" -ne 2 ]; then echo "→ LỖI fetch_build_s14 (rc=$rcPR)"; exit 1; fi
  if [ "$rcSc" -ne 0 ] && [ "$rcSc" -ne 2 ]; then echo "→ LỖI fetch_screens_s14 (rc=$rcSc)"; exit 1; fi
  if [ "$rcPR" -eq 2 ] && [ "$rcSc" -eq 2 ]; then echo "→ PR + screens đều không đổi, khỏi push."; exit 0; fi

  # Dựng tree cho nhánh `data`. mktree cần entries sort theo tên (byte):
  #   'data-s14.json'(data-) < 'data.json'(data.) < 'screens-s14.json'(s…)
  B_S14=$(git hash-object -w data-s14.json)
  B_SCR=$(git hash-object -w screens-s14.json)
  B_D13=$(git rev-parse refs/heads/data:data.json 2>/dev/null)   # Sprint 13 đông lạnh (carry-forward)
  if [ -n "$B_D13" ]; then
    TREE=$(printf '100644 blob %s\tdata-s14.json\n100644 blob %s\tdata.json\n100644 blob %s\tscreens-s14.json\n' \
                  "$B_S14" "$B_D13" "$B_SCR" | git mktree)
  else
    TREE=$(printf '100644 blob %s\tdata-s14.json\n100644 blob %s\tscreens-s14.json\n' \
                  "$B_S14" "$B_SCR" | git mktree)
  fi
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="biennguyen131311@gmail.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh s14 (PR rc=$rcPR, screens rc=$rcSc) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (s14 PR + screens, KHÔNG build Pages). Web tươi ~5p (cache raw 300s)." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
