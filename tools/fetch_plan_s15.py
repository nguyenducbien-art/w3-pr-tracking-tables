#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lấy TRẠNG THÁI phân công Sprint 15 từ Backlog (assignee + status) → s15-status.json.
Bảng phân công (build_s15.py) fetch file này để hiển thị LIVE:
  - Implement PIC = assignee của ticket 親 (タスク(親)) — chỗ team gán khi nhận màn.
  - Test PIC      = assignee của ticket テスト実施.
  - status        = trạng thái ticket đó (Open→todo / In Progress→wip / Resolved,Closed→done).

⚠️ Ticket Sprint 15 KHÔNG gán milestone đồng nhất → query theo issueType(親/テスト実施)+category 画面実装
(179 親 toàn sprint), lọc client-side về đúng số ticket trong report (s15-plan.json).
Key theo SỐ TICKET (keyId): impl theo 親 ticket, test theo テスト実施 ticket.

API key đọc từ env BACKLOG_API_KEY hoặc tools/.backlog_key (gitignored). Best-effort:
thiếu key / API lỗi → exit khác 0/2 (refresh.sh coi là lỗi, giữ file cũ, KHÔNG đè rỗng).
Exit: 0=đổi · 2=không đổi · 1=lỗi. Usage: python3 fetch_plan_s15.py [out.json]
"""
import json, os, re, sys, datetime, urllib.request, urllib.parse

OUT = sys.argv[1] if len(sys.argv) > 1 else "s15-status.json"
BACKLOG_HOST = "dialog-inc.backlog.com"
CATEGORY_UI  = 2230051     # category 画面実装
TYPE_PARENT  = 4092231     # タスク(親)   → Implement PIC
TYPE_TEST    = 4092260     # タスク(テスト実施) → Test PIC
NAME = {"nguyenanhkhoa": "Khoa", "nguyenducbien": "Biên", "nguyennhatminh": "Minh",
        "phambaohung": "Hưng", "phamtiendat": "Đạt", "phamngocson": "Sơn", "trinhduybong": "Bồn"}
STATE = {"Open": "todo", "In Progress": "wip", "Resolved": "done", "Closed": "done"}

def backlog_key():
    k = os.environ.get("BACKLOG_API_KEY")
    if k and k.strip():
        return k.strip()
    try:
        return open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backlog_key")).read().strip() or None
    except OSError:
        return None

def short(a):
    if not a:
        return None
    uid = ((a.get("nulabAccount") or {}).get("uniqueId") or "")
    return next((v for k, v in NAME.items() if uid.startswith(k)), a.get("name", "?")[:14])

def fetch_all(key):
    """Tất cả ticket 親 + テスト実施 (category 画面実装), phân trang."""
    out, offset = [], 0
    while True:
        q = [("apiKey", key), ("categoryId[]", CATEGORY_UI),
             ("issueTypeId[]", TYPE_PARENT), ("issueTypeId[]", TYPE_TEST),
             ("count", 100), ("offset", offset)]
        url = "https://%s/api/v2/issues?%s" % (BACKLOG_HOST, urllib.parse.urlencode(q))
        with urllib.request.urlopen(url, timeout=45) as r:
            batch = json.loads(r.read().decode("utf-8"))
        out.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        if offset > 2000:
            break
    return out

def main():
    key = backlog_key()
    if not key:
        print("[fetch_plan] KHÔNG có Backlog API key", file=sys.stderr); sys.exit(1)
    issues = None
    for attempt in range(3):
        try:
            issues = fetch_all(key); break
        except Exception as e:
            print("[fetch_plan] thử %d/3 lỗi: %s" % (attempt + 1, e), file=sys.stderr)
    if issues is None:
        sys.exit(1)   # → refresh.sh coi là lỗi, giữ s15-status.json cũ

    impl, test = {}, {}
    for it in issues:
        tid = str(it.get("keyId"))
        rec = {"pic": short(it.get("assignee")),
               "st": STATE.get((it.get("status") or {}).get("name"), "todo")}
        t = (it.get("issueType") or {}).get("id")
        if t == TYPE_PARENT:
            impl[tid] = rec
        elif t == TYPE_TEST:
            test[tid] = rec

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"updated": now, "impl": impl, "test": test}

    def core(d):
        return json.dumps({"impl": d.get("impl"), "test": d.get("test")}, ensure_ascii=False, sort_keys=True)
    try:
        if core(json.load(open(OUT))) == core(data):
            print("[fetch_plan] no change — bỏ push"); sys.exit(2)
    except (OSError, ValueError):
        pass

    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    na = sum(1 for v in impl.values() if v["pic"])
    print("[fetch_plan] %s | 親=%d (assigned %d) · テスト実施=%d | %s"
          % (OUT, len(impl), na, len(test), now))

if __name__ == "__main__":
    main()
