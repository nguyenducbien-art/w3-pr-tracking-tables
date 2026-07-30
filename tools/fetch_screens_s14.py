#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Điều tra tiến độ migrate 27 màn Sprint 14 TRỰC TIẾP từ code nhánh
mimosa/frontend/develop/r20260727 (repo dialog-inc/w3package_v2) → screens-s14.json.

Tự động phần ĐỘNG (trạng thái migrate + route thực) đọc từ code; phần TĨNH
(画面名 / ticket / PIC) là cấu hình cố định bên dưới — đổi PIC thì sửa CONFIG.

Cách suy ra trạng thái (khớp memory project_sprint14_screens):
  done = route trong tabUrlResolver.ts KHÔNG bị comment  +  folder (protected)<route> tồn tại
  wip  = chưa merge NHƯNG có feature branch mimosa/frontend/feature/ANGULAR_REPLACE-<ticket>
  todo = chưa merge, không có branch

Chạy được từ cron nền: fetch qua SSH host-alias github-w3 (key không passphrase),
KHÔNG cần ssh-agent. Chỉ đọc (fetch + git show/ls-tree/ls-remote) — không đụng
working tree hay branch của clone _base.

Exit: 0 = có đổi (đã ghi) · 2 = không đổi (bỏ push) · 1 = lỗi.
Usage: python3 fetch_screens_s14.py [output.json]
"""
import json, os, re, subprocess, sys, datetime

CODE_REPO = "/Volumes/Works/rikkeisoft/w3package_v2_mimosa_upgrade_frontend_develop_base"
BRANCH    = "mimosa/frontend/develop/r20260727"
RESOLVER  = "frontend/packages/libs/src/screen/tabUrlResolver.ts"
APP_ROOT  = "frontend/apps/web/src/app/(protected)"
OUT = sys.argv[1] if len(sys.argv) > 1 else "screens-s14.json"

# đảm bảo git fetch chạy được non-interactive dù cron không có agent
os.environ.setdefault(
    "GIT_SSH_COMMAND",
    "ssh -o BatchMode=yes -o IdentitiesOnly=yes -i %s" % os.path.expanduser("~/.ssh/id_ed25519_w3"))

# ---- CONFIG TĨNH: 27 màn (sid, 画面名, ticket-on-commit, PIC) ----
# PIC/画面名/ticket đổi rất hiếm; khi reassign PIC thì sửa ở đây.
CONFIG = [
  (252, "在庫_変更履歴一覧",             "547", "Khoa"),
  (254, "在庫_変更履歴明細",             "548", "Minh"),
  (261, "在庫_在庫追加",                 "549", "Khoa"),
  (265, "在庫_情報変更",                 "546", "Khoa"),
  (280, "移動_一覧",                     "789", "Đạt"),
  (282, "移動_明細",                     "571", "Minh"),
  (298, "移動_内容追加",                 "572", "Biên"),
  (303, "在庫変遷_商品別",               "553", "Minh"),
  (333, "セット品作成_一覧",             "583", "Khoa"),
  (335, "セット品作成_明細",             "584", "Khoa"),
  (342, "セット品作成_履歴一覧",         "587", "Biên"),
  (344, "セット品作成_履歴明細",         "588", "Hưng"),
  (353, "セット品作成_内容追加",         "585", "Khoa"),
  (362, "荷姿変更_一覧",                 "600", "Hưng"),
  (387, "直接入庫_一覧",                 "745", "Đạt"),
  (396, "直接入庫_履歴明細",             "562", "Hưng"),
  (402, "直接入庫_内容追加",             "563", "Hưng"),
  (471, "在庫_在庫出荷指示作成",         "550", "Khoa"),
  (518, "セット品作成_セット品候補一覧", "586", "Biên"),
  (638, "在庫出荷指示作成",             "741", "Đạt"),
  (640, "在庫断面_一覧",                 "551", "Minh"),
  (641, "在庫断面_明細",                 "552", "Minh"),
  (645, "在庫_全在庫一覧",               "543", "Đạt"),
  (690, "シリアル番号_追加・編集",       "607", "Minh"),
  (704, "在庫予測_出荷予測明細",         "557", "Hưng"),
  (705, "在庫予測_在庫予測一覧",         "555", "Minh"),
  (706, "在庫予測_在庫予測明細",         "556", "Hưng"),
]
PIC_ORDER = ["Khoa", "Đạt", "Biên", "Minh", "Hưng"]

# màn KHÔNG bao giờ là "màn migrate độc lập" (không có route riêng) → không tính wip
# dù có feature branch; note giải thích lý do.
STATUS_LOCK_TODO = {471}
NOTE_OVERRIDE = {
  471: "không có route riêng; chỉ dùng làm CONFIG_SCREEN_ID (nguồn grid columns) cho màn 638",
  705: "subnav / nguồn điều hướng của màn 706",
}

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("cmd fail: %s\n%s" % (" ".join(args), r.stderr[:400]))
    return r.stdout

def git(*a):
    return run(["git", "-C", CODE_REPO] + list(a))

def resolver_line(resolver, sid):
    for ln in resolver.splitlines():
        if re.search(r"\(%d\)" % sid, ln):
            return ln
    return None

def parse_line(ln):
    """(active, route) — active = dòng KHÔNG bị comment //; route = giá trị đích."""
    if ln is None:
        return (False, "")
    active = re.match(r"\s*//", ln) is None
    m = re.search(r"'[^']+'\s*:\s*'([^']+)'", ln)
    return (active, m.group(1) if m else "")

def note_for(sid, st, ticket):
    if sid in NOTE_OVERRIDE and st != "done":
        return NOTE_OVERRIDE[sid]
    if st == "wip":
        return "branch feature/ANGULAR_REPLACE-%s có code, chưa merge vào r" % ticket
    if st == "todo":
        return "chưa có code"
    return ""

def investigate():
    git("fetch", "origin", BRANCH)
    sha = git("rev-parse", "FETCH_HEAD").strip()
    resolver = git("show", "%s:%s" % (sha, RESOLVER))
    # toàn bộ path dưới (protected) — 1 lần, check prefix trong Python
    tree = git("ls-tree", "-r", "--name-only", sha, APP_ROOT)
    paths = tree.splitlines()
    def folder_exists(route):
        pfx = "%s%s/" % (APP_ROOT, route)
        return any(p.startswith(pfx) for p in paths)
    # feature branch theo ticket (1 call, non-interactive)
    lsr = git("ls-remote", "--heads", "origin")
    branch_tickets = set(re.findall(
        r"refs/heads/mimosa/frontend/feature/ANGULAR_REPLACE-(\d+)\b", lsr))

    screens = []
    for sid, name, ticket, pic in CONFIG:
        active, route = parse_line(resolver_line(resolver, sid))
        if active and folder_exists(route):
            st, rt = "done", route
        elif sid not in STATUS_LOCK_TODO and ticket in branch_tickets:
            st, rt = "wip", ""
        else:
            st, rt = "todo", ""
        screens.append({"sid": sid, "name": name, "route": rt, "ticket": ticket,
                        "pic": pic, "st": st, "note": note_for(sid, st, ticket)})
    return sha, screens

def main():
    sha, screens = investigate()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"updated": now, "tip": sha[:10], "branch": BRANCH,
            "picOrder": PIC_ORDER, "screens": screens}

    # dedup theo NỘI DUNG màn (bỏ updated + tip) → chỉ push khi trạng thái đổi
    def core(d):
        return json.dumps(d.get("screens"), ensure_ascii=False, sort_keys=True)
    try:
        old = json.load(open(OUT))
        if core(old) == core(data):
            print("[fetch_screens] no change (tip=%s) — bỏ push" % sha[:10])
            sys.exit(2)
    except (FileNotFoundError, ValueError):
        pass

    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    nd = sum(1 for s in screens if s["st"] == "done")
    nw = sum(1 for s in screens if s["st"] == "wip")
    nt = sum(1 for s in screens if s["st"] == "todo")
    print("[fetch_screens] %s | %d màn: done=%d wip=%d todo=%d | tip=%s @ %s"
          % (OUT, len(screens), nd, nw, nt, sha[:10], now))

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("[fetch_screens] LỖI: %s" % e, file=sys.stderr)
        sys.exit(1)
