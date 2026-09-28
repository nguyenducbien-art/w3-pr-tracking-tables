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
