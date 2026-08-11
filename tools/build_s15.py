# -*- coding: utf-8 -*-
# Build s15.html — bảng PHÂN CÔNG VIỆC Sprint 15 (tĩnh, data từ s15-plan.json).
# UI: 1 bảng + TAB theo domain (gọn); data nhúng inline, JS render tab đang chọn.
# Sprint 15 chưa code → chưa có migrate/PR tracking; page này show kế hoạch phân công trước.
# Nguồn plan = s15-plan.json (tracked). Đổi phân công → sửa JSON rồi chạy lại build_s15.py.
# Usage: python3 build_s15.py [../s15-plan.json]
import json, re, sys, ast
from sprints import nav_html

PLAN = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "s15-plan.json"))
NAV  = nav_html("Sprint 15")
css  = re.search(r'<style>.*?</style>', open("_head.html").read(), re.S).group(0)
MASCOT = ('<script src="https://nguyenducbien-art.github.io/pixel-pets/pixel-pets.js" '
          'data-min="2" data-max="5" defer></script>')
FAVICON = ""
for _l in open("build_s14.py"):
    if _l.startswith("FAVICON = "):
        FAVICON = ast.literal_eval(re.match(r'\s*(".*")', _l[len("FAVICON = "):]).group(1)); break

# ---- PR tracking (Bảng 1 Common / Bảng 2 Màn-Fix / Bảng phụ scaffold) ----
# Lấy RENDER_JS từ build_s12 (PR-only, không screen-list) → retarget sang r20260810 / data-s15.json.
_pr = re.search(r'RENDER_JS = r"""(.*?)"""', open("build_s12.py").read(), re.S).group(1)
for _a, _b in [("data-s12.json", "data-s15.json"), ("r20260629", "r20260810"),
               ("r629", "r810"), ("Sprint 12", "Sprint 15"), ("2026-07-27", "2026-08-01")]:
    _pr = _pr.replace(_a, _b)
PR_RENDER = _pr

def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# nhãn tab tiếng Anh cho mỗi domain = phần trong ngoặc "(...)"; fallback = bỏ "ドメイン"
for d in PLAN["domains"]:
    m = re.search(r"\((.*?)\)", d["domain"])
    d["short"] = m.group(1).strip() if m else re.split(r"ドメイン", d["domain"])[0].strip()

TYPE_ORDER = ["一覧 (list)", "登録/編集 (edit)", "明細 (details)", "特殊 (special)"]
TYPE_LBL = {"一覧 (list)": "list", "登録/編集 (edit)": "edit", "明細 (details)": "details", "特殊 (special)": "special"}

def allocation():
    counts, pics = {}, []
    for d in PLAN["domains"]:
        for r in d["rows"]:
            p = r["impl_pic"].strip() or "(để trống)"
            if p not in counts:
                counts[p] = {t: 0 for t in TYPE_ORDER}; pics.append(p)
            counts[p][r["type"]] += 1
    order = [p for p in pics if p != "(để trống)"] + (["(để trống)"] if "(để trống)" in pics else [])
    head = '<tr><th>PIC</th>' + "".join('<th>%s</th>' % TYPE_LBL[t] for t in TYPE_ORDER) + '<th>Tổng</th></tr>'
    rows, tot, g = "", {t: 0 for t in TYPE_ORDER}, 0
    for p in order:
        c = counts[p]; s = sum(c.values()); g += s
        for t in TYPE_ORDER:
            tot[t] += c[t]
        pcell = ('<span class="cf-na">(để trống)</span>' if p == "(để trống)" else '<span class="dev">%s</span>' % esc(p))
        cells = "".join('<td>%s</td>' % (c[t] or '<span class="cf-na">·</span>') for t in TYPE_ORDER)
        rows += '<tr><td>%s</td>%s<td><b>%d</b></td></tr>' % (pcell, cells, s)
    foot = ('<tr style="border-top:2px solid var(--border)"><td><b>Tổng</b></td>'
            + "".join('<td><b>%d</b></td>' % tot[t] for t in TYPE_ORDER) + '<td><b>%d</b></td></tr>' % g)
    return ('<div class="scroll-wrap" style="max-width:520px;margin-bottom:16px"><table style="min-width:460px">'
            '<thead>' + head + '</thead><tbody>' + rows + foot + '</tbody></table></div>')

# tab bar 1 (domain): [Tất cả] + mỗi domain
total = sum(len(d["rows"]) for d in PLAN["domains"])
dtabs = '<button class="s15tab active" data-i="-1">Tất cả <span class="cnt">%d</span></button>' % total
for i, d in enumerate(PLAN["domains"]):
    dtabs += '<button class="s15tab" data-i="%d">%s <span class="cnt">%d</span></button>' % (i, esc(d["short"]), len(d["rows"]))

# tab bar 2 (dev = Implement PIC)
from collections import Counter
devcnt = Counter((r["impl_pic"].strip() or "(để trống)") for d in PLAN["domains"] for r in d["rows"])
DEV_ORDER = ["Minh", "Đạt09", "Khoa", "Hưng", "(để trống)"]
dev_list = [p for p in DEV_ORDER if p in devcnt] + [p for p in devcnt if p not in DEV_ORDER]
ptabs = ""
for p in dev_list:
    lbl = "(chưa gán)" if p == "(để trống)" else p
    ptabs += '<button class="s15tab" data-pic="%s">%s <span class="cnt">%d</span></button>' % (esc(p), esc(lbl), devcnt[p])

TABCSS = ("<style>"
  ".s15tabwrap{border-bottom:1px solid var(--border);margin:8px 0 10px}"
  ".s15tabs{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:3px}"
  ".s15lbl{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--text-dim);margin-right:8px;min-width:50px}"
  ".s15tab{padding:6px 11px;border:1px solid var(--border);border-bottom:none;border-radius:7px 7px 0 0;"
  "background:var(--bg-header);color:var(--text-dim);cursor:pointer;font:600 12.5px system-ui,sans-serif;position:relative;top:1px}"
  ".s15tab:hover{color:var(--text)}"
  ".s15tab.active{background:var(--accent);color:#fff}"
  ".s15tab .cnt{font-size:10.5px;opacity:.85;font-variant-numeric:tabular-nums}"
  ":root[data-theme=\"dark\"] .s15tab.active{color:#10201c}"
  "@media (prefers-color-scheme:dark){.s15tab.active{color:#10201c}}"
  ":root[data-theme=\"light\"] .s15tab.active{color:#fff}"
  ".s15dom{font-size:11.5px;color:var(--text-dim);margin:0 0 6px}"
  "</style>")

ASSIGN_RENDER = r"""(function(){
var PLAN = JSON.parse(document.getElementById('s15-data').textContent);
var TLBL={"一覧 (list)":["pill-open","list"],"登録/編集 (edit)":["pill-draft","edit"],"明細 (details)":["pill-merged","details"],"特殊 (special)":["pill-pinned","special"]};
var STP={done:["pill-approved","✅"],wip:["pill-changes","🔵"],todo:["pill-todo","⚪"]};
var TO=["一覧 (list)","登録/編集 (edit)","明細 (details)","特殊 (special)"], LBL={"一覧 (list)":"list","登録/編集 (edit)":"edit","明細 (details)":"details","特殊 (special)":"special"};
var DORDER=["Khoa","Đạt","Minh","Hưng","Biên","Sơn","Bồn"];
var BASE=PLAN.backlogBase;
var ST={impl:{},test:{},updated:""};
var RT={}, RTB='', RTloaded=false;   // route React live (per-sprint) từ routes-s15.json
function reactUrl(r){ if(RTloaded){ var rt=RT[String(r.sid)]; return rt?(RTB+rt):''; } return r.react_url||''; }
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function allRows(){ return PLAN.domains.reduce(function(a,d){return a.concat(d.rows);},[]); }
function livePic(r){ var x=ST.impl[String(r.parent)]; return (x&&x.pic)||'(chưa gán)'; }
function implSt(r){ var x=ST.impl[String(r.parent)]; return x&&x.st; }
function testRec(r){ return ST.test[String(r.test)]; }
function tk(lbl,n){ if(!n) return ''; var b=/^\d+$/.test(String(n))?('<a href="'+BASE+n+'" target="_blank" rel="noopener">'+n+'</a>'):('<span class="ticket">'+esc(n)+'</span>'); return '<span style="color:var(--text-dim);font-size:10px">'+lbl+'</span> '+b; }
function stpill(st){ if(!st) return ''; var x=STP[st]||STP.todo; return ' <span class="pill '+x[0]+'" title="'+st+'">'+x[1]+'</span>'; }
function picCell(name,st){ if(!name||name==='(chưa gán)') return '<span class="cf-na">(chưa gán)</span>'; return '<span class="dev">'+esc(name)+'</span>'+stpill(st); }
function rowHtml(r){
  var t=TLBL[r.type]||['pill-draft',r.type];
  var tickets=[tk('親',r.parent),tk('実',r.impl),tk('テ',r.test)].filter(Boolean).join(' <span style="color:var(--border)">·</span> ');
  var ang = r.angular_url ? '<a href="'+esc(r.angular_url)+'" target="_blank" rel="noopener" title="'+esc(r.angular_url)+'">'+esc(r.angular_url.replace(/^https?:\/\/[^/]+/,''))+'</a>' : '<span class="cf-na">—</span>';
  var ru = reactUrl(r);
  var rea = ru ? '<a href="'+esc(ru)+'" target="_blank" rel="noopener" title="'+esc(ru)+'">'+esc(ru.replace(/^https?:\/\/[^/]+/,''))+'</a>' : '<span class="cf-na">—</span>';
  var tr=testRec(r);
  return '<tr>'
    +'<td><span class="ticket">'+esc(r.sid)+'</span></td>'
    +'<td>'+ang+'</td>'
    +'<td>'+rea+'</td>'
    +'<td><span class="jp-cell">'+esc(r.name)+'</span></td>'
    +'<td><span class="pill '+t[0]+'">'+t[1]+'</span></td>'
    +'<td class="conflict-cell" style="white-space:nowrap">'+tickets+'</td>'
    +'<td>'+picCell(livePic(r),implSt(r))+'</td>'
    +'<td>'+((tr&&tr.pic)?picCell(tr.pic,tr.st):'<span class="cf-na">—</span>')+'</td>'
  +'</tr>';
}
function picOrder(cnt){
  return DORDER.filter(function(p){return cnt[p];})
    .concat(Object.keys(cnt).filter(function(p){return DORDER.indexOf(p)<0 && p!=='(chưa gán)';}))
    .concat(cnt['(chưa gán)']?['(chưa gán)']:[]);
}
function renderDevTabs(){
  var cnt={}; allRows().forEach(function(r){var p=livePic(r);cnt[p]=(cnt[p]||0)+1;});
  document.getElementById('s15devtabs').innerHTML = picOrder(cnt).map(function(p){
    return '<button class="s15tab" data-pic="'+esc(p)+'">'+esc(p)+' <span class="cnt">'+cnt[p]+'</span></button>';
  }).join('');
}
function renderAlloc(){
  var m={}; allRows().forEach(function(r){var p=livePic(r); if(!m[p]){m[p]={};TO.forEach(function(t){m[p][t]=0;});} m[p][r.type]++;});
  var head='<tr><th>PIC (Backlog)</th>'+TO.map(function(t){return '<th>'+LBL[t]+'</th>';}).join('')+'<th>Tổng</th></tr>';
  var tot={},g=0; TO.forEach(function(t){tot[t]=0;});
  var rows=picOrder(m).map(function(p){var ss=0;var c=TO.map(function(t){ss+=m[p][t];tot[t]+=m[p][t];return '<td>'+(m[p][t]||'<span class="cf-na">·</span>')+'</td>';}).join('');g+=ss;
    var pc=(p==='(chưa gán)')?'<span class="cf-na">(chưa gán)</span>':'<span class="dev">'+esc(p)+'</span>';
    return '<tr><td>'+pc+'</td>'+c+'<td><b>'+ss+'</b></td></tr>';}).join('');
  var foot='<tr style="border-top:2px solid var(--border)"><td><b>Tổng</b></td>'+TO.map(function(t){return '<td><b>'+tot[t]+'</b></td>';}).join('')+'<td><b>'+g+'</b></td></tr>';
  document.getElementById('s15alloc').innerHTML='<div class="scroll-wrap" style="max-width:560px"><table style="min-width:480px"><thead>'+head+'</thead><tbody>'+rows+foot+'</tbody></table></div>';
}
function renderView(btn){
  var di=btn.getAttribute('data-i'), pk=btn.getAttribute('data-pic'), rows, label;
  if(pk!=null){ rows=allRows().filter(function(r){return livePic(r)===pk;}); label='Dev: '+pk+' — '+rows.length+' màn (Backlog assignee)'; }
  else { var i=parseInt(di,10); rows=i<0?allRows():PLAN.domains[i].rows; label=i<0?('Tất cả '+rows.length+' màn / '+PLAN.domains.length+' domain'):(PLAN.domains[i].domain+' — '+rows.length+' màn'); }
  document.getElementById('s15tbody').innerHTML=rows.map(rowHtml).join('');
  document.getElementById('s15dom').textContent=label;
  [].forEach.call(document.querySelectorAll('.s15tab'),function(b){b.classList.toggle('active',b===btn);});
}
function renderAll(){
  var cur=document.querySelector('.s15tab.active'); var pk=cur&&cur.getAttribute('data-pic'); var di=cur&&cur.getAttribute('data-i');
  renderDevTabs(); renderAlloc();
  var keep = pk!=null ? document.querySelector('.s15tab[data-pic="'+(window.CSS&&CSS.escape?CSS.escape(pk):pk)+'"]')
                      : (di!=null ? document.querySelector('.s15tab[data-i="'+di+'"]') : null);
  renderView(keep || document.querySelector('.s15tab[data-i="-1"]'));
  var mm=document.getElementById('s15meta'); if(mm) mm.textContent = ST.updated ? ('PIC/status theo Backlog assignee · cập nhật '+ST.updated) : 'đang tải trạng thái Backlog…';
}
document.querySelector('.s15tabwrap').addEventListener('click',function(e){var b=e.target.closest('.s15tab'); if(b) renderView(b);});
function fetchStatus(){
  var U='https://raw.githubusercontent.com/nguyenducbien-art/w3-pr-tracking-tables/data/s15-status.json';
  return fetch(U+'?t='+Date.now()).then(function(r){return r.json();}).then(function(d){ST=d;renderAll();})
    .catch(function(){ renderAll(); });
}
function fetchRoutes(){
  var U='https://raw.githubusercontent.com/nguyenducbien-art/w3-pr-tracking-tables/data/routes-s15.json';
  return fetch(U+'?t='+Date.now()).then(function(r){return r.json();}).then(function(d){
    RT=d.routes||{}; RTB=d.base||''; RTloaded=true;
    var rm=document.getElementById('s15rmeta'); if(rm) rm.textContent='URL React = per-sprint stg (nhánh '+((d.branch||'').split('/').pop())+', cập nhật '+(d.updated||'')+')';
    renderAll();
  }).catch(function(){ /* giữ react_url tĩnh đã nhúng */ });
}
renderAll(); fetchStatus(); fetchRoutes(); setInterval(fetchStatus,60000); setInterval(fetchRoutes,60000);
})();
"""

body = ('<div class="page">'
  + '<div class="page-header"><h1>Phân công việc — Sprint 15</h1>'
  + '<span class="meta">' + str(total) + ' màn · ' + str(len(PLAN["domains"])) + ' domain · PIC LIVE từ Backlog</span></div>'
  + '<div id="s15meta" class="subtitle" style="margin-bottom:2px;font-style:italic">đang tải trạng thái Backlog…</div>'
  + '<div id="s15rmeta" class="subtitle" style="margin-bottom:6px;font-style:italic">đang tải route React…</div>'
  + '<div class="subtitle">' + esc(PLAN["note"]) + '</div>'
  + '<details style="margin-bottom:10px"><summary style="cursor:pointer;font-size:13px;font-weight:600">Phân bổ theo Backlog assignee (live)</summary>'
  + '<div id="s15alloc" style="margin-top:8px"></div></details>'
  + '<div class="s15tabwrap">'
  +   '<div class="s15tabs"><span class="s15lbl">Domain</span>' + dtabs + '</div>'
  +   '<div class="s15tabs"><span class="s15lbl">Dev</span><span id="s15devtabs"></span></div>'
  + '</div>'
  + '<div id="s15dom" class="s15dom"></div>'
  + '<div class="scroll-wrap"><table style="min-width:1220px"><thead><tr>'
  + '<th>Screen ID / URL</th><th>AngularJS stg</th><th>React (per-sprint)</th><th>Tên màn</th><th>Loại</th><th>Ticket (親 / 実装 / テスト)</th>'
  + '<th>Impl PIC (Backlog)</th><th>Test PIC (Backlog)</th>'
  + '</tr></thead><tbody id="s15tbody"></tbody></table></div>'
  + '<div class="footnote">Loại màn: <span class="pill pill-open">list</span> 一覧 · '
  + '<span class="pill pill-draft">edit</span> 登録/編集 · <span class="pill pill-merged">details</span> 明細 · '
  + '<span class="pill pill-pinned">special</span> 特殊. &nbsp; Ticket: <b>親</b>=cha · <b>実装</b>=implement＆単体テスト · <b>テ</b>=テスト実施 (click mở Backlog).<br>'
  + '<b>Impl PIC / Test PIC = assignee THẬT trên Backlog</b> (親 / テスト実施), tự cập nhật mỗi 5p; status: '
  + '<span class="pill pill-approved">✅</span> Resolved/Closed · <span class="pill pill-changes">🔵</span> In Progress · '
  + '<span class="pill pill-todo">⚪</span> Open · “(chưa gán)” = chưa ai nhận trên Backlog.<br>'
  + 'Screen list / 画面名 / loại / ticket / URL là cấu hình cố định (<code>s15-plan.json</code>); '
  + '<b>Table A</b> phía trên = PR tracking (nhánh r20260810).</div>'
  + '</div>')

doc = ('<!DOCTYPE html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n<title>Phân công — Sprint 15</title>\n'
       + FAVICON + '\n' + css + '\n' + TABCSS + '\n</head>\n<body>\n'
       + NAV + '\n<div id="app"></div>\n' + body + '\n' + MASCOT + '\n'
       + '<script id="table-data" type="application/json"></script>\n'
       + '<script>' + PR_RENDER + '</script>\n'
       + '<script id="s15-data" type="application/json">' + json.dumps(PLAN, ensure_ascii=False) + '</script>\n'
       + '<script>' + ASSIGN_RENDER + '</script>\n</body>\n</html>')
open("s15.html", "w").write(doc)
print("built s15.html | Table A PR (fetch data-s15.json) + phân công %d màn / %d domain" % (total, len(PLAN["domains"])))
