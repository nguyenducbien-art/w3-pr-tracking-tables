# -*- coding: utf-8 -*-
# Build s15.html — bảng PHÂN CÔNG VIỆC Sprint 15 (tĩnh, data từ s15-plan.json).
# Sprint 15 chưa code → chưa có migrate/PR tracking; page này show kế hoạch phân công trước.
# Nguồn plan = s15-plan.json (tracked). Đổi phân công → sửa JSON rồi chạy lại build_s15.py.
# Usage: python3 build_s15.py [../s15-plan.json]
import json, re, sys
from sprints import nav_html

PLAN = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "s15-plan.json"))
NAV  = nav_html("Sprint 15")
css  = re.search(r'<style>.*?</style>', open("_head.html").read(), re.S).group(0)
MASCOT = ('<script src="https://nguyenducbien-art.github.io/pixel-pets/pixel-pets.js" '
          'data-min="2" data-max="5" defer></script>')

BASE = PLAN["backlogBase"]
WIP  = set(PLAN.get("wip_parents", []))
TYPE = {   # 実装タイプ → (class pill, nhãn ngắn)
  "一覧 (list)":      ("pill-open",    "list"),
  "登録/編集 (edit)": ("pill-draft",   "edit"),
  "明細 (details)":   ("pill-merged",  "details"),
  "特殊 (special)":   ("pill-pinned",  "special"),
}
TYPE_ORDER = ["一覧 (list)", "登録/編集 (edit)", "明細 (details)", "特殊 (special)"]

def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def tk(num):
    if not num:
        return '<span class="cf-na">—</span>'
    if re.fullmatch(r"\d+", str(num)):
        return '<a href="%s%s" target="_blank" rel="noopener">AR-%s</a>' % (BASE, num, num)
    return '<span class="ticket">%s</span>' % esc(num)

def type_pill(t):
    cls, lbl = TYPE.get(t, ("pill-draft", esc(t)))
    return '<span class="pill %s">%s</span>' % (cls, lbl)

def pic_cell(p):
    p = (p or "").strip()
    if not p or p == "(để trống)":
        return '<span class="cf-na" title="pool chưa gán">(để trống)</span>'
    return '<span class="dev">%s</span>' % esc(p)

def row(r):
    wip = r.get("parent") in WIP
    tail = ' <span class="badge-common" title="Minh đang làm">WIP</span>' if wip else ''
    return ('<tr>'
      + '<td><span class="ticket">' + esc(r["sid"]) + '</span></td>'
      + '<td><span class="jp-cell">' + esc(r["name"]) + '</span></td>'
      + '<td>' + type_pill(r["type"]) + '</td>'
      + '<td>' + tk(r["parent"]) + '</td>'
      + '<td>' + tk(r["impl"]) + '</td>'
      + '<td>' + tk(r["test"]) + '</td>'
      + '<td>' + pic_cell(r["impl_pic"]) + tail + '</td>'
      + '<td>' + (pic_cell(r["test_pic"]) if r.get("test_pic") else '<span class="cf-na">—</span>') + '</td>'
      + '<td>' + (esc(r["free_test"]) if r.get("free_test") else '<span class="cf-na">—</span>') + '</td>'
      + '</tr>')

def domain_block(d, idx):
    body = "".join(row(r) for r in d["rows"])
    return ('<h2 style="font-size:15px;font-weight:700;margin:26px 0 6px;letter-spacing:-0.01em;">'
            + str(idx) + '. ' + esc(d["domain"]) + ' <span style="font-weight:400;color:var(--text-dim);font-size:12px;">— ' + str(len(d["rows"])) + ' màn</span></h2>'
      + '<div class="scroll-wrap"><table style="min-width:1180px"><thead><tr>'
      + '<th>Screen ID / URL</th><th>Tên màn</th><th>Loại</th><th>親 (cha)</th><th>実装 (impl)</th>'
      + '<th>テスト実施 (test)</th><th>Impl PIC</th><th>Test PIC</th><th>Free test</th>'
      + '</tr></thead><tbody>' + body + '</tbody></table></div>')

def allocation():
    # PIC × loại màn
    pics, counts = [], {}
    for d in PLAN["domains"]:
        for r in d["rows"]:
            p = r["impl_pic"].strip() or "(để trống)"
            if p not in counts:
                counts[p] = {t: 0 for t in TYPE_ORDER}; pics.append(p)
            counts[p][r["type"]] += 1
    # thứ tự: người thật trước, (để trống) cuối
    order = [p for p in pics if p != "(để trống)"] + (["(để trống)"] if "(để trống)" in pics else [])
    head = '<tr><th>PIC</th>' + "".join('<th>%s</th>' % TYPE[t][1] for t in TYPE_ORDER) + '<th>Tổng</th></tr>'
    rows = ""
    tot = {t: 0 for t in TYPE_ORDER}; gtot = 0
    for p in order:
        c = counts[p]; s = sum(c.values()); gtot += s
        for t in TYPE_ORDER:
            tot[t] += c[t]
        cells = "".join('<td>%s</td>' % (c[t] or '<span class="cf-na">·</span>') for t in TYPE_ORDER)
        rows += '<tr><td>%s</td>%s<td><b>%d</b></td></tr>' % (pic_cell(p), cells, s)
    foot = '<tr style="border-top:2px solid var(--border)"><td><b>Tổng</b></td>' + "".join('<td><b>%d</b></td>' % tot[t] for t in TYPE_ORDER) + '<td><b>%d</b></td></tr>' % gtot
    return ('<div class="scroll-wrap" style="max-width:560px"><table style="min-width:480px"><thead>'
            + head + '</thead><tbody>' + rows + foot + '</tbody></table></div>')

total = sum(len(d["rows"]) for d in PLAN["domains"])
body = ('<div class="page">'
  + '<div class="page-header"><h1>Phân công việc — Sprint 15</h1>'
  + '<span class="meta">' + str(total) + ' màn · ' + str(len(PLAN["domains"])) + ' domain · kế hoạch (chưa bắt đầu code)</span></div>'
  + '<div class="subtitle">' + esc(PLAN["note"]) + '</div>'
  + '<h2 style="font-size:15px;font-weight:700;margin:18px 0 6px;">Phân bổ Implement PIC (chia đều theo loại màn)</h2>'
  + allocation()
  + "".join(domain_block(d, i + 1) for i, d in enumerate(PLAN["domains"]))
  + '<div class="footnote">Loại màn (実装タイプ): <span class="pill pill-open">list</span> 一覧 · '
  + '<span class="pill pill-draft">edit</span> 登録/編集 · <span class="pill pill-merged">details</span> 明細 · '
  + '<span class="pill pill-pinned">special</span> 特殊.<br>'
  + 'Ticket: 親 = ticket cha (親), 実装 = implement＆単体テスト, テスト実施 = integration test — click mở Backlog. '
  + '“(để trống)” Impl PIC = pool màn chưa gán. <b>WIP</b> = Minh đang làm (親 616/619/643).<br>'
  + 'Bảng này là <b>kế hoạch phân công</b> (data từ report, nhập tay ở <code>s15-plan.json</code>). '
  + 'Khi Sprint 15 bắt đầu code sẽ bổ sung bảng PR tracking + trạng thái migrate như Sprint 14.</div>'
  + '</div>')

CLICK = ("document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^=\"http\"]');"
         "if(a){e.preventDefault();window.open(a.href,'_blank','noopener');}},true);")

import ast
FAVICON = ""
for _l in open("build_s14.py"):
    if _l.startswith("FAVICON = "):
        FAVICON = ast.literal_eval(re.match(r'\s*(".*")', _l[len("FAVICON = "):]).group(1))
        break

doc = ('<!DOCTYPE html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n<title>Phân công — Sprint 15</title>\n'
       + FAVICON + '\n' + css + '\n</head>\n<body>\n'
       + NAV + '\n' + body + '\n' + MASCOT + '\n<script>' + CLICK + '</script>\n</body>\n</html>')
open("s15.html", "w").write(doc)
print("built s15.html |", total, "màn /", len(PLAN["domains"]), "domain")
