# -*- coding: utf-8 -*-
# Danh sách sprint dùng CHUNG cho mọi build_s*.py (menu điều hướng).
# Thêm sprint mới: thêm 1 dòng vào SPRINTS rồi regenerate tất cả page + push main.
# data/screens/plan = file mà ô TÌM KIẾM (search.js, repo root) đọc: data/screens trên nhánh `data`,
# plan phục vụ từ Pages (cùng origin). rlabel = nhãn cột r khi 1 key gộp nhiều nhánh.
import os, glob, json, html
SPRINTS = [
    {"label": "Sprint 12", "href": "s12.html", "data": "data-s12.json"},
    {"label": "Sprint 13", "href": "index.html", "data": "data.json"},
    {"label": "Sprint 14", "href": "s14.html", "data": "data-s14.json", "screens": "screens-s14.json"},
    {"label": "Sprint 15+16", "href": "s15.html", "data": "data-s15.json", "plan": "s15-plan.json"},
    {"label": "Sprint 17", "href": "s17.html", "data": "data-s17.json"},   # Sprint 16 nằm chung page s15 (không có nhánh r riêng)
    {"label": "Sprint 18", "href": "s18.html", "data": "data-s18.json", "rlabel": "→r0810/0921"},
]

def _ver():
    # version = mtime mới nhất trong các file quyết định SHELL (CSS + menu + build scripts).
    # → đổi mỗi khi sửa shell; giống nhau cho cả 4 page (cùng tập file) → menu nhất quán.
    # Vì Pages set cache-control:max-age=600 cho HTML, phải đổi URL menu để chuyển page KHÔNG dính cache cũ.
    srcs = ["_head.html", "sprints.py", "../search.js"] + glob.glob("build_s*.py")
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
    # search.js tự chèn ô tìm kiếm vào .topnav-inner; data-sprints = danh sách file để tra.
    search = ('<script src="search.js%s" data-sprints="%s" defer></script>'
              % (q, html.escape(json.dumps(SPRINTS, ensure_ascii=False), quote=True)))
    return ('<nav class="topnav"><div class="topnav-inner">'
            '<span class="topnav-brand">W3 PR Tracking</span>'
            '<span class="topnav-sep">/</span>' + items + '</div></nav>' + search)
