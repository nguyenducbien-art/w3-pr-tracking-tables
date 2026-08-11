#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Đọc route React của các màn Sprint 15 TRỰC TIẾP từ code nhánh deploy per-sprint
mimosa/frontend/develop/per-sprint (repo dialog-inc/w3package_v2) → routes-s15.json.
(per-sprint = đúng nhánh đang deploy lên mimosa-stg-react-per-sprint → route khớp URL thật.)

route = path folder `(protected)/<route>/_lib/constants.ts` khai báo
        `export const SCREEN_ID = (SCREEN_IDS|MODAL_SCREEN_IDS).<X>` với X map ra sid
        (screen-ids.ts). URL hiển thị = base per-sprint + route (client-side, build_s15.py).
        → route lấy từ chính path folder (đúng mọi domain, không đoán tên).
Chỉ xuất map {sid: route} cho màn ĐÃ migrate; màn chưa có folder → không có key
→ bảng phân công hiển thị '—'. Tự cập nhật khi thêm màn migrate vào r20260810.

Chạy được từ cron nền: fetch qua SSH host-alias github-w3 (key không passphrase). Chỉ đọc
(fetch vào ref RIÊNG + git show/grep/rev-parse) — KHÔNG đụng working tree _base.

Exit: 0 = có đổi (đã ghi) · 2 = không đổi (bỏ push) · 1 = lỗi.
Usage: python3 fetch_routes_s15.py [output.json]
"""
import json, re, subprocess, sys, datetime, os

CODE_REPO = "/Volumes/Works/rikkeisoft/w3package_v2_mimosa_upgrade_frontend_develop_base"
BRANCH    = "mimosa/frontend/develop/per-sprint"
LOCAL_REF = "refs/screens-cron/per-sprint"   # ref riêng (tránh race FETCH_HEAD dùng chung _base)
IDS_TS    = "frontend/packages/config/screen-ids.ts"
APP_ROOT  = "frontend/apps/web/src/app/(protected)"
REACT_BASE = "https://mimosa-stg-react-per-sprint.dialog-wms.com"
OUT = sys.argv[1] if len(sys.argv) > 1 else "routes-s15.json"

os.environ.setdefault(
    "GIT_SSH_COMMAND",
    "ssh -o BatchMode=yes -o IdentitiesOnly=yes -i %s" % os.path.expanduser("~/.ssh/id_ed25519_w3"))

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode not in (0, 1):   # git grep trả 1 khi không match (không phải lỗi)
        raise RuntimeError("cmd fail: %s\n%s" % (" ".join(args), r.stderr[:400]))
    return r.stdout

def git(*a):
    return run(["git", "-C", CODE_REPO] + list(a))

def investigate():
    git("fetch", "origin", "+%s:%s" % (BRANCH, LOCAL_REF))
    sha = git("rev-parse", LOCAL_REF).strip()
    # map SCREEN_IDS.<name> / MODAL_SCREEN_IDS.<name> -> sid (parse toàn bộ 'KEY: number')
    ids = git("show", "%s:%s" % (sha, IDS_TS))
    name2sid = {n: int(v) for n, v in re.findall(r"([A-Z0-9_]+)\s*:\s*(\d+)", ids)}
    # folder màn đã implement: khai báo SCREEN_ID chính + path → route
    grep = git("grep", "-n", "-E",
               r"export const SCREEN_ID = (SCREEN_IDS|MODAL_SCREEN_IDS)\.", sha, "--", APP_ROOT)
    sid2route = {}
    for line in grep.splitlines():
        mp = re.search(r"\(protected\)(/.*?)/_lib/constants\.ts", line)
        mn = re.search(r"(?:SCREEN_IDS|MODAL_SCREEN_IDS)\.(\w+)", line)
        if not (mp and mn) or mn.group(1) not in name2sid:
            continue
        # bỏ segment route-group '(...)' khỏi path (không phải segment URL)
        segs = [s for s in mp.group(1).split("/") if s and not (s.startswith("(") and s.endswith(")"))]
        sid2route[name2sid[mn.group(1)]] = "/" + "/".join(segs)
    # CHỐT CHẶN: detection rỗng = chắc chắn lỗi (git show/grep hỏng) — KHÔNG ghi đè bản tốt.
    if not name2sid or not sid2route:
        raise RuntimeError("detection RỖNG (name2sid=%d, sid2route=%d) @ %s — nghi git show/grep lỗi"
                           % (len(name2sid), len(sid2route), sha[:10]))
    return sha, sid2route

def main():
    sha, sid2route = investigate()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    routes = {str(sid): rt for sid, rt in sorted(sid2route.items())}
    data = {"updated": now, "tip": sha[:10], "branch": BRANCH, "base": REACT_BASE, "routes": routes}

    def core(d):   # dedup theo NỘI DUNG routes (bỏ updated + tip) → chỉ push khi map đổi
        return json.dumps(d.get("routes"), ensure_ascii=False, sort_keys=True)
    try:
        old = json.load(open(OUT))
        if core(old) == core(data):
            print("[fetch_routes] no change (tip=%s) — bỏ push" % sha[:10])
            sys.exit(2)
    except (FileNotFoundError, ValueError):
        pass

    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("[fetch_routes] %s | %d màn có route React | tip=%s @ %s"
          % (OUT, len(routes), sha[:10], now))

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("[fetch_routes] LỖI: %s" % e, file=sys.stderr)
        sys.exit(1)
