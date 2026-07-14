# -*- coding: utf-8 -*-
# Build SHELL (index.html + artifact) từ data.json có sẵn.
# data.json do fetch_build.py sinh. build_s13.py KHÔNG chứa data.
# Usage: python3 build_s13.py   (đọc ./data.json)
import json, re, sys
DATA = json.load(open(sys.argv[1] if len(sys.argv)>1 else "data.json"))

# CSS lấy từ _head.html (chỉ block <style>)
css = re.search(r'<style>.*?</style>', open("_head.html").read(), re.S).group(0)

RENDER_JS = r"""
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function render(D){
  var U=D.prUrlBase, COMMON=new Set(D.common), INVALID=new Set(D.invalidBase);
  var PILL={merged:['merged','MERGED'],draft:['draft','DRAFT'],approved:['approved','APPROVED'],changes:['changes','CHANGES'],open:['open','OPEN']};
  function pill(st){var x=PILL[st]||PILL.open;return '<span class="pill pill-'+x[0]+'">'+x[1]+'</span>';}
  function one(p,inv){
    var mark=p.cf==='ok'?'<span class="cf-ok">✓</span>':'<span class="cf-bad">✗</span>';
    var inb=inv?' <span class="badge-invalid" title="ルール違反">invalid</span>':'';
    return '<a href="'+U+p.num+'" target="_blank" rel="noopener">#'+p.num+'</a>'+inb+' '+pill(p.st)+' '+mark;
  }
  function cell(prs,inv){
    if(!prs||!prs.length) return '<span class="cf-na">—</span>';
    return prs.map(function(p){return one(p,inv);}).join('<br>');
  }
  function unb(n){return n>0?'<span class="unresolved">'+n+'</span>':'0';}
  function cnt(a){return a?a.length:0;}

  // ---- bảng chính ----
  var nbase=0,nr629=0,nr713=0,npr=0,totun=0,ncf=0;
  var rows=D.main.map(function(r){
    var b=r.base||[],r629=r.r629||[],r713=r.r713||[];
    nbase+=cnt(b);nr629+=cnt(r629);nr713+=cnt(r713);npr+=cnt(b)+cnt(r629)+cnt(r713);totun+=r.unres;
    [b,r629,r713].forEach(function(a){a.forEach(function(p){if(p.cf==='bad')ncf++;});});
    var devcls=(r.dev==='bien')?'dev dev-bien':'dev';
    var badge=COMMON.has(r.ticket)?' <span class="badge-common">common</span>':'';
    var rep=r.drive?'<span class="report-yes">✓</span>':'<span class="report-no">—</span>';
    return '<tr>'
      +'<td><span class="ticket">'+r.ticket+'</span>'+badge+'</td>'
      +'<td><span class="'+devcls+'">'+r.dev+'</span></td>'
      +'<td>'+cell(b,INVALID.has(r.ticket))+'</td>'
      +'<td>'+cell(r629,false)+'</td>'
      +'<td>'+cell(r713,false)+'</td>'
      +'<td><span class="date-cell">'+r.created+'</span></td>'
      +'<td><span class="kanaya-cell">—</span></td>'
      +'<td>'+rep+'</td>'
      +'<td><span class="copilot-cell">'+r.cop+'</span></td>'
      +'<td>'+unb(r.unres)+'</td>'
      +'<td><span class="title-cell">'+esc(r.title)+'</span></td>'
    +'</tr>';
  }).join('');

  // ---- bảng phụ scaffold ----
  var scfUn=0,scfCf=0;
  var scfRows=D.scaffold.map(function(r){
    scfUn+=r.unres; if(r.pr.cf==='bad')scfCf++;
    var devcls=(r.dev==='bien')?'dev dev-bien':'dev';
    return '<tr>'
      +'<td><span class="ticket">'+r.ticket+'</span></td>'
      +'<td><span class="'+devcls+'">'+r.dev+'</span></td>'
      +'<td>'+cell([r.pr],false)+'</td>'
      +'<td><span class="date-cell">'+r.created+'</span></td>'
      +'<td><span class="copilot-cell">'+r.cop+'</span></td>'
      +'<td>'+unb(r.unres)+'</td>'
      +'<td><span class="title-cell">'+esc(r.title)+'</span></td>'
    +'</tr>';
  }).join('');

  var html=''
   +'<div class="page">'
   +'<div class="page-header"><h1>Table A — Sprint 13</h1>'
     +'<span class="meta">cập nhật '+D.updated+' · repo '+D.repo+'</span></div>'
   +'<div class="subtitle">Tất cả PR (team-dev Rikkei) tạo từ <b>2026-07-13</b> nhắm vào <b>develop/base</b>, <b>r20260629</b> hoặc <b>r20260713</b> — chỉ cần có PR vào 1 trong 3 nhánh là được tính. Loại PR CLOSED và PR sync/chore/evidence.</div>'
   +'<div class="stats">'
     +'<div class="stat"><span class="stat-val">'+D.main.length+'</span> ticket</div>'
     +'<div class="stat"><span class="stat-val">'+npr+'</span> PR sống</div>'
     +'<div class="stat">→base <span class="stat-val">'+nbase+'</span></div>'
     +'<div class="stat">→r20260629 <span class="stat-val">'+nr629+'</span></div>'
     +'<div class="stat">→r20260713 <span class="stat-val">'+nr713+'</span></div>'
     +'<div class="stat">conflict <span class="stat-val warn">'+ncf+'</span></div>'
     +'<div class="stat">Copilot unresolved <span class="stat-val warn">'+totun+'</span></div>'
   +'</div>'
   +'<div class="scroll-wrap"><table><thead><tr>'
     +'<th>Ticket</th><th>Dev</th><th>→base</th><th>→r20260629</th><th>→r20260713</th>'
     +'<th>Created</th><th>Kanaya</th><th>Report</th><th>Copilot</th><th>Unres.</th><th>Title</th>'
   +'</tr></thead><tbody>'+rows+'</tbody></table></div>'
   +'<h2 style="font-size:15px;font-weight:700;margin:26px 0 4px;letter-spacing:-0.01em;">Bảng phụ — PR → '+D.scaffoldBranch.split('/').pop()+' <span style="font-weight:400;color:var(--text-dim);font-size:12px;">(giàn giáo / bake rule vào SKILL)</span></h2>'
   +'<div class="subtitle">PR trỏ vào nhánh <b>'+D.scaffoldBranch.split('/').pop()+'</b> — cập nhật giàn giáo (rules + frontend-screen-* SKILL). Loại PR sync base/r713→scaffold.</div>'
   +'<div class="stats">'
     +'<div class="stat"><span class="stat-val">'+D.scaffold.length+'</span> PR sống</div>'
     +'<div class="stat">conflict <span class="stat-val warn">'+scfCf+'</span></div>'
     +'<div class="stat">Copilot unresolved <span class="stat-val warn">'+scfUn+'</span></div>'
   +'</div>'
   +'<div class="scroll-wrap"><table style="min-width:1000px;"><thead><tr>'
     +'<th>Ticket</th><th>Dev</th><th>→scaffold</th><th>Created</th><th>Copilot</th><th>Unres.</th><th>Title</th>'
   +'</tr></thead><tbody>'+scfRows+'</tbody></table></div>'
   +'<div class="footnote">Status pill theo từng PR: '
     +'<span class="pill pill-open">OPEN</span> <span class="pill pill-draft">DRAFT</span> '
     +'<span class="pill pill-approved">APPROVED</span> <span class="pill pill-changes">CHANGES</span> '
     +'<span class="pill pill-merged">MERGED</span>.<br>'
     +'Conflict: ✓ MERGEABLE / ✗ CONFLICTING. Report ✓ = có link Drive self-review.<br>'
     +'🔴 Ticket <b>common</b> đếm Copilot chỉ từ PR→base (bỏ r713 cùng code sync).</div>'
   +'</div>';
  document.getElementById('app').innerHTML=html;
}
function fetchData(){
  return fetch('data.json?t='+Date.now()).then(function(r){return r.json();}).then(render)
    .catch(function(e){var a=document.getElementById('app'); if(!a.innerHTML) a.innerHTML='<p style="color:red;padding:20px">Fetch data.json error: '+e+'</p>';});
}
(function(){
  var el=document.getElementById('table-data');
  var txt=el?el.textContent.trim():'';
  if(txt){ try{render(JSON.parse(txt));}catch(e){document.getElementById('app').innerHTML='<p style="color:red;padding:20px">JSON error: '+e+'</p>';} return; }
  fetchData();
  setInterval(fetchData, 300000);  // tự làm mới data mỗi 5 phút (chỉ chế độ fetch/Pages)
})();
document.addEventListener('click',function(e){
  var a=e.target.closest&&e.target.closest('a[href^="http"]');
  if(a){e.preventDefault();window.open(a.href,'_blank','noopener');}
},true);
"""

TITLE = "Table A — Sprint 13"
FAVICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
           "%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%8A%3C/text%3E%3C/svg%3E\">")  # 📊

def build(inline):
    if inline:
        data_script = '<script id="table-data" type="application/json">'+json.dumps(DATA,ensure_ascii=False)+'</script>'
    else:
        data_script = '<script id="table-data" type="application/json"></script>'
    inner = ('<title>'+TITLE+'</title>\n'+FAVICON+'\n'+css+'\n'
             '<div id="app"></div>\n'+data_script+'\n<script>'+RENDER_JS+'</script>')
    return inner

# artifact = fragment + inline JSON
open("table-a-s13.html","w").write(build(True))

# hosted = full document, fetch data.json
doc = ('<!DOCTYPE html>\n<html lang="vi">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n<title>'+TITLE+'</title>\n'+FAVICON+'\n'+css+'\n</head>\n<body>\n'
       '<div id="app"></div>\n<script id="table-data" type="application/json"></script>\n<script>'+RENDER_JS+'</script>\n</body>\n</html>')
open("index.html","w").write(doc)

print("built shell: index.html (fetch) + table-a-s13.html (artifact,inline) từ data.json |",
      len(DATA["main"]),"main +",len(DATA["scaffold"]),"scaffold")
