# -*- coding: utf-8 -*-
# Danh sách sprint dùng CHUNG cho mọi build_s*.py (menu điều hướng).
# Thêm sprint mới: thêm 1 dòng vào SPRINTS rồi regenerate tất cả page + push main.
SPRINTS = [
    {"label": "Sprint 13", "href": "index.html"},
    {"label": "Sprint 14", "href": "s14.html"},
]

def nav_html(active_label):
    """Thanh menu tĩnh (bake vào shell) — sprint active được đánh dấu class active."""
    items = "".join(
        '<a href="%s"%s>%s</a>' % (
            s["href"], ' class="active"' if s["label"] == active_label else "", s["label"])
        for s in SPRINTS
    )
    return ('<nav class="topnav"><div class="topnav-inner">'
            '<span class="topnav-brand">W3 PR Tracking</span>'
            '<span class="topnav-sep">/</span>' + items + '</div></nav>')
