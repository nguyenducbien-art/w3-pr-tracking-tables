#!/bin/bash
# Làm mới dữ liệu PR-tracking (launchd cron mỗi 5' + chạy tay được).
# LỊCH LÀM MỚI (từ 2026-09-22, user yêu cầu bật cron cho 14/15/17/18):
#   - Sprint 18 (active)  → data-s18.json                                  MỖI TICK (5')
#   - Sprint 17           → data-s17.json                                  mỗi OLD_EVERY_MIN (30')
#   - Sprint 15+16        → data-s15 + s15-status (Backlog) + routes-s15   mỗi OLD_EVERY_MIN (30')
#   - Sprint 14           → data-s14 + screens-s14 (git r20260727)         mỗi OLD_EVERY_MIN (30')
#   Vì sao 14/15/17 không chạy mỗi tick: 3 sprint này ~470 lời gọi GraphQL/lượt (s18 vài chục) và ~10'/lượt
#   → mỗi tick sẽ ăn ~3000/giờ = 60% hạn mức 5000/giờ DÙNG CHUNG với mọi phiên gh khác + s18 chậm còn 10'.
#   Mốc lần chạy OK gần nhất: tools/.last_s14|s15|s17 (gitignored; xoá file = ép chạy ở tick sau).
#   Cờ chạy tay: REFRESH_Sxx=1 ép chạy ngay · REFRESH_Sxx=0 tắt hẳn (đông lạnh) · không đặt = theo lịch 30'.
# ĐÔNG LẠNH: Sprint 12 (data-s12.json) + Sprint 13 (data.json) từ 2026-08-11 — KHÔNG refresh.
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
  # Sprint 14/15/17 theo lịch OLD_EVERY_MIN (xem đầu file); không chạy lượt này → rc=2 (bỏ qua).
  OLD_EVERY_MIN=30
  due() {   # $1 = s14|s15|s17 → đến hạn khi chưa có mốc hoặc mốc cũ hơn OLD_EVERY_MIN phút
    [ ! -f "tools/.last_$1" ] || [ -n "$(find "tools/.last_$1" -mmin +$((OLD_EVERY_MIN - 1)))" ]
  }
  mark() {  # chỉ ghi mốc khi fetch OK (rc 0/2) → fetch lỗi thì tick sau thử lại
    { [ "$2" -eq 0 ] || [ "$2" -eq 2 ]; } && touch "tools/.last_$1"
  }
  RUN_S17=${REFRESH_S17:-$(due s17 && echo 1 || echo 0)}
  RUN_S15=${REFRESH_S15:-$(due s15 && echo 1 || echo 0)}
  RUN_S14=${REFRESH_S14:-$(due s14 && echo 1 || echo 0)}
  echo "→ lượt này: s18 · s17=$RUN_S17 · s15=$RUN_S15 · s14=$RUN_S14"
  rc17=2; rc15=2; rcPl=2; rcRt=2; rc14=2; rcSc=2
  if [ "$RUN_S17" = "1" ]; then
    python3 tools/fetch_build_s17.py   data-s17.json;     rc17=$?; mark s17 $rc17
  fi
  if [ "$RUN_S15" = "1" ]; then
    python3 tools/fetch_build_s15.py   data-s15.json;     rc15=$?; mark s15 $rc15
    python3 tools/fetch_plan_s15.py    s15-status.json;   rcPl=$?
    python3 tools/fetch_routes_s15.py  routes-s15.json;   rcRt=$?
  fi
  if [ "$RUN_S14" = "1" ]; then
    python3 tools/fetch_build_s14.py   data-s14.json;     rc14=$?; mark s14 $rc14
    python3 tools/fetch_screens_s14.py screens-s14.json;  rcSc=$?
  fi
  # rc: 0=đổi, 2=không đổi, khác=lỗi.
  # QUAN TRỌNG: fetch lỗi (rc=1) KHÔNG chặn push nữa. Mỗi fetch script khi lỗi KHÔNG ghi đè file
  # output → file trên đĩa vẫn là bản TỐT lần trước → carry-forward. Chỉ cảnh báo.
  # (Bug cũ: 1 fetch ssh-timeout → exit 1 → bỏ qua push cả s15 đã fetch thành công → web đứng.)
  changed=0
  for pair in "s18:$rc18" "s17:$rc17" "s15:$rc15" "plan15:$rcPl" "routes15:$rcRt" "s14:$rc14" "screens14:$rcSc"; do
    n=${pair%:*}; rc=${pair#*:}
    if [ "$rc" -eq 0 ]; then changed=1
    elif [ "$rc" -ne 2 ]; then echo "→ CẢNH BÁO fetch $n lỗi (rc=$rc) — giữ bản cũ trên đĩa, vẫn push phần khác"; fi
  done
  if [ "$changed" -eq 0 ]; then echo "→ Không file nào đổi (hoặc chỉ lỗi tạm) — khỏi push."; exit 0; fi

  # Dựng tree cho nhánh `data`. mktree cần entries sort theo tên (byte):
  #   'data-s12' < 'data-s14' < 'data-s15' < 'data-s17' < 'data-s18' < 'data.json' < 'routes-s15' < 's15-status' < 'screens-s14'
  #   ('-' = 0x2D < '.' = 0x2E → mọi 'data-*' đứng trước 'data.json')
  # Blob từng file: đã fetch + OK (rc 0/2) → file local vừa fetch; còn lại (đông lạnh, hoặc fetch LỖI)
  # → blob đang có trên nhánh data. KHÔNG lấy file local khi fetch lỗi: file local của sprint đông lạnh
  # lâu có thể CŨ HƠN nhánh data → push lùi dữ liệu.
  blob() {  # $1=file  $2=rc  $3=đã fetch (1/0)
    if [ "$3" = "1" ] && { [ "$2" -eq 0 ] || [ "$2" -eq 2 ]; }; then git hash-object -w "$1"
    else git rev-parse "refs/heads/data:$1"; fi
  }
  B18=$(blob data-s18.json    "$rc18" 1)                        # active (Sprint 18)
  B17=$(blob data-s17.json    "$rc17" "$RUN_S17")      # Sprint 17
  B15=$(blob data-s15.json    "$rc15" "$RUN_S15")      # Sprint 15+16
  BPL=$(blob s15-status.json  "$rcPl" "$RUN_S15")      # phân công S15 — Backlog
  BRT=$(blob routes-s15.json  "$rcRt" "$RUN_S15")      # route React S15
  B14=$(blob data-s14.json    "$rc14" "$RUN_S14")      # Sprint 14
  BSC=$(blob screens-s14.json "$rcSc" "$RUN_S14")      # Sprint 14 screen list
  B12=$(git rev-parse refs/heads/data:data-s12.json)     # frozen (Sprint 12)
  B13=$(git rev-parse refs/heads/data:data.json)          # frozen (Sprint 13)
  TREE=$(printf '100644 blob %s\tdata-s12.json\n100644 blob %s\tdata-s14.json\n100644 blob %s\tdata-s15.json\n100644 blob %s\tdata-s17.json\n100644 blob %s\tdata-s18.json\n100644 blob %s\tdata.json\n100644 blob %s\troutes-s15.json\n100644 blob %s\ts15-status.json\n100644 blob %s\tscreens-s14.json\n' \
                "$B12" "$B14" "$B15" "$B17" "$B18" "$B13" "$BRT" "$BPL" "$BSC" | git mktree)
  PARENT=$(git rev-parse refs/heads/data)
  COMMIT=$(git -c user.name="biennguyen" -c user.email="nguyenducbien-art@users.noreply.github.com" \
           commit-tree "$TREE" -p "$PARENT" -m "auto-refresh (rc s18=$rc18 s17=$rc17 s15=$rc15/$rcPl/$rcRt s14=$rc14/$rcSc) $(date '+%F %H:%M')")
  git update-ref refs/heads/data "$COMMIT"
  git push -q origin data 2>/dev/null \
    && echo "→ Đã push nhánh data (s18 + S17=$RUN_S17 S15=$RUN_S15 S14=$RUN_S14; KHÔNG build Pages). Web tươi ~5p." \
    || echo "→ push FAIL (kiểm tra tay)"
} > >(tee -a "$LOG") 2>&1
