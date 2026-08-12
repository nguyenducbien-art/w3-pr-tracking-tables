#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch live PR data từ GitHub (dialog-inc/w3package_v2) → build data-s15.json cho
Table A Sprint 15 (nhắm base + r20260810 + r20260810_scaffold).
Self-contained: chỉ dùng gh + python stdlib. KHÔNG chứa secret.
Usage: python3 fetch_build_s15.py [output_data.json]
"""
import json, re, subprocess, sys, datetime, time

REPO = "dialog-inc/w3package_v2"
OWNER, NAME = "dialog-inc", "w3package_v2"
SINCE = "2026-08-01"                      # bound scan; Sprint 15 gate thực = "có PR nhắm r20260810" (không phải ngày)
PRURL = "https://github.com/%s/pull/" % REPO
OUT = sys.argv[1] if len(sys.argv) > 1 else "data-s15.json"

EXCLUDE = {"1495"}                        # ticket ẩn hẳn khỏi bảng (mọi PR base/r810) — user yêu cầu 08-03
BASE_COMMON_SINCE = "2026-08-10"          # LUẬT MỞ RỘNG: common PR→base (chưa có r810 PR) created >= ngày này cũng vào Sprint 15
# ĐẶC CÁCH dev: khi PR gốc của người sở hữu màn bị CLOSED (bị gh_list lọc) + chỉ còn PR fix của
# người khác được merge → dev tự suy sẽ SAI. Map {ticket: dev-short} ép đúng người sở hữu.
FORCE_DEV = {"635": "minh"}               # 635: PR gốc #11821 (Minh) CLOSED, còn #11867 (bien fix) MERGED

DEV = {"nguyenducbien-art":"bien","nguyennhatminh-dl":"minh","phambaohung-dl":"hung",
       "phamtiendat-oss":"dat","nguyenanhkhoa-rk":"khoa"}

def load_ticket_sid():
    """map ticket(親/実装/テスト) -> screen_id, từ s15-plan.json (repo root). {} nếu thiếu file."""
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "s15-plan.json")
    try:
        plan = json.load(open(p))
    except (OSError, ValueError):
        return {}
    t2s = {}
    for dom in plan.get("domains", []):
        for r in dom.get("rows", []):
            for k in ("parent", "impl", "test"):
                if r.get(k):
                    t2s.setdefault(str(r[k]), str(r["sid"]))   # first-wins
    return t2s

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("cmd fail: %s\n%s" % (" ".join(args), r.stderr[:500]))
    return r.stdout

def ensure_account():
    subprocess.run(["gh","auth","switch","--user","nguyenducbien-art"],
                   capture_output=True, text=True)
    who = run(["gh","api","user","--jq",".login"]).strip()
    if who != "nguyenducbien-art":
        raise RuntimeError("sai gh account: %s (cần nguyenducbien-art)" % who)

def dev_of(login): return DEV.get(login, login)

_SUF = re.compile(r'-(dl|oss|rk|art|dialog|inc)$', re.I)
def short_name(login):
    if not login: return None
    return DEV.get(login) or _SUF.sub('', login)   # map dev đã biết, else bỏ hậu tố -dl/-rk/...

def fmt_dt(iso):
    # "2026-07-14T15:07:32Z" (UTC) -> "MM-DD HH:MM" giờ VN (UTC+7)
    dt = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=7)
    return dt.strftime("%m-%d %H:%M")

def ticket_from_branch(seg):
    s = re.sub(r'^#','',seg); s = re.sub(r'^ANGULAR_REPLACE-','',s); s = re.sub(r'^common-','',s)
    m = re.match(r'(\d+)', s); return m.group(1) if m else None

def ticket_from_title(t):
    m = re.search(r'ANGULAR_REPLACE-(\d+)', t or ''); return m.group(1) if m else None

def is_sync(seg):
    if seg in ('base','r20260629','r20260713','r20260713_scaffold','r20260810','r20260810_scaffold'): return True
    if re.match(r'^pr\d+', seg): return True
    if 'evidences' in seg: return True
    if re.match(r'^r2026\d{4}-', seg): return True
    return False

def clean_title(t):
    t = t or ''
    t = re.sub(r'^(fix|feat|chore|test|refactor|docs)\s*:\s*', '', t)
    t = re.sub(r'^(\[[^\]]*\]\s*)+', '', t)
    t = re.sub(r'\s*#ANGULAR_REPLACE-\d+\s*$', '', t)
    return t.strip()

def gh_list(branch):
    out = run(["gh","pr","list","--repo",REPO,"--base","mimosa/frontend/develop/"+branch,
               "--state","all","--limit","400","--json","number,state,createdAt,headRefName,author,title"])
    return [p for p in json.loads(out)
            if p["state"] != "CLOSED" and p["createdAt"][:10] >= SINCE]

_Q = ('query($n:Int!){repository(owner:"%s",name:"%s"){pullRequest(number:$n){'
      'state isDraft reviewDecision mergeable additions deletions changedFiles commits{totalCount} '
      'reviewRequests(first:20){nodes{requestedReviewer{__typename ... on User{login} ... on Team{name} ... on Mannequin{login}}}} '
      'latestOpinionatedReviews(first:20){nodes{author{login} state}} '
      'body reviewThreads(first:100){nodes{isResolved '
      'comments(first:1){nodes{author{login}}}}}}}}' % (OWNER, NAME))

# query nhẹ chỉ lấy mergeable — dùng retry khi GitHub trả UNKNOWN (tính lazy)
_QM = ('query($n:Int!){repository(owner:"%s",name:"%s"){pullRequest(number:$n){mergeable}}}' % (OWNER, NAME))

def resolve_cf(d, n):
    """CONFLICTING→bad, MERGEABLE→ok, MERGED→ok; OPEN mà UNKNOWN thì retry, cuối cùng vẫn UNKNOWN→unk."""
    if d.get("state") == "MERGED": return "ok"
    mg = d.get("mergeable")
    if d.get("state") == "OPEN" and mg == "UNKNOWN":
        for _ in range(3):
            time.sleep(2)
            try:
                mg = json.loads(run(["gh","api","graphql","-F","n=%d"%n,"-f","query="+_QM]))["data"]["repository"]["pullRequest"]["mergeable"]
            except Exception:
                break
            if mg != "UNKNOWN": break
    if mg == "CONFLICTING": return "bad"
    if mg == "MERGEABLE":   return "ok"
    return "unk"

def status_of(d):
    if d.get("state") == "MERGED": return "merged"
    if d.get("isDraft"): return "draft"
    rd = d.get("reviewDecision")
    if rd == "APPROVED": return "approved"
    if rd == "CHANGES_REQUESTED": return "changes"
    return "open"

def pr_detail(n):
    d = json.loads(run(["gh","api","graphql","-F","n=%d"%n,"-f","query="+_Q]))["data"]["repository"]["pullRequest"]
    th = [t for t in d["reviewThreads"]["nodes"]
          if t["comments"]["nodes"] and re.search("[Cc]opilot", t["comments"]["nodes"][0]["author"]["login"] or "")]
    total = len(th); unres = len([t for t in th if not t["isResolved"]])
    drive = bool(re.search(r'drive\.google\.com', d.get("body") or "", re.I))
    cf = resolve_cf(d, n)   # bad/ok/unk (retry mergeable khi UNKNOWN)
    nc = (d.get("commits") or {}).get("totalCount", 0)   # số commit của PR (branch ahead base)
    add = d.get("additions") or 0; dele = d.get("deletions") or 0   # số dòng thêm/xoá (diff stat)
    fc = d.get("changedFiles") or 0                                  # số file thay đổi
    # reviewers: pending = được request nhưng chưa review; ap/ch = latest approve / changes-requested
    pending = []
    for rn in ((d.get("reviewRequests") or {}).get("nodes") or []):
        rev = rn.get("requestedReviewer") or {}
        nm = short_name(rev.get("login") or rev.get("name"))
        if nm and nm not in pending: pending.append(nm)
    approved, changes = [], []
    for rv in ((d.get("latestOpinionatedReviews") or {}).get("nodes") or []):
        nm = short_name((rv.get("author") or {}).get("login"))
        if not nm: continue
        if rv.get("state") == "APPROVED" and nm not in approved: approved.append(nm)
        elif rv.get("state") == "CHANGES_REQUESTED" and nm not in changes: changes.append(nm)
    rvw = {"ap": approved, "ch": changes, "pd": pending}
    return {"cop": total, "unres": unres, "drive": drive, "cf": cf, "st": status_of(d),
            "nc": nc, "add": add, "del": dele, "fc": fc, "rvw": rvw}

def build():
    ensure_account()
    # ---- Sprint 15 = ticket CÓ PR nhắm r20260810 (KHÔNG lọc theo ngày) ----
    # base PR chỉ hiện cho các ticket đã có r810 PR (khớp theo ticket number).
    tickets = {}
    s15 = set()
    for p in gh_list("r20260810"):
        seg = p["headRefName"].split("/")[-1]
        if is_sync(seg): continue
        tk = ticket_from_branch(seg)
        if not tk or tk in EXCLUDE: continue
        s15.add(tk)
        t = tickets.setdefault(tk, {"base":[], "r810":[], "meta":[], "common":False})
        det = pr_detail(p["number"])
        t["r810"].append({"num": p["number"], "cf": det["cf"], "st": det["st"],
                          "nc": det["nc"], "add": det["add"], "del": det["del"], "fc": det["fc"]})
        t["meta"].append({"num":p["number"],"key":"r810","author":p["author"]["login"],
                          "created":p["createdAt"],"title":p["title"],"det":det})
        if seg.startswith("common-"): t["common"] = True

    # ---- LUẬT MỞ RỘNG (2026-08-10): common PR→base (branch `common-…`) CHƯA có r810 PR,
    #      created >= BASE_COMMON_SINCE → kết nạp vào Sprint 15 (hiện Bảng 1, cột →r810 trống). ----
    base_prs = gh_list("base")
    for p in base_prs:
        seg = p["headRefName"].split("/")[-1]
        if is_sync(seg) or not seg.startswith("common-"): continue
        tk = ticket_from_branch(seg)
        if not tk or tk in EXCLUDE or tk in s15: continue   # đã có r810 PR thì bỏ (đã thuộc s15)
        if p["createdAt"][:10] < BASE_COMMON_SINCE: continue
        s15.add(tk)

    for p in base_prs:
        seg = p["headRefName"].split("/")[-1]
        if is_sync(seg): continue
        tk = ticket_from_branch(seg)
        if tk not in s15: continue   # ticket thuộc Sprint 15 (có r810 PR HOẶC common-base created >= BASE_COMMON_SINCE)
        t = tickets.setdefault(tk, {"base":[], "r810":[], "meta":[], "common":False})
        det = pr_detail(p["number"])
        t["base"].append({"num": p["number"], "cf": det["cf"], "st": det["st"],
                          "nc": det["nc"], "add": det["add"], "del": det["del"], "fc": det["fc"]})
        t["meta"].append({"num":p["number"],"key":"base","author":p["author"]["login"],
                          "created":p["createdAt"],"title":p["title"],"det":det})
        if seg.startswith("common-"): t["common"] = True

    t2s = load_ticket_sid()   # ticket -> screen_id (từ s15-plan.json)
    main = []
    for tk, t in tickets.items():
        metas = t["meta"]; common = t["common"]
        base_m = [m for m in metas if m["key"] == "base"]
        # PR đại diện (dev/title/reviewers) = PR SỚM NHẤT = tác giả GỐC của ticket.
        # KHÔNG lấy metas[0] (PR số cao nhất/mới nhất do gh sort desc) — sẽ gán nhầm cho người
        # tạo PR fix follow-up (vd ...-fix-r20260810 / -docs) thay vì người implement gốc.
        rep = min(metas, key=lambda m: m["created"])
        dev = FORCE_DEV.get(tk, dev_of(rep["author"]))   # đặc cách override khi PR gốc bị CLOSED
        src = (base_m if base_m else metas) if common else metas   # common: copilot base-only
        cop = sum(m["det"]["cop"] for m in src)
        unres = sum(m["det"]["unres"] for m in src)
        drive = any(m["det"]["drive"] for m in (base_m or metas))
        created = fmt_dt(min(m["created"] for m in metas))   # PR sớm nhất, MM-DD HH:MM (giờ VN)
        main.append({"ticket":tk,"dev":dev,"bien":dev=="bien","sid":t2s.get(tk,""),
                     "base":t["base"],"r810":t["r810"],
                     "created":created,"drive":drive,"cop":cop,"unres":unres,
                     "rvw":rep["det"]["rvw"],   # reviewers của PR đại diện (PR gốc/sớm nhất)
                     "title":clean_title(rep["title"]),"_common":common})
    main.sort(key=lambda m:(m["created"], 1 if m["base"] else 0), reverse=True)
    common_list = [m["ticket"] for m in main if m["_common"]]
    for m in main: m.pop("_common", None)

    # ---- bảng phụ scaffold ----
    scaffold = []
    for p in gh_list("r20260810_scaffold"):
        seg = p["headRefName"].split("/")[-1]
        if is_sync(seg): continue
        det = pr_detail(p["number"])
        dev = dev_of(p["author"]["login"])
        scaffold.append({"ticket":ticket_from_title(p["title"]) or "—","dev":dev,"bien":dev=="bien",
                         "pr":{"num":p["number"],"cf":det["cf"],"st":det["st"],"nc":det["nc"],"add":det["add"],"del":det["del"],"fc":det["fc"]},"created":fmt_dt(p["createdAt"]),
                         "cop":det["cop"],"unres":det["unres"],"rvw":det["rvw"],"title":clean_title(p["title"])})
    scaffold.sort(key=lambda m:m["created"], reverse=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"updated":now,"repo":REPO,"prUrlBase":PRURL,
            "common":common_list,"invalidBase":[],
            "scaffoldBranch":"mimosa/frontend/develop/r20260810_scaffold",
            "main":main,"scaffold":scaffold}

    # dedupe: nếu nội dung (BỎ 'updated') không đổi so với file cũ → không ghi, exit 2
    def strip_ts(d):
        d = dict(d); d.pop("updated", None); return json.dumps(d, ensure_ascii=False, sort_keys=True)
    try:
        old = json.load(open(OUT))
        if strip_ts(old) == strip_ts(data):
            print("[fetch_build] no change (bỏ qua push)")
            sys.exit(2)
    except (FileNotFoundError, ValueError):
        pass
    json.dump(data, open(OUT,"w"), ensure_ascii=False, indent=1)
    print("[fetch_build] %s | main=%d scaffold=%d common=%d updated=%s"
          % (OUT, len(main), len(scaffold), len(common_list), now))

if __name__ == "__main__":
    build()
