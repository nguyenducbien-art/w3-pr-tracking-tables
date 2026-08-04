#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Điều tra tiến độ migrate các màn Sprint 14 TRỰC TIẾP từ code nhánh
mimosa/frontend/develop/r20260727 (repo dialog-inc/w3package_v2) → screens-s14.json.

DANH SÁCH MÀN (sid + 画面名 + ticket + PIC) = milestone "Sprint 14" trên Backlog,
category 画面実装 (nguồn CHUẨN, 2026-07-30: 43 task). Reassign PIC / thêm-bớt màn:
  cập nhật CONFIG bên dưới (query lại Backlog milestoneId=1691970, category 2230051).
  → ticket = issueKey Backlog (KHÁC số ticket trên commit/PR — 1 màn 2 hệ số).

TRẠNG THÁI (động, đọc code):
  done = có folder màn thật trên r20260727 — tồn tại `(protected)/<route>/_lib/constants.ts`
         khai báo `export const SCREEN_ID = SCREEN_IDS.<X>` với X map ra sid (screen-ids.ts).
         → route hiển thị lấy từ chính path folder (đúng mọi domain, không đoán tên route).
  chưa = chưa có folder đó trên r20260727 (đang làm ở feature branch hoặc chưa bắt đầu).
Detection dựa SCREEN_ID-folder (KHÔNG dựa route comment ở tabUrlResolver) nên chắc chắn:
bắt được cả màn không có route riêng trong resolver (vd 棚卸系).

Chạy được từ cron nền: fetch qua SSH host-alias github-w3 (key không passphrase), KHÔNG
cần ssh-agent. Chỉ đọc (fetch + git show/grep/rev-parse) — không đụng working tree _base.

Exit: 0 = có đổi (đã ghi) · 2 = không đổi (bỏ push) · 1 = lỗi.
Usage: python3 fetch_screens_s14.py [output.json]
"""
import json, os, re, subprocess, sys, datetime, urllib.request, urllib.parse

CODE_REPO = "/Volumes/Works/rikkeisoft/w3package_v2_mimosa_upgrade_frontend_develop_base"
BRANCH    = "mimosa/frontend/develop/r20260727"
LOCAL_REF = "refs/screens-cron/r20260727"   # ref riêng của script (tránh race FETCH_HEAD dùng chung)
IDS_TS    = "frontend/packages/config/screen-ids.ts"
APP_ROOT  = "frontend/apps/web/src/app/(protected)"
OUT = sys.argv[1] if len(sys.argv) > 1 else "screens-s14.json"

# ---- Backlog 結合テスト実施 (integration test) — cột người test + trạng thái test ----
# Query REST API tasks 'テスト実施' (issueType 4092260) trong milestone Sprint 14 (1691970).
# API key đọc từ env BACKLOG_API_KEY hoặc file tools/.backlog_key (GITIGNORED — Claude không thấy).
# Best-effort: thiếu key / API lỗi → bỏ cột test (KHÔNG làm hỏng detection migrate).
BACKLOG_HOST   = "dialog-inc.backlog.com"
BL_MILESTONE   = 1691970    # milestone "Sprint 14"
BL_TEST_TYPE   = 4092260    # タスク(テスト実施) = 結合テスト実施
TESTER = {"nguyenanhkhoa":"Khoa","nguyenducbien":"Biên","nguyennhatminh":"Minh",
          "phambaohung":"Hưng","phamtiendat":"Đạt","phamngocson":"Sơn","trinhduybong":"Bồn"}
TEST_STATE = {"Resolved":"done","Closed":"done","In Progress":"wip","Open":"todo"}

def backlog_key():
    k = os.environ.get("BACKLOG_API_KEY")
    if k and k.strip():
        return k.strip()
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backlog_key")
    try:
        k = open(p).read().strip()
        return k or None
    except OSError:
        return None

def load_prev_tests(path):
    """test/tester từ screens-s14.json lần trước — dùng khi Backlog lỗi, tránh xoá cột test."""
    try:
        old = json.load(open(path))
        return {s["sid"]: {"test": s.get("test"), "tester": s.get("tester")}
                for s in old.get("screens", []) if s.get("test")}
    except (OSError, ValueError):
        return {}

def fetch_tests():
    """screen_id -> {test, tester}.
       {}   = KHÔNG có key (cột test tắt có chủ đích → test=None).
       None = có key NHƯNG Backlog lỗi (caller GIỮ test data lần trước, KHÔNG xoá)."""
    key = backlog_key()
    if not key:
        print("[fetch_screens] (không có Backlog API key → bỏ dữ liệu cột test)", file=sys.stderr)
        return {}
    q = urllib.parse.urlencode({"apiKey": key, "milestoneId[]": BL_MILESTONE,
                                "issueTypeId[]": BL_TEST_TYPE, "count": 100})
    url = "https://%s/api/v2/issues?%s" % (BACKLOG_HOST, q)
    issues = None
    for attempt in range(3):   # retry: Backlog trả 43 issue có thể chậm
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                issues = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            print("[fetch_screens] (Backlog thử %d/3 lỗi: %s)" % (attempt + 1, e), file=sys.stderr)
    if issues is None:
        return None   # → giữ test data cũ
    out = {}
    for it in issues:
        m = re.search(r"screen_id=(\d+)", it.get("summary", ""))
        if not m:
            continue
        st = TEST_STATE.get((it.get("status") or {}).get("name"), "todo")
        a = it.get("assignee") or {}
        uid = ((a.get("nulabAccount") or {}).get("uniqueId") or "")
        tester = next((v for k, v in TESTER.items() if uid.startswith(k)), a.get("name", "?"))
        out[int(m.group(1))] = {"test": st, "tester": tester}
    return out

os.environ.setdefault(
    "GIT_SSH_COMMAND",
    "ssh -o BatchMode=yes -o IdentitiesOnly=yes -i %s" % os.path.expanduser("~/.ssh/id_ed25519_w3"))

# ---- CONFIG: 43 màn Sprint 14 (sid, 画面名, ticket=Backlog issueKey, PIC) — snapshot Backlog 2026-07-30 ----
CONFIG = [
  (252, "在庫_変更履歴一覧",             "697",  "Khoa"),
  (254, "在庫_変更履歴明細",             "701",  "Minh"),
  (261, "在庫_在庫追加",                 "705",  "Khoa"),
  (265, "在庫_情報変更",                 "693",  "Minh"),
  (280, "移動_一覧",                     "789",  "Đạt"),
  (282, "移動_明細",                     "793",  "Minh"),
  (298, "移動_内容追加",                 "797",  "Biên"),
  (303, "在庫変遷_商品別",               "721",  "Minh"),
  (306, "棚卸_対象在庫一覧",             "809",  "Hưng"),
  (311, "棚卸_調査一覧",                 "813",  "Hưng"),
  (313, "棚卸_調査明細",                 "817",  "Minh"),
  (318, "棚卸_履歴一覧",                 "829",  "Minh"),
  (320, "棚卸_履歴明細",                 "833",  "Khoa"),
  (327, "棚卸_調査結果登録",             "821",  "Khoa"),
  (333, "セット品作成_一覧",             "841",  "Khoa"),
  (335, "セット品作成_明細",             "845",  "Khoa"),
  (342, "セット品作成_履歴一覧",         "857",  "Biên"),
  (344, "セット品作成_履歴明細",         "861",  "Hưng"),
  (353, "セット品作成_内容追加",         "849",  "Khoa"),
  (362, "荷姿変更_一覧",                 "909",  "Hưng"),
  (373, "荷姿変更_履歴明細",             "929",  "Khoa"),
  (387, "直接入庫_一覧",                 "745",  "Đạt"),
  (396, "直接入庫_履歴明細",             "757",  "Hưng"),
  (402, "直接入庫_内容追加",             "761",  "Hưng"),
  (446, "画面設定_ステータス別設定",     "1089", "Đạt"),
  (518, "セット品作成_セット品候補一覧", "853",  "Biên"),
  (622, "セット品崩し_一覧",             "865",  "Hưng"),
  (623, "セット品崩し_明細",             "873",  "Đạt"),
  (624, "セット品崩し_履歴一覧",         "881",  "Đạt"),
  (625, "セット品崩し_履歴明細",         "885",  "Khoa"),
  (626, "セット品崩し_内容追加",         "877",  "Đạt"),
  (627, "セット品崩し_セット品候補一覧", "869",  "Hưng"),
  (634, "棚卸予定外在庫_内容追加",       "837",  "Khoa"),
  (638, "在庫出荷指示作成",             "741",  "Đạt"),
  (640, "在庫断面_一覧",                 "713",  "Minh"),
  (641, "在庫断面_明細",                 "717",  "Minh"),
  (645, "在庫_全在庫一覧",               "681",  "Đạt"),
  (685, "シリアル番号_一覧",             "933",  "Biên"),
  (690, "シリアル番号_追加・編集",       "937",  "Hưng"),
  (702, "作業履歴_作業者別",             "941",  "Hưng"),
  (704, "在庫予測_出荷予測明細",         "737",  "Hưng"),
  (705, "在庫予測_在庫予測一覧",         "729",  "Minh"),
  (706, "在庫予測_在庫予測明細",         "733",  "Hưng"),
]
PIC_ORDER = ["Khoa", "Đạt", "Biên", "Minh", "Hưng"]
# ghi chú cho vài màn chưa migrate (chỉ hiện khi status != done)
NOTE_TODO = {
  705: "subnav / nguồn điều hướng của màn 706",
  634: "sub-screen thuộc 棚卸予定外在庫",
}

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode not in (0, 1):   # git grep trả 1 khi không match (không phải lỗi)
        raise RuntimeError("cmd fail: %s\n%s" % (" ".join(args), r.stderr[:400]))
    return r.stdout

def git(*a):
    return run(["git", "-C", CODE_REPO] + list(a))

def investigate():
    # Fetch vào REF RIÊNG (không dùng FETCH_HEAD chung) — _base là workspace dùng chung,
    # process khác fetch xen vào sẽ đè FETCH_HEAD → đọc nhầm tree → detection sai.
    # '+' = force (phòng nhánh r bị force-push). Ref này chỉ script này ghi.
    git("fetch", "origin", "+%s:%s" % (BRANCH, LOCAL_REF))
    sha = git("rev-parse", LOCAL_REF).strip()
    # map SCREEN_IDS.<name> -> sid
    ids = git("show", "%s:%s" % (sha, IDS_TS))
    m = re.search(r"SCREEN_IDS\s*=\s*\{(.*?)\}\s*as const", ids, re.S)
    name2sid = {n: int(v) for n, v in re.findall(r"(\w+)\s*:\s*(\d+)", m.group(1))} if m else {}
    # các folder màn đã implement: khai báo SCREEN_ID chính + path → route
    grep = git("grep", "-n", "-E", r"export const SCREEN_ID = SCREEN_IDS\.", sha, "--", APP_ROOT)
    sid2route = {}
    for line in grep.splitlines():
        mp = re.search(r"\(protected\)(/.*?)/_lib/constants\.ts", line)
        mn = re.search(r"SCREEN_IDS\.(\w+)", line)
        if mp and mn and mn.group(1) in name2sid:
            sid2route[name2sid[mn.group(1)]] = mp.group(1)
    # CHỐT CHẶN: detection rỗng = chắc chắn lỗi (git show/grep hỏng, tree đọc dở) — KHÔNG để
    # ghi dữ liệu "toàn chưa" đè lên bản tốt. Sprint luôn có màn done → sid2route rỗng ⇒ raise.
    if not name2sid or not sid2route:
        raise RuntimeError("detection RỖNG (name2sid=%d, sid2route=%d) @ %s — nghi git show/grep "
                           "lỗi hoặc tree đọc dở; bỏ qua để không đè dữ liệu tốt"
                           % (len(name2sid), len(sid2route), sha[:10]))
    tests = fetch_tests()   # {} = tắt (no key) · None = Backlog lỗi → giữ data cũ · dict = ok
    if tests is None:
        tests = load_prev_tests(OUT)
        print("[fetch_screens] (Backlog lỗi → GIỮ test data lần trước: %d màn)" % len(tests), file=sys.stderr)
    screens = []
    for sid, name, ticket, pic in CONFIG:
        if sid in sid2route:
            st, rt, note = "done", sid2route[sid], ""
        else:
            st, rt, note = "todo", "", NOTE_TODO.get(sid, "chưa migrate vào r20260727")
        tt = tests.get(sid) or {}
        screens.append({"sid": sid, "name": name, "route": rt, "ticket": ticket,
                        "pic": pic, "st": st, "note": note,
                        "test": tt.get("test"), "tester": tt.get("tester")})
    return sha, screens

def main():
    sha, screens = investigate()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"updated": now, "tip": sha[:10], "branch": BRANCH,
            "picOrder": PIC_ORDER, "screens": screens}

    def core(d):   # dedup theo NỘI DUNG màn (bỏ updated + tip) → chỉ push khi trạng thái đổi
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
    print("[fetch_screens] %s | %d màn: done=%d chưa=%d | tip=%s @ %s"
          % (OUT, len(screens), nd, len(screens) - nd, sha[:10], now))

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("[fetch_screens] LỖI: %s" % e, file=sys.stderr)
        sys.exit(1)
