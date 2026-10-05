# -*- coding: utf-8 -*-
# Xếp tay PR vào sprint, ĐÈ luật "chia theo ngày tạo PR" của page s15 / s17 / s18.
# Dùng khi PR tạo sau mốc cắt nhưng thuộc việc của sprint trước (vd PR port r20260810 → base).
# Mỗi PR chỉ nằm ở ĐÚNG 1 page: page khớp số sprint thì lấy, các page theo ngày khác thì bỏ.
# Sửa file này → tick cron sau tự áp (fetch_build_s15/s17/s18 đọc lúc chạy); page s17 hiện ghi chú
# danh sách PR xếp tay → cần rebuild page + push main nếu muốn ghi chú cập nhật.
PR_SPRINT = {
    13020: 17,   # AR-2047 port → base (tạo 25/09) — việc Sprint 17; user yêu cầu 25/09
    13021: 17,   # AR-1708 port → base (tạo 25/09) — việc Sprint 17; user yêu cầu 25/09
    13051: 17,   # AR-2037 port → base (tạo 28/09) — việc Sprint 17; user yêu cầu 28/09
    13068: 17,   # AR-2037 fix tiếp → r20260810 (tạo 28/09) — việc Sprint 17; user yêu cầu 28/09
    13072: 15,   # AR-1551 fix tiếp → r20260810 (tạo 28/09) — việc Sprint 15+16; user yêu cầu 28/09
    13073: 15,   # AR-1655 port → base (tạo 28/09) — việc Sprint 15+16; user yêu cầu 28/09
}


def keep(p, sprint, in_window):
    """True nếu PR thuộc page `sprint`: PR xếp tay → theo PR_SPRINT; còn lại → theo khoảng ngày."""
    forced = PR_SPRINT.get(p["number"])
    return forced == sprint if forced is not None else in_window


# ---- Tự động: PR mới của ticket sprint cũ → về page của sprint ĐẦU TIÊN ticket xuất hiện (user yêu cầu 05/10) ----
# "Sprint gốc" của ticket = sprint nhỏ nhất mà ticket có PR (không CLOSED) theo đúng luật vào page đó:
#   - Sprint 15+16: phải có PR nhắm r20260810 trong khoảng ngày (page s15 chỉ nhận ticket có PR r810)
#   - Sprint 17 / 18: có PR nhắm nhánh r hoặc base trong khoảng ngày
# PR xếp tay (PR_SPRINT) vẫn ưu tiên cao nhất và cũng được tính là bằng chứng cho sprint được xếp.
# Ticket chỉ có PR trước Sprint 15 (Sprint 14 trở về trước, page dựng theo nhánh r) → không có sprint gốc
# ở đây → PR mới của nó vẫn theo luật ngày.
WINDOWS = ((15, "2026-08-01", "2026-09-06"), (17, "2026-09-07", "2026-09-20"), (18, "2026-09-21", "9999-12-31"))
HOME_BRANCHES = ("r20260810", "r20260921", "base")


def sprint_of_date(d):
    for s, a, b in WINDOWS:
        if a <= d <= b: return s
    return None


def ticket_home(raw, vn_date, ticket_of):
    """raw = {branch: [PR json]} của HOME_BRANCHES; ticket_of(headRefName) → ticket hoặc None. Trả {ticket: sprint gốc}."""
    home = {}
    for br, prs in raw.items():
        for p in prs:
            if p["state"] == "CLOSED": continue
            tk = ticket_of(p["headRefName"])
            if not tk: continue
            s = PR_SPRINT.get(p["number"]) or sprint_of_date(vn_date(p["createdAt"]))
            if s is None or (s == 15 and br != "r20260810"): continue
            if tk not in home or s < home[tk]: home[tk] = s
    return home


def keep_auto(p, sprint, in_window, home, tk, d):
    """Như keep(), thêm bước giữa: ticket có sprint gốc SỚM HƠN sprint theo ngày của PR → PR về sprint gốc.
    Chỉ dời LÙI về sprint cũ; PR tạo trước Sprint 15 (ngoài mọi khoảng ngày) giữ nguyên luật ngày."""
    forced = PR_SPRINT.get(p["number"])
    if forced is not None: return forced == sprint
    ds = sprint_of_date(d)
    if ds is not None and tk in home and home[tk] < ds: return home[tk] == sprint
    return in_window
