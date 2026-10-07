# -*- coding: utf-8 -*-
# Build kanaya.html — page tổng hợp "PR đang chờ Kanaya review", gom từ data của MỌI sprint (nhánh data).
# Không có data riêng: JS fetch các data-sNN.json rồi lọc PR chưa MERGED mà reviewer `kanayam` đang ở
# trạng thái được request (pd). Ưu tiên reviewer theo TỪNG PR (p.rv — fetch_build_s14/15/17/18/19 ghi từ 06/10);
# data đông lạnh (s12/s13) không có p.rv → lùi về reviewer gộp theo dòng ticket (r.rvw).
# Usage: python3 build_kanaya.py
import json, re, ast
from sprints import nav_html, SPRINTS

NAV = nav_html("Chờ Kanaya")
css = re.search(r'<style>.*?</style>', open("_head.html").read(), re.S).group(0)
MASCOT = ('<script src="https://nguyenducbien-art.github.io/pixel-pets/pixel-pets.js" '
          'data-min="2" data-max="5" defer></script>')
FAVICON = ""
for _l in open("build_s14.py"):
    if _l.startswith("FAVICON = "):
        FAVICON = ast.literal_eval(re.match(r'\s*(".*")', _l[len("FAVICON = "):]).group(1)); break

JS = r"""
var WHO='kanayam';
var SPRINTS=__SPRINTS__;
var RAW='https://raw.githubusercontent.com/nguyenducbien-art/w3-pr-tracking-tables/data/';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function tkLink(t){var s=String(t==null?'':t);return /^\d+$/.test(s)
  ?'<a class="ticket" href="https://dialog-inc.backlog.com/view/ANGULAR_REPLACE-'+s+'" target="_blank" rel="noopener" title="Mở ticket '+s+' trên Backlog">'+s+'</a>'
  :'<span class="ticket">'+esc(s)+'</span>';}
var PILL={merged:['merged','MERGED'],draft:['draft','DRAFT'],approved:['approved','APPROVED'],changes:['changes','CHANGES'],open:['open','OPEN']};
function pill(st){var x=PILL[st]||PILL.open;return '<span class="pill pill-'+x[0]+'">'+x[1]+'</span>';}
function has(a){return (a||[]).indexOf(WHO)>=0;}

// Collect every not-merged PR on which WHO is a requested (pending) reviewer.
function collect(S,D){
  var out=[], common={}; (D.common||[]).forEach(function(t){common[t]=1;});
  function take(r,p,target,kind){
    if(!p||p.st==='merged') return;
    var rv=p.rv||r.rvw||{};            // per-PR reviewers when available, else row-level (frozen data)
    if(!has(rv.pd)) return;
    out.push({sprint:S.label,href:S.href,ticket:r.ticket,dev:r.dev,num:p.num,st:p.st,cf:p.cf,cr:p.cr||'',
      nc:p.nc,fc:p.fc,add:p.add,del:p.del,target:target,kind:kind,
      again:has(rv.ch)?'ch':(has(rv.ap)?'ap':''),approx:!p.rv,
      drvurl:r.drvurl,drive:r.drive,unres:r.unres||0,title:r.title||'',url:D.prUrlBase});
  }
  (D.main||[]).forEach(function(r){
    var kind=common[r.ticket]?'common':'màn/fix';
    (r.base||[]).forEach(function(p){take(r,p,'base',kind);});
    ['r629','r713','r727','r810'].forEach(function(k){(r[k]||[]).forEach(function(p){take(r,p,'r',kind);});});
  });
  (D.scaffold||[]).forEach(function(r){take(r,r.pr,'scaffold','scaffold');});
  return out;
}
function row(x){
  var mark=x.cf==='bad'?'<span class="cf-bad" title="CONFLICTING">✗</span>':(x.cf==='unk'?'<span class="cf-unk">?</span>':'<span class="cf-ok" title="MERGEABLE">✓</span>');
  var meta=(x.nc!=null?' <span class="commits">'+x.nc+'c</span>':'')+(x.fc!=null?' <span class="files">'+x.fc+'f</span>':'')
    +((x.add!=null||x.del!=null)?' <span class="adds">+'+(x.add||0)+'</span><span class="dels">−'+(x.del||0)+'</span>':'');
  var wait=x.again==='ch'?'<span class="rv-pd" title="Kanaya đã request changes, đang chờ review lại"><span class="rv-ch" style="margin:0">✗</span>→⏳ review lại</span>'
    :(x.again==='ap'?'<span class="rv-pd" title="Kanaya đã approve, được mời review lại"><span class="rv-ap" style="margin:0">✓</span>→⏳ review lại</span>'
    :'<span class="rv-pd" title="được request, chưa review lần nào">⏳ lần đầu</span>');
  if(x.approx) wait+=' <span class="cf-unk" title="Data sprint đông lạnh: reviewer gộp theo ticket, không chắc đúng PR này">?</span>';
  var rep=x.drvurl?('<a class="report-yes" href="'+esc(x.drvurl)+'" target="_blank" rel="noopener" title="Mở file report">✓ mở</a>')
    :(x.drive?'<span class="report-yes">✓</span>':'<span class="report-no">—</span>');
  var devcls=(x.dev==='bien')?'dev dev-bien':'dev';
  return '<tr data-dev="'+esc(x.dev)+'" data-target="'+x.target+'">'
    +'<td><a href="'+esc(x.url)+x.num+'" target="_blank" rel="noopener">#'+x.num+'</a>'+(x.cr?' <span class="date-cell">('+esc(x.cr)+')</span>':'')+' '+pill(x.st)+' '+mark+meta+'</td>'
    +'<td>'+wait+'</td>'
    +'<td>→'+x.target+'</td>'
    +'<td>'+tkLink(x.ticket)+'</td>'
    +'<td><span class="'+devcls+'">'+esc(x.dev)+'</span></td>'
    +'<td><a href="'+esc(x.href)+'#q='+x.num+'" title="Mở dòng này ở page sprint">'+esc(x.sprint)+'</a></td>'
    +'<td>'+esc(x.kind)+'</td>'
    +'<td>'+rep+'</td>'
    +'<td>'+(x.unres>0?'<span class="unresolved">'+x.unres+'</span>':'0')+'</td>'
    +'<td><span class="title-cell">'+esc(x.title)+'</span></td></tr>';
}
var F={dev:'',target:''};
function render(all,updated,errs){
  var seen={}; all=all.filter(function(x){if(seen[x.num])return false;seen[x.num]=1;return true;});
  all.sort(function(a,b){return a.num-b.num;});   // PR cũ nhất (chờ lâu nhất) lên đầu
  var n1=all.filter(function(x){return !x.again;}).length, bad=all.filter(function(x){return x.cf==='bad';}).length;
  function opts(key,lbl){var v={};all.forEach(function(x){v[x[key]]=(v[x[key]]||0)+1;});
    return lbl+': <select data-f="'+key+'" style="font-size:12px;padding:2px 6px;border-radius:6px;margin-right:14px"><option value="">Tất cả ('+all.length+')</option>'
      +Object.keys(v).sort().map(function(k){return '<option value="'+esc(k)+'"'+(F[key]===k?' selected':'')+'>'+(key==='target'?'→':'')+esc(k)+' ('+v[k]+')</option>';}).join('')+'</select>';}
  var html='<div class="page"><div class="page-header"><h1>⏳ PR đang chờ Kanaya review</h1>'
    +'<span class="meta">cập nhật '+esc(updated)+' · gom từ '+SPRINTS.length+' page sprint</span></div>'
    +'<div class="subtitle">Mọi PR <b>chưa MERGED</b> mà <b>'+WHO+'</b> đang được request review (GitHub “Reviewers” còn chờ) — gồm cả PR Kanaya đã request changes rồi được mời review lại. '
    +'Sắp theo số PR tăng dần (PR cũ nhất ở trên). Dữ liệu lấy từ các page sprint nên tươi theo lịch cron của từng sprint (Sprint 19: 5 phút, sprint cũ: 30 phút).</div>'
    +'<div class="stats">'
      +'<div class="stat">PR đang chờ <span class="stat-val">'+all.length+'</span></div>'
      +'<div class="stat">lần đầu <span class="stat-val">'+n1+'</span></div>'
      +'<div class="stat">review lại <span class="stat-val">'+(all.length-n1)+'</span></div>'
      +'<div class="stat">conflict <span class="stat-val warn">'+bad+'</span></div>'
    +'</div>'
    +(errs.length?'<p style="color:var(--unresolved-fg);font-size:12px">Không tải được: '+esc(errs.join(', '))+'</p>':'')
    +'<div class="devfilter" style="margin:8px 0 2px;font-size:12px;color:var(--text-dim)">'+opts('dev','Lọc dev')+opts('target','Nhánh đích')+'</div>'
    +'<div class="scroll-wrap"><table><thead><tr><th>PR</th><th>Chờ Kanaya</th><th>Nhánh đích</th><th>Ticket</th><th>Dev</th><th>Sprint</th><th>Loại</th><th>Report</th><th>Unres.</th><th>Title</th></tr></thead>'
    +'<tbody id="kb">'+(all.length?all.map(row).join(''):'<tr><td colspan="10" style="text-align:center;padding:24px">Không có PR nào đang chờ Kanaya 🎉</td></tr>')+'</tbody></table></div>'
    +'<div class="footnote">Status pill: <span class="pill pill-open">OPEN</span> <span class="pill pill-draft">DRAFT</span> <span class="pill pill-approved">APPROVED</span> <span class="pill pill-changes">CHANGES</span> · ✓ MERGEABLE / ✗ CONFLICTING.<br>'
    +'<span class="rv-pd">⏳ lần đầu</span> = được request, Kanaya chưa review lần nào · <span class="rv-pd"><span class="rv-ch" style="margin:0">✗</span>→⏳ review lại</span> = Kanaya đã request changes, đã được mời review lại.<br>'
    +'Report / Unres. (Copilot chưa resolve) là số của cả dòng ticket ở page sprint. Bấm tên sprint để mở đúng dòng ở page đó.</div></div>';
  document.getElementById('app').innerHTML=html;
  applyF();
}
function applyF(){
  [].forEach.call(document.querySelectorAll('#kb tr[data-dev]'),function(tr){
    tr.style.display=((!F.dev||tr.getAttribute('data-dev')===F.dev)&&(!F.target||tr.getAttribute('data-target')===F.target))?'':'none';});
}
document.addEventListener('change',function(e){
  var s=e.target; if(!s||!s.getAttribute||!s.getAttribute('data-f'))return;
  F[s.getAttribute('data-f')]=s.value; applyF();
});
function load(){
  var list=SPRINTS.filter(function(s){return s.data;}), errs=[], upd='';
  return Promise.all(list.map(function(S){
    return fetch(RAW+S.data+'?t='+Date.now()).then(function(r){if(!r.ok)throw 0;return r.json();})
      .then(function(D){ if((D.updated||'')>upd) upd=D.updated; return collect(S,D); })
      .catch(function(){errs.push(S.label);return [];});
  })).then(function(parts){ render([].concat.apply([],parts),upd,errs); });
}
load(); setInterval(load,60000);
document.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a[href^="http"]');
  if(a){e.preventDefault();window.open(a.href,'_blank','noopener');}
},true);
""".replace("__SPRINTS__", json.dumps([{"label": s["label"], "href": s["href"], "data": s.get("data")} for s in SPRINTS], ensure_ascii=False))

TITLE = "PR chờ Kanaya"
doc = ('<!DOCTYPE html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n<title>' + TITLE + '</title>\n' + FAVICON + '\n' + css + '\n</head>\n<body>\n'
       + NAV + '\n<div id="app"></div>\n' + MASCOT + '\n<script>' + JS + '</script>\n</body>\n</html>')
open("kanaya.html", "w").write(doc)
print("built kanaya.html")
