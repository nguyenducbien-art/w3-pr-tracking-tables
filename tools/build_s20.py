# -*- coding: utf-8 -*-
# Build SHELL s18.html — Table A Sprint 18 (từ 21/09/2026). data-s20.json do fetch_build_s18.py sinh.
# Từ Sprint 16 không còn nhánh r riêng mỗi sprint → chia theo NGÀY TẠO PR; cột "→r" gộp r0810 + r0921 + r1005.
# Page này CHỈ PR tracking (Bảng 1 common + Bảng 2 màn/fix + bảng phụ scaffold) — không có bảng phân công
# (Sprint 19 chưa có plan màn như s15-plan.json).
# RENDER_JS tái sử dụng của build_s12.py (bản PR-only) rồi retarget sang data-s17.json / r810 / Sprint 17.
# Usage: python3 build_s20.py [../data-s20.json]
import json, re, sys, ast
from sprints import nav_html

DATA = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "data-s20.json"))
NAV  = nav_html("Sprint 20")
css  = re.search(r'<style>.*?</style>', open("_head.html").read(), re.S).group(0)
MASCOT = ('<script src="https://nguyenducbien-art.github.io/pixel-pets/pixel-pets.js" '
          'data-min="2" data-max="5" defer></script>')
FAVICON = ""
for _l in open("build_s14.py"):
    if _l.startswith("FAVICON = "):
        FAVICON = ast.literal_eval(re.match(r'\s*(".*")', _l[len("FAVICON = "):]).group(1)); break

# ---- RENDER_JS: lấy bản PR-only của build_s12 → retarget ----
_pr = re.search(r'RENDER_JS = r"""(.*?)"""', open("build_s12.py").read(), re.S).group(1)
for _a, _b in [("data-s12.json", "data-s20.json"), ("r20260629", "r20260810"),
               ("r629", "r810"), ("Sprint 12", "Sprint 20"), ("2026-07-27", "2026-10-19")]:
    _pr = _pr.replace(_a, _b)

# ---- CHÈN cột "Screen" (screen_id) — CHỈ Bảng 2 (normalRows), qua param showScreen (giống build_s15) ----
# r.sid nhúng sẵn trong data-s17.json (map ticket→screen_id từ s15-plan.json; Sprint 17 chưa có plan riêng
# nên chỉ khớp được ticket của màn Sprint 15 làm tiếp).
_SCR_CELL = ("+(showScreen?('<td>'+(r.sid?'<span class=\"ticket\">'+esc(String(r.sid))"
             "+'</span>':'<span class=\"cf-na\">—</span>')+'</td>'):'')")
_TICKET_CELL = "+'<td>'+tkLink(r.ticket)+'</td>'"
assert _pr.count(_TICKET_CELL) == 2, "kỳ vọng ô ticket 2 lần (mainRow+scfRow)"
_pr = _pr.replace(_TICKET_CELL, _TICKET_CELL + _SCR_CELL, 1)   # count=1 → chỉ mainRow
for _a, _b in [
    ("function mainRow(r){", "function mainRow(r,showScreen){"),
    ("function mainBlock(rows,title,sub){", "function mainBlock(rows,title,sub,showScreen){"),
    ("return mainRow(r);", "return mainRow(r,showScreen);"),
    ("'<th>Ticket</th><th>Dev</th><th>→base</th>",
     "'<th>Ticket</th>'+(showScreen?'<th>Screen</th>':'')+'<th>Dev</th><th>→base</th>"),
    ("Copilot chỉ đếm PR→base.')", "Copilot chỉ đếm PR→base.',false)"),
    # cột "→r" gộp r20260810 + r20260921 (nhánh sau chưa tồn tại) → không ghi cứng 1 tên nhánh
    ("<th>→r20260810</th>", "<th>→r 0810/1005/1019</th>"),
    ("(màn migration + fix lẻ).')", "(màn migration + fix lẻ).',true)"),
    # subtitle: nói rõ luật chia theo ngày + trỏ ngược về page Sprint 15+16
    ("tạo từ <b>2026-10-19</b> vào <b>develop/base</b> / <b>r20260810</b> — chia 2 bảng",
     "tạo từ <b>2026-10-19</b> (ngày bắt đầu Sprint 20) vào <b>develop/base</b> / <b>r20261019</b> (nhánh của Sprint 20) / <b>r20260810</b> / <b>r20261005</b>"
     " — chia theo NGÀY TẠO PR, PR trước 19/10 xem ở page Sprint 19. PR mới của ticket đã có ở sprint trước tự về page của sprint đó. Bên phải #PR là tag nhánh r đích."
     " Chia 2 bảng"),
    ('<a href="index.html" style="font-family:inherit;font-size:12px">← Sprint 13</a>',
     '<a href="s19.html" style="font-family:inherit;font-size:12px">← Sprint 19</a>'),
]:
    assert _a in _pr, "anchor không thấy: %s" % _a[:50]
    _pr = _pr.replace(_a, _b)
RENDER_JS = _pr

TITLE = "Table A — Sprint 20"

def build(inline):
    data_script = ('<script id="table-data" type="application/json">'
                   + (json.dumps(DATA, ensure_ascii=False) if inline else "") + '</script>')
    return ('<title>' + TITLE + '</title>\n' + FAVICON + '\n' + css + '\n'
            + NAV + '\n<div id="app"></div>\n' + MASCOT + '\n' + data_script + '\n<script>' + RENDER_JS + '</script>')

# artifact = fragment + inline JSON
open("table-a-s20.html", "w").write(build(True))

# hosted = full document, FETCH data-s20.json từ nhánh data (Sprint 20 = sprint active, cron 5p)
doc = ('<!DOCTYPE html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n<title>' + TITLE + '</title>\n' + FAVICON + '\n' + css + '\n</head>\n<body>\n'
       + NAV + '\n<div id="app"></div>\n' + MASCOT + '\n<script id="table-data" type="application/json"></script>\n<script>' + RENDER_JS + '</script>\n</body>\n</html>')
open("s20.html", "w").write(doc)

print("built shell: s20.html (fetch) + table-a-s20.html (artifact,inline) từ data-s20.json |",
      len(DATA["main"]), "main +", len(DATA["scaffold"]), "scaffold")
