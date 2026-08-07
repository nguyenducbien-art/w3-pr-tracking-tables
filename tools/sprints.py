# -*- coding: utf-8 -*-
# Danh sách sprint dùng CHUNG cho mọi build_s*.py (menu điều hướng).
# Thêm sprint mới: thêm 1 dòng vào SPRINTS rồi regenerate tất cả page + push main.
import os, glob
SPRINTS = [
    {"label": "Sprint 12", "href": "s12.html"},
    {"label": "Sprint 13", "href": "index.html"},
    {"label": "Sprint 14", "href": "s14.html"},
    {"label": "Sprint 15", "href": "s15.html"},
]

def _ver():
    # version = mtime mới nhất trong các file quyết định SHELL (CSS + menu + build scripts).
    # → đổi mỗi khi sửa shell; giống nhau cho cả 4 page (cùng tập file) → menu nhất quán.
    # Vì Pages set cache-control:max-age=600 cho HTML, phải đổi URL menu để chuyển page KHÔNG dính cache cũ.
    srcs = ["_head.html", "sprints.py"] + glob.glob("build_s*.py")
    try:
        return str(int(max(os.path.getmtime(f) for f in srcs if os.path.exists(f))))
    except ValueError:
        return ""

def nav_html(active_label):
    """Thanh menu (bake vào shell) — active được đánh dấu; href gắn ?v=<ver> để bust cache khi đổi shell."""
    q = _ver()
    q = ("?v=" + q) if q else ""
    items = "".join(
        '<a href="%s%s"%s>%s</a>' % (
            s["href"], q, ' class="active"' if s["label"] == active_label else "", s["label"])
        for s in SPRINTS
    )
    return ('<nav class="topnav"><div class="topnav-inner">'
            '<span class="topnav-brand">W3 PR Tracking</span>'
            '<span class="topnav-sep">/</span>' + items + '</div></nav>')
