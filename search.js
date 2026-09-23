/*
 * W3 PR Tracking — search by ticket number or PR number across every sprint page.
 * Loaded on every page by tools/sprints.py nav_html():
 *   <script src="search.js?v=..." data-sprints='[{label,href,data,screens?,plan?,rlabel?}]' defer>
 * - Search box is injected into the top nav; "/" focuses it, Enter searches, Esc closes the modal.
 * - Data: sprint JSON from the `data` branch (raw.githubusercontent) + s15-plan.json (same origin).
 * - Result links carry "#q=<n>": the target page scrolls to and flashes the matching rows.
 */
(function () {
  'use strict';
  var me = document.currentScript;
  var SPR = [];
  try { SPR = JSON.parse((me && me.getAttribute('data-sprints')) || '[]'); } catch (e) { SPR = []; }
  var RAW = 'https://raw.githubusercontent.com/nguyenducbien-art/w3-pr-tracking-tables/data/';
  var BACKLOG = 'https://dialog-inc.backlog.com/view/ANGULAR_REPLACE-';
  var GH = 'https://github.com/dialog-inc/w3package_v2/';
  var BR = { base: '→base', r629: '→r0629', r713: '→r0713', r727: '→r0727', r810: '→r0810', scaffold: '→scaffold' };
  var PILL = { merged: 'MERGED', draft: 'DRAFT', approved: 'APPROVED', changes: 'CHANGES', open: 'OPEN' };
  var ROLE = { parent: '親 (parent)', impl: '実装 (implementation)', test: 'テスト実施 (test execution)' };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function url(u) { return /^https?:\/\//i.test(String(u || '')) ? esc(u) : '#'; }

  // ---- styles (reuse page tokens from _head.html so light/dark both work) ----
  var css = document.createElement('style');
  css.textContent = [
    '.srch-form{margin-left:auto;display:flex;align-items:center}',
    '.srch-form input{font:500 12.5px -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;width:210px;max-width:46vw;',
    ' padding:5px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text)}',
    '.srch-form input:focus{outline:2px solid color-mix(in srgb,var(--accent) 55%,transparent);outline-offset:1px;border-color:var(--accent)}',
    '.srch-back{position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.45);display:flex;align-items:flex-start;justify-content:center;padding:6vh 12px 12px}',
    '.srch-modal{width:min(820px,100%);min-width:0;max-height:86vh;display:flex;flex-direction:column;background:var(--bg-table);color:var(--text);',
    ' border:1px solid var(--border);border-radius:10px;box-shadow:0 18px 50px rgba(0,0,0,.35)}',
    '.srch-head{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border)}',
    '.srch-head h2{font-size:14px;font-weight:700;margin:0;flex:1}',
    '.srch-x{border:0;background:transparent;color:var(--text-dim);font-size:22px;line-height:1;cursor:pointer;padding:0 4px;border-radius:4px}',
    '.srch-x:hover{color:var(--text);background:var(--bg-header)}',
    '.srch-body{overflow:auto;padding:12px 16px 16px;font-size:12.5px}',
    '.srch-sum{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 12px;color:var(--text-dim)}',
    '.srch-chip{display:inline-block;padding:2px 9px;border-radius:999px;border:1px solid var(--border);color:var(--text);font-weight:600;text-decoration:none}',
    '.srch-chip:hover{border-color:var(--accent);text-decoration:none}',
    '.srch-card{border:1px solid var(--border);border-radius:8px;padding:10px 12px;margin:0 0 10px;background:var(--bg);min-width:0;overflow-wrap:anywhere}',
    '.srch-meta{font-size:11.5px;color:var(--text-dim);margin-bottom:4px}',
    '.srch-meta a{font-weight:700}',
    '.srch-ttl{font-size:13px;margin-bottom:6px;overflow-wrap:anywhere}',
    // _head.html styles every table for the wide PR grid (min-width 1500px, nowrap cells, zebra rows)
    // → reset those for the small PR list inside the modal.
    '.srch-prs{border-collapse:collapse;width:100%;min-width:0;font-size:12px}',
    '.srch-prs tbody tr,.srch-prs tbody tr:nth-child(even),.srch-prs tbody tr:hover{background:none;border:0}',
    '.srch-prs td{padding:3px 8px 3px 0;vertical-align:top;border:0;white-space:normal;font-size:12px}',
    '.srch-prs td:first-child{padding-left:0;white-space:nowrap;color:var(--text-dim);width:1%}',
    '.srch-prs tr.srch-hit td{background:color-mix(in srgb,var(--accent) 14%,transparent)}',
    '.srch-foot{margin-top:6px;font-size:11.5px;color:var(--text-dim);display:flex;flex-wrap:wrap;gap:4px 14px}',
    '.srch-none p{margin:0 0 8px}',
    '.srch-links{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:4px}',
    '.srch-note{font-size:11px;color:var(--text-dim);margin-top:10px}',
    'tr.srch-flash td{animation:srchflash 3.2s ease-out}',
    '@keyframes srchflash{0%,55%{background:color-mix(in srgb,var(--accent) 30%,transparent)}100%{background:transparent}}',
    '@media (max-width:640px){.srch-form{margin-left:0;width:100%}.srch-form input{width:100%;max-width:none}}'
  ].join('\n');
  document.head.appendChild(css);

  // ---- search box in the nav ----
  var inner = document.querySelector('.topnav-inner');
  if (!inner) return;
  var form = document.createElement('form');
  form.className = 'srch-form';
  form.setAttribute('role', 'search');
  form.innerHTML = '<input type="search" inputmode="numeric" autocomplete="off" '
    + 'placeholder="Tìm số ticket / PR   ( / )" aria-label="Tìm theo số ticket hoặc số PR">';
  inner.appendChild(form);
  var input = form.querySelector('input');

  // ---- data loading (cached ~2 min) ----
  var cache = null, cacheAt = 0;
  function getJSON(url) {
    return fetch(url + (url.indexOf('?') < 0 ? '?' : '&') + 't=' + Date.now())
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }
  function loadAll() {
    if (cache && Date.now() - cacheAt < 120000) return cache;
    cacheAt = Date.now();
    cache = Promise.all(SPR.map(function (s) {
      var jobs = [
        s.data ? getJSON(RAW + s.data).catch(function (e) { return { _err: String(e) }; }) : Promise.resolve(null),
        s.screens ? getJSON(RAW + s.screens).catch(function () { return null; }) : Promise.resolve(null),
        s.plan ? getJSON(s.plan).catch(function () { return null; }) : Promise.resolve(null)
      ];
      return Promise.all(jobs).then(function (x) { return { s: s, D: x[0], SC: x[1], PL: x[2] }; });
    }));
    return cache;
  }

  // ---- search ----
  function prLists(r) {
    var out = [];
    Object.keys(r).forEach(function (k) {
      var v = r[k];
      if (Array.isArray(v) && v.length && v[0] && typeof v[0] === 'object' && 'num' in v[0]) out.push({ key: k, list: v });
    });
    out.sort(function (a, b) { return (a.key === 'base' ? 0 : 1) - (b.key === 'base' ? 0 : 1); });
    return out;
  }
  function find(all, n) {
    var hits = [], extra = [], errs = [];
    all.forEach(function (x) {
      var s = x.s, D = x.D;
      if (D && D._err) errs.push(s.label);
      if (D && !D._err) {
        var com = new Set(D.common || []);
        (D.main || []).forEach(function (r) {
          var prs = prLists(r);
          var tk = String(r.ticket) === n;
          var pr = prs.some(function (l) { return l.list.some(function (p) { return String(p.num) === n; }); });
          if (tk || pr) hits.push({ s: s, D: D, r: r, prs: prs, table: com.has(r.ticket) ? 'Bảng 1 — Common component' : 'Bảng 2 — Màn / Fix thường' });
        });
        (D.scaffold || []).forEach(function (r) {
          var p = r.pr || {};
          if (String(r.ticket) === n || String(p.num) === n)
            hits.push({ s: s, D: D, r: r, prs: [{ key: 'scaffold', list: [p] }], table: 'Bảng phụ — scaffold' });
        });
      }
      if (x.SC && x.SC.screens) x.SC.screens.forEach(function (sc) {
        if (String(sc.ticket) === n) extra.push({ s: s, kind: 'screen', sc: sc });
      });
      if (x.PL && x.PL.domains) x.PL.domains.forEach(function (d) {
        (d.rows || []).forEach(function (row) {
          ['parent', 'impl', 'test'].forEach(function (k) {
            if (String(row[k]) === n) extra.push({ s: s, kind: 'plan', row: row, role: k, dom: d.domain });
          });
        });
      });
    });
    return { hits: hits, extra: extra, errs: errs };
  }

  // ---- rendering ----
  function pill(st) { return '<span class="pill pill-' + esc(PILL[st] ? st : 'open') + '">' + (PILL[st] || 'OPEN') + '</span>'; }
  function prLine(p, U, n) {
    var cf = p.cf === 'bad' ? '<span class="cf-bad" title="CONFLICTING">✗ conflict</span>'
      : (p.cf === 'unk' ? '<span class="cf-unk">?</span>' : '<span class="cf-ok">✓</span>');
    var stat = [];
    if (p.nc != null) stat.push(p.nc + 'c');
    if (p.fc != null) stat.push(p.fc + 'f');
    if (p.add != null || p.del != null) stat.push('+' + (p.add || 0) + '−' + (p.del || 0));
    return '<a href="' + url(U + p.num) + '" target="_blank" rel="noopener">#' + esc(p.num) + '</a>'
      + (p.cr ? ' <span class="date-cell">(' + esc(p.cr) + ')</span>' : '')
      + ' ' + pill(p.st) + ' ' + cf + (stat.length ? ' <span class="date-cell">' + esc(stat.join(' ')) + '</span>' : '');
  }
  function rvw(r) {
    if (!r) return '—';
    var o = [];
    (r.ap || []).forEach(function (x) { o.push('<span class="rv-ap">✓' + esc(x) + '</span>'); });
    (r.ch || []).forEach(function (x) { o.push('<span class="rv-ch">✗' + esc(x) + '</span>'); });
    (r.pd || []).forEach(function (x) { o.push('<span class="rv-pd">⏳' + esc(x) + '</span>'); });
    return o.length ? o.join(' ') : '—';
  }
  function pageLink(s, n) { return esc(s.href) + '#q=' + encodeURIComponent(n); }
  function card(h, n) {
    var r = h.r, U = h.D.prUrlBase || (GH + 'pull/');
    var rows = h.prs.map(function (l) {
      var lbl = (l.key === 'r810' && h.s.rlabel) ? h.s.rlabel : (BR[l.key] || ('→' + l.key));
      return l.list.map(function (p) {
        return '<tr' + (String(p.num) === n ? ' class="srch-hit"' : '') + '><td>' + esc(lbl) + '</td><td>' + prLine(p, U, n) + '</td></tr>';
      }).join('');
    }).join('');
    var tk = /^\d+$/.test(String(r.ticket))
      ? '<a class="ticket" href="' + BACKLOG + esc(r.ticket) + '" target="_blank" rel="noopener" title="Mở ticket trên Backlog">' + esc(r.ticket) + ' ↗</a>'
      : '<span class="ticket">' + esc(r.ticket) + '</span>';
    var foot = ['Reviewers: ' + rvw(r.rvw)];
    if (r.drvurl) foot.push('Report: <a class="report-yes" href="' + url(r.drvurl) + '" target="_blank" rel="noopener">✓ mở</a>');
    else if ('drive' in r) foot.push('Report: ' + (r.drive ? '<span class="report-yes">✓</span>' : '<span class="report-no">—</span>'));
    if (r.cop != null) foot.push('Copilot ' + esc(r.cop) + (r.unres ? ' · <span class="cf-bad">unres ' + esc(r.unres) + '</span>' : ' · unres 0'));
    if (r.sid) foot.push('Screen <span class="ticket">' + esc(r.sid) + '</span>');
    return '<div class="srch-card">'
      + '<div class="srch-meta"><a href="' + pageLink(h.s, n) + '">' + esc(h.s.label) + '</a> · ' + esc(h.table) + '</div>'
      + '<div class="srch-ttl">' + tk + ' <span class="dev' + (r.dev === 'bien' ? ' dev-bien' : '') + '">' + esc(r.dev) + '</span> — ' + esc(r.title) + '</div>'
      + '<table class="srch-prs"><tbody>' + rows + '</tbody></table>'
      + '<div class="srch-foot">' + foot.map(function (x) { return '<span>' + x + '</span>'; }).join('') + '</div>'
      + '</div>';
  }
  function extraCard(e, n) {
    if (e.kind === 'screen') {
      var sc = e.sc;
      return '<div class="srch-card"><div class="srch-meta"><a href="' + pageLink(e.s, n) + '">' + esc(e.s.label) + '</a> · Danh sách màn</div>'
        + '<div class="srch-ttl">Màn <span class="ticket">' + esc(sc.sid) + '</span> ' + esc(sc.name)
        + (sc.route ? ' <span class="date-cell">' + esc(sc.route) + '</span>' : '') + '</div>'
        + '<div class="srch-foot"><span>PIC: ' + esc(sc.pic || '—') + ' (' + esc(sc.st || '—') + ')</span>'
        + '<span>Test: ' + esc(sc.tester || '—') + ' (' + esc(sc.test || '—') + ')</span></div></div>';
    }
    var row = e.row;
    var links = [];
    if (row.angular_url) links.push('<a href="' + url(row.angular_url) + '" target="_blank" rel="noopener">AngularJS ↗</a>');
    if (row.react_url) links.push('<a href="' + url(row.react_url) + '" target="_blank" rel="noopener">React ↗</a>');
    return '<div class="srch-card"><div class="srch-meta"><a href="' + pageLink(e.s, n) + '">' + esc(e.s.label) + '</a> · Phân công việc · ' + esc(e.dom) + '</div>'
      + '<div class="srch-ttl">Màn <span class="ticket">' + esc(row.sid) + '</span> ' + esc(row.name) + ' — ticket ' + esc(n) + ' là <b>' + esc(ROLE[e.role]) + '</b></div>'
      + '<div class="srch-foot"><span>親 ' + esc(row.parent || '—') + ' · 実 ' + esc(row.impl || '—') + ' · テ ' + esc(row.test || '—') + '</span>'
      + '<span>Impl PIC (plan): ' + esc(row.impl_pic || '—') + '</span>' + (links.length ? '<span>' + links.join(' · ') + '</span>' : '') + '</div></div>';
  }
  function notFound(n, errs) {
    return '<div class="srch-card srch-none">'
      + '<p>Không thấy <b>' + esc(n) + '</b> trong bảng nào (' + SPR.length + ' sprint, kể cả danh sách màn S14 và phân công S15).</p>'
      + '<p class="srch-note" style="margin-top:0">Lý do hay gặp: PR bị CLOSED (bảng bỏ PR đóng) · ticket được sửa "ké" trong PR của ticket khác'
      + ' (bảng lấy số ticket từ tên nhánh / title PR) · ticket bị ẩn theo yêu cầu · PR đồng bộ (sync) bị loại · PR thuộc repo/nhánh khác mimosa/frontend.</p>'
      + '<div class="srch-links">'
      + '<a href="' + GH + 'pull/' + esc(n) + '" target="_blank" rel="noopener">PR #' + esc(n) + ' trên GitHub ↗</a>'
      + '<a href="' + GH + 'pulls?q=' + encodeURIComponent('is:pr ANGULAR_REPLACE-' + n) + '" target="_blank" rel="noopener">PR có ANGULAR_REPLACE-' + esc(n) + ' ↗</a>'
      + '<a href="' + BACKLOG + esc(n) + '" target="_blank" rel="noopener">Ticket ' + esc(n) + ' trên Backlog ↗</a>'
      + '</div></div>' + errNote(errs);
  }
  function errNote(errs) {
    return errs.length ? '<p class="srch-note">⚠️ Không tải được dữ liệu: ' + esc(errs.join(', ')) + ' — kết quả có thể thiếu.</p>' : '';
  }

  // ---- modal ----
  var back = null, lastFocus = null;
  function close() {
    if (!back) return;
    back.remove(); back = null;
    document.removeEventListener('keydown', onKey, true);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function onKey(e) { if (e.key === 'Escape') { e.preventDefault(); close(); } }
  function open(title, html) {
    close();
    lastFocus = document.activeElement;
    back = document.createElement('div');
    back.className = 'srch-back';
    back.innerHTML = '<div class="srch-modal" role="dialog" aria-modal="true" aria-labelledby="srch-h">'
      + '<div class="srch-head"><h2 id="srch-h">' + title + '</h2><button type="button" class="srch-x" aria-label="Đóng">×</button></div>'
      + '<div class="srch-body">' + html + '</div></div>';
    back.addEventListener('click', function (e) { if (e.target === back) close(); });
    back.querySelector('.srch-x').addEventListener('click', close);
    document.body.appendChild(back);
    document.addEventListener('keydown', onKey, true);
    back.querySelector('.srch-x').focus();
  }
  function setBody(html) { if (back) back.querySelector('.srch-body').innerHTML = html; }

  function run(q) {
    var n = String(q || '').replace(/[^0-9]/g, '').replace(/^0+(?=\d)/, '');
    if (!n) return;
    open('Kết quả tìm “' + esc(n) + '”', '<p class="srch-note">Đang tải dữ liệu các sprint…</p>');
    loadAll().then(function (all) {
      var res = find(all, n);
      if (!res.hits.length && !res.extra.length) { setBody(notFound(n, res.errs)); return; }
      var seen = [], chips = '';
      res.hits.concat(res.extra).forEach(function (h) {
        if (seen.indexOf(h.s.label) < 0) { seen.push(h.s.label); chips += '<a class="srch-chip" href="' + pageLink(h.s, n) + '">' + esc(h.s.label) + '</a>'; }
      });
      var upd = all.filter(function (x) { return x.D && x.D.updated && seen.indexOf(x.s.label) >= 0; })
        .map(function (x) { return x.s.label + ' ' + x.D.updated; });
      setBody('<div class="srch-sum">Có ở: ' + chips + '</div>'
        + res.hits.map(function (h) { return card(h, n); }).join('')
        + res.extra.map(function (e) { return extraCard(e, n); }).join('')
        + '<p class="srch-note">Dữ liệu cập nhật: ' + esc(upd.join(' · ')) + '. Bấm tên sprint để mở trang và nhảy tới dòng đó.</p>'
        + errNote(res.errs));
    }).catch(function (e) {
      cache = null;
      setBody('<p class="cf-bad">Lỗi tải dữ liệu: ' + esc(e) + '</p>');
    });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); run(input.value); });
  document.addEventListener('keydown', function (e) {
    var t = e.target, typing = t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if (e.key === '/' && !typing && !back && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); input.focus(); input.select(); }
  });

  // ---- "#q=<n>" on arrival: scroll to + flash matching rows once the tables have rendered ----
  function flash(n) {
    // Pages re-render their tables asynchronously (e.g. s15 re-renders the assignment table when
    // Backlog status / routes arrive) → keep matching for a few seconds and re-apply to new nodes.
    var t0 = Date.now(), first = null, last = null;
    function inView(tr) { var r = tr.getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; }
    (function tick() {
      var vis = [].filter.call(document.querySelectorAll('tbody tr'), function (tr) {
        if (tr.closest('.srch-modal') || tr.offsetParent === null) return false;
        var t = tr.querySelector('.ticket');
        if (t && t.textContent.trim() === n) return true;
        return [].some.call(tr.querySelectorAll('a'), function (a) {
          var x = a.textContent.trim();
          return x === '#' + n || (x === n && /backlog/.test(a.href));
        });
      });
      vis.forEach(function (tr) { tr.classList.add('srch-flash'); });
      if (vis.length) {
        if (!first) first = Date.now();
        // scroll on first hit, when a re-render replaced the row, or while the layout is still settling
        if (vis[0] !== last || (Date.now() - first < 1800 && !inView(vis[0]))) {
          if (!inView(vis[0])) vis[0].scrollIntoView({ block: 'center' });
          last = vis[0];
        }
      }
      if (Date.now() - (first || t0) < (first ? 6000 : 15000)) setTimeout(tick, 250);
    })();
  }
  function fromHash() {
    // "#q=<n>"    → jump to + flash the rows on this page (links inside the result modal)
    // "#find=<n>" → open the result modal directly (shareable search link)
    var m = /(?:^|[#&])q=(\d+)/.exec(location.hash);
    if (m) { input.value = m[1]; flash(m[1]); }
    var f = /(?:^|[#&])find=(\d+)/.exec(location.hash);
    if (f) { input.value = f[1]; run(f[1]); }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
