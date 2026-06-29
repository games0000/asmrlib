#!/usr/bin/env python3
"""
app.py - DLsite 收藏浏览器
依赖: pip install flask
用法: python app.py  → 打开 http://localhost:5000
"""

import sqlite3
import json
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_from_directory

_HERE   = Path(__file__).parent
DB_PATH = _HERE / "dlsite.db"

app = Flask(__name__)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>音声ライブラリ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg:        #0c0c11;
  --surface:   #13131a;
  --card:      #18181f;
  --card-h:    #1f1f2a;
  --border:    #252530;
  --border-h:  #3a3a50;
  --accent:    #a78bfa;
  --accent-d:  #7c3aed;
  --accent-g:  linear-gradient(135deg, #a78bfa, #818cf8);
  --text:      #ede9f8;
  --sub:       #9490a8;
  --muted:     #52505e;
  --r18:       #e0191c;
  --r15:       #fb923c;
  --all:       #34d399;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-h); border-radius: 2px; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Space Grotesk', 'Noto Sans JP', sans-serif;
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ─── Sidebar ─────────────────────────────────────── */
#sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#sidebar-header {
  padding: 20px 16px 14px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 12px;
}
.logo-mark {
  font-size: 18px;
  font-weight: 700;
  background: var(--accent-g);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.logo-sub {
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.search-wrap {
  position: relative;
}
.search-wrap svg {
  position: absolute;
  left: 10px; top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}
#search {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px 8px 32px;
  color: var(--text);
  font-size: 12px;
  font-family: inherit;
  outline: none;
  transition: border-color .15s;
}
#search:focus { border-color: var(--accent-d); }
#search::placeholder { color: var(--muted); }

#sidebar-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filter-section {}
.filter-heading {
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}
.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.pill {
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 9px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  background: transparent;
  font-family: inherit;
  transition: all .15s;
  white-space: nowrap;
}
.pill:hover { border-color: var(--border-h); color: var(--text); }
.pill.on { background: var(--accent-d); border-color: var(--accent-d); color: #fff; }

.age-pill-全年齢.on { background: #065f46; border-color: var(--all); color: var(--all); }
.age-pill-R-15.on   { background: #7c2d12; border-color: var(--r15); color: var(--r15); }
.age-pill-R1.on   { background: #7f1d1d; border-color: var(--r18); color: var(--r18); }

/* ─── Main ───────────────────────────────────────── */
#main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#topbar {
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

#stats {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.03em;
}
#stats b { color: var(--accent); font-weight: 500; }

#blur-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 5px 12px;
  font-size: 11px;
  color: var(--sub);
  cursor: pointer;
  font-family: inherit;
  transition: all .2s;
}
#blur-toggle.on {
  border-color: var(--r18);
  color: var(--r18);
  background: rgba(248,113,113,.08);
}
.blur-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--muted);
  transition: background .2s;
}
#blur-toggle.on .blur-dot { background: var(--r18); }

#sort-btns { display: flex; gap: 4px; }
.sort-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 4px 11px;
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  font-family: inherit;
  transition: all .15s;
}
.sort-btn:hover { color: var(--text); border-color: var(--border-h); }
.sort-btn.on { border-color: var(--accent-d); color: var(--accent); background: rgba(124,58,237,.1); }

#grid-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px 24px;
}

#grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(172px, 1fr));
  gap: 14px;
}

/* ─── Card ───────────────────────────────────────── */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform .18s ease, border-color .18s, box-shadow .18s;
}
.card:hover {
  transform: translateY(-3px);
  border-color: var(--border-h);
  box-shadow: 0 8px 24px rgba(0,0,0,.4);
}

.card-img-wrap {
  position: relative;
  overflow: hidden;
}
.card-img-wrap img {
  width: 100%;
  aspect-ratio: 4/3;
  object-fit: cover;
  display: block;
  transition: filter .3s, transform .3s;
}
.card-img-wrap img.blurred {
  filter: blur(16px);
  transform: scale(1.08);
}
.card-img-wrap img.blurred:hover {
  filter: blur(0);
  transform: scale(1);
}

.card-age {
  position: absolute;
  top: 7px; right: 7px;
  font-size: 9px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  backdrop-filter: blur(6px);
}
.age-R18  { background: rgba(248,113,113,.25); color: var(--r18); border: 1px solid rgba(248,113,113,.3); }
.age-R-15  { background: rgba(251,146,60,.25);  color: var(--r15); border: 1px solid rgba(251,146,60,.3); }
.age-全年齢 { background: rgba(52,211,153,.2);   color: var(--all); border: 1px solid rgba(52,211,153,.25); }

.card-body {
  padding: 10px 11px 11px;
}
.card-rj {
  font-size: 9px;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.06em;
  margin-bottom: 4px;
  font-family: 'Space Grotesk', monospace;
}
.card-title {
  font-size: 11px;
  line-height: 1.45;
  color: var(--text);
  font-weight: 400;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 5px;
}
.card-cv {
  font-size: 10px;
  color: var(--sub);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-date {
  font-size: 9px;
  color: var(--muted);
  margin-top: 3px;
  font-variant-numeric: tabular-nums;
}

#empty {
  color: var(--muted);
  font-size: 13px;
  text-align: center;
  padding-top: 80px;
}

/* ─── Modal ──────────────────────────────────────── */
#modal-bg {
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,.65);
  backdrop-filter: blur(4px);
  z-index: 200;
  align-items: center;
  justify-content: center;
}
#modal-bg.open { display: flex; }

#modal {
  background: var(--surface);
  border: 1px solid var(--border-h);
  border-radius: 14px;
  width: min(580px, 92vw);
  max-height: 86vh;
  overflow-y: auto;
  position: relative;
  animation: modal-in .18s ease;
}
@keyframes modal-in {
  from { opacity: 0; transform: scale(.96) translateY(8px); }
  to   { opacity: 1; transform: scale(1)  translateY(0); }
}

#modal-close {
  position: absolute; top: 14px; right: 14px; z-index: 1;
  width: 28px; height: 28px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 50%;
  color: var(--sub);
  font-size: 13px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
#modal-close:hover { border-color: var(--border-h); color: var(--text); }

.modal-cover {
  width: 100%;
  border-radius: 12px 12px 0 0;
  overflow: hidden;
  background: var(--card);
  max-height: 240px;
}
.modal-cover img {
  width: 100%;
  max-height: 240px;
  object-fit: cover;
  display: block;
}

.modal-body { padding: 20px 22px 24px; }

.modal-rj {
  font-size: 10px;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.1em;
  margin-bottom: 6px;
}
.modal-title {
  font-size: 15px;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 14px;
}

.modal-info {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 12px;
  font-size: 12px;
  margin-bottom: 14px;
  align-items: baseline;
}
.modal-info-label { color: var(--muted); white-space: nowrap; }
.modal-info-val   { color: var(--text); }

.modal-age-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 5px;
  letter-spacing: 0.05em;
}

.modal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}
.modal-tag {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 11px;
  padding: 3px 9px;
  color: var(--sub);
  transition: border-color .12s;
}
.modal-tag:hover { border-color: var(--border-h); color: var(--text); }

.modal-desc {
  font-size: 12px;
  line-height: 1.8;
  color: var(--sub);
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  white-space: pre-wrap;
}
</style>
</head>
<body>

<aside id="sidebar">
  <div id="sidebar-header">
    <div class="logo">
      <span class="logo-mark">声库</span>
      <span class="logo-sub">Collection</span>
    </div>
    <div class="search-wrap">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input id="search" placeholder="タイトル · CV · RJ番号" oninput="filter()">
    </div>
  </div>

  <div id="sidebar-body">
    <div class="filter-section">
      <div class="filter-heading">分级</div>
      <div class="filter-pills" id="age-filters"></div>
    </div>
    <div class="filter-section">
      <div class="filter-heading">声优</div>
      <div class="filter-pills" id="cv-filters"></div>
    </div>
    <div class="filter-section">
      <div class="filter-heading">标签</div>
      <div class="filter-pills" id="tag-filters"></div>
    </div>
  </div>
</aside>

<div id="main">
  <div id="topbar">
    <div id="stats"></div>
    <div id="sort-btns">
      <button class="sort-btn on" onclick="setSort('release_date',this)">发售日</button>
      <button class="sort-btn" onclick="setSort('added_at',this)">入库日</button>
      <button class="sort-btn" onclick="setSort('title',this)">标题</button>
    </div>
    <button id="blur-toggle" class="on" onclick="toggleBlur()">
      <span class="blur-dot"></span>
      R18 遮蔽
    </button>
  </div>
  <div id="grid-wrap">
    <div id="grid"></div>
    <div id="empty" style="display:none">没有找到符合条件的作品</div>
  </div>
</div>

<div id="modal-bg" onclick="closeModal(event)">
  <div id="modal">
    <button id="modal-close" onclick="closeModal()">✕</button>
    <div id="modal-content"></div>
  </div>
</div>

<script>
let ALL = [];
let activeCVs  = new Set();
let activeTags = new Set();
let activeAges = new Set();
let blurOn   = true;
let sortKey  = 'release_date';

function setSort(key, btn) {
  sortKey = key;
  document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  filter();
}

function sortWorks(works) {
  return [...works].sort((a, b) => {
    if (sortKey === 'title') return (a.title||'').localeCompare(b.title||'', 'ja');
    const va = a[sortKey] || '';
    const vb = b[sortKey] || '';
    if (!va && !vb) return 0;
    if (!va) return 1;
    if (!vb) return -1;
    return vb.localeCompare(va);   // DESC
  });
}

async function init() {
  const [works, cvs, tags] = await Promise.all([
    fetch('/api/works').then(r => r.json()),
    fetch('/api/cvs').then(r => r.json()),
    fetch('/api/tags').then(r => r.json()),
  ]);
  ALL = works;
  buildAgeFilters();
  buildCVFilters(cvs);
  buildTagFilters(tags);
  render(ALL);
}

function buildAgeFilters() {
  const ages = [...new Set(ALL.map(w => w.age_rating).filter(Boolean))];
  document.getElementById('age-filters').innerHTML = ages.map(a =>
    `<button class="pill age-pill-${a}" onclick="toggleAge('${a}',this)">${a}</button>`
  ).join('');
}
function buildCVFilters(cvs) {
  document.getElementById('cv-filters').innerHTML = cvs.map(c =>
    `<button class="pill" onclick="toggleCV('${esc(c.name_jp)}',this)">${esc(c.name_jp)}</button>`
  ).join('');
}
function buildTagFilters(tags) {
  document.getElementById('tag-filters').innerHTML = tags.map(t =>
    `<button class="pill" onclick="toggleTag('${esc(t.name_jp)}',this)">${esc(TAG_JP2CN[t.name_jp]||t.name_jp)}</button>`
  ).join('');
}

function toggleAge(v, b) { toggle(activeAges, v, b); filter(); }
function toggleCV(v, b)  { toggle(activeCVs,  v, b); filter(); }
function toggleTag(v, b) { toggle(activeTags, v, b); filter(); }
function toggle(set, v, btn) {
  set.has(v) ? set.delete(v) : set.add(v);
  btn.classList.toggle('on');
}

function filter() {
  const q = document.getElementById('search').value.toLowerCase();
  const res = ALL.filter(w => {
    if (q && !w.title?.toLowerCase().includes(q)
          && !w.rj_id?.toLowerCase().includes(q)
          && !(w.cvs||[]).some(c => c.toLowerCase().includes(q))) return false;
    if (activeCVs.size  && !(w.cvs||[]).some(c => activeCVs.has(c)))   return false;
    if (activeTags.size && !(w.tags||[]).some(t => activeTags.has(t)))  return false;
    if (activeAges.size && !activeAges.has(w.age_rating))               return false;
    return true;
  });
  render(res);
}

function ageClass(r) {
  if (r === 'R18') return 'age-R18';
  if (r === 'R-15') return 'age-R-15';
  return 'age-全年齢';
}

function render(works) {
  const grid  = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const stats = document.getElementById('stats');
  stats.innerHTML = `<b>${works.length}</b> / ${ALL.length} 作品`;
  works = sortWorks(works);
  if (!works.length) { grid.innerHTML = ''; empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  grid.innerHTML = works.map(w => `
    <div class="card" onclick="showDetail('${w.rj_id}')">
      <div class="card-img-wrap">
        <img src="${w.cover_path ? '/cover/'+encodeURIComponent(w.rj_id) : ''}"
             data-age="${w.age_rating||''}"
             onerror="this.parentElement.style.display='none'" loading="lazy">
        ${w.age_rating ? `<span class="card-age ${ageClass(w.age_rating)}">${w.age_rating}</span>` : ''}
      </div>
      <div class="card-body">
        <div class="card-rj">${w.rj_id}</div>
        <div class="card-title">${esc(w.title)}</div>
        <div class="card-cv">${(w.cvs||[]).map(esc).join(' · ') || '—'}</div>
        ${w.release_date ? `<div class="card-date">${w.release_date}</div>` : ''}
      </div>
    </div>
  `).join('');
  setTimeout(() => document.querySelectorAll('img[data-age]').forEach(applyBlur), 0);
}

function toggleBlur() {
  blurOn = !blurOn;
  const btn = document.getElementById('blur-toggle');
  btn.classList.toggle('on', blurOn);
  btn.lastChild.textContent = blurOn ? ' R18 遮蔽' : ' R18 显示';
  document.querySelectorAll('img[data-age]').forEach(applyBlur);
}
function applyBlur(img) {
  img.classList.toggle('blurred', blurOn && img.dataset.age === 'R18');
}

async function showDetail(rj_id) {
  const w = await fetch('/api/work/' + rj_id).then(r => r.json());
  const ageCls = ageClass(w.age_rating);
  document.getElementById('modal-content').innerHTML = `
    <div class="modal-cover">
      <img src="${w.cover_path ? '/cover/'+encodeURIComponent(rj_id) : ''}"
           onerror="this.parentElement.style.display='none'">
    </div>
    <div class="modal-body">
      <div class="modal-rj">${w.rj_id}</div>
      <div class="modal-title">${esc(w.title)}</div>
      <div class="modal-info">
        <span class="modal-info-label">社团</span>
        <span class="modal-info-val">${esc(w.circle||'—')}</span>
        <span class="modal-info-label">声优</span>
        <span class="modal-info-val">${(w.cvs||[]).map(esc).join('　') || '—'}</span>
        ${w.release_date ? `<span class="modal-info-label">发售日</span>
        <span class="modal-info-val">${esc(w.release_date)}</span>` : ''}
        <span class="modal-info-label">分级</span>
        <span class="modal-info-val">
          <span class="modal-age-badge ${ageCls}">${w.age_rating||'—'}</span>
        </span>
      </div>
      ${(w.tags||[]).length ? `
      <div class="modal-tags">
        ${(w.tags||[]).map(tag => `<span class="modal-tag">${esc(TAG_JP2CN[tag]||tag)}</span>`).join('')}
      </div>` : ''}
      ${w.description ? `<div class="modal-desc">${esc(w.description)}</div>` : ''}
    </div>
  `;
  document.getElementById('modal-bg').classList.add('open');
}

function closeModal(e) {
  if (!e || e.target === document.getElementById('modal-bg') || e.currentTarget.id === 'modal-close')
    document.getElementById('modal-bg').classList.remove('open');
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

const TAG_JP2CN = {
  // 玩法 / 行为 (シチュエーション・行為)
  "バイノーラル/ダミヘ": "双耳/假人头", "ダミーヘッド": "假人头麦克风",
  "耳舐め": "舔耳", "耳かき": "掏耳", "囁き": "耳语", "ささやき": "耳语",
  "吐息": "呼吸声", "ASMR": "ASMR", "環境音": "环境音", "睡眠導入": "助眠",
  "キス": "接吻", "口内射精": "口内射精", "フェラチオ": "口交",
  "クンニ": "口交(女)", "手コキ": "手交", "パイズリ": "乳交",
  "イマラチオ": "强制口交", "イラマチオ": "强制口交", "アナル": "肛交", 
  "sissy": "伪娘", "オナニー": "自慰", "オナニー指示": "自慰指示", 
  "乳首責め": "乳头责", "痴女": "痴女", "逆レイプ": "逆强制", "レイプ": "强制",
  "催眠": "催眠", "洗脳": "洗脑", "阻薬": "春药", "トランス/暗示": "出神/暗示",
  "调教": "调教", "拘束": "束缚", "SM": "SM", "支配": "支配",
  "言語責め": "言语责", "言語侵犯": "言语侵犯", "言葉責め": "言语责", "罵倒": "辱骂",
  "低音ボイス": "低音", "高音ボイス": "高音", "ロリ系ボイス": "萝莉音", "ボイス": "语音",
  "フェチ": "恋物/癖好", "複数プレイ/乱交": "多人群交/乱交", "女性優位": "女性主导",
  "焦らし": "挑逗/憋精", "男性受け": "男性受(常指逆推/被动)",

  // 剧情 / 氛围 (ストーリー・属性)
  "純愛": "纯爱", "ラブラブ/あまあま": "甜蜜", "甘々": "甜蜜",
  "NTR": "NTR", "寝取り": "寝取", "寝取られ": "被寝取",
  "ハーレム": "后宫", "逆ハーレム": "逆后宫",
  "学園もの": "校园", "学校/学園": "学校/校园", "オフィス": "职场", 
  "異世界": "异世界", "ファンタジー": "奇幻", "現代": "现代", 
  "和風": "日风", "着物/和服": "和服", "日常/生活": "日常/生活",
  "ほのぼの": "温馨/轻松", "退廃/背徳/インモラル": "颓废/背德/不伦",
  "萌え": "萌系/有爱", "シリーズもの": "系列作", "健全": "健全/全年龄",

  // 角色 / 身份 (キャラクター)
  "お姉さん": "大姐姐", "妹": "妹妹", "義妹": "义妹(继妹)", "幼馴染": "青梅竹马", "幼なじみ": "青梅竹马",
  "彼女": "女友", "彼氏": "男友", "恋人同士": "恋人/情侣", "嫁": "老婆", "旦那": "老公",
  "メイド": "女仆", "先生": "老师", "生徒": "学生", "学生": "学生",
  "後輩": "后辈", "先輩": "前辈", "先輩/後輩": "前辈/后辈", "上司": "上司", "部下": "下属",
  "ツンデレ": "傲娇", "ヤンデレ": "病娇", "触ナー": "丧系",
  "クール": "冷淡", "天然": "天然呆", "強気": "强势", "クール攻め": "高冷攻",
  "年上": "年上", "年下": "年下", "年下攻め": "年下攻",
  "人外": "非人类", "人外娘/モンスター娘": "人外娘/魔物娘", "獣耳": "兽耳", "エルフ": "精灵",
  "サキュバス": "魅魔", "幽霊": "幽灵", "吸血鬼": "吸血鬼", "お嬢様": "大小姐",
  "ギャル": "辣妹", "VTuber": "VTuber/虚拟主播", "少女": "少女", "ボクっ娘": "仆娘(自称bokku的假小子)",
  "百合": "百合", "OL": "OL/职场女性",

  // 体型 / 外貌 (体型・外見)
  "巨乳": "巨乳", "爆乳": "爆乳", "巨乳/爆乳": "巨乳/爆乳",
  "貧乳": "贫乳", "つるぺた": "贫乳/搓衣板", "ロリ": "萝莉", "ショタ": "正太",

  // 内容分类 / 状态 (シチュエーション・状態)
  "癒し": "治愈", "睡眠": "睡眠", "添い寝": "同床", "同床": "同床",
  "おやすみ": "晚安", "起こし": "叫醒", "朝起こし": "早安叫醒", "耳ふー": "向耳吹气",
  "イチャイチャ": "腻歪", "えっち": "H", "工作サポ": "自慰辅助", "自慰辅助": "自慰辅助",
  "中出し": "内射", "内射": "内射", "顔射": "颜射", "大量射精": "大量射精",
  "ごっくん/食ザー": "吞精",
  "妊娠/孕ませ": "妊娠/孕", "赤ちゃんプレイ": "婴儿扮演",
  "おっぱい": "胸部", "胸部": "胸部", "おしり": "臀部", "ふともも": "大腿",
  "コスプレ": "角色扮演", "制服": "制服", "水着": "泳装", "脱衣": "脱衣",
  "淡白/あっさり": "淡泊/简单(指流程不繁琐)","トランス/暗示ボイス": "出神/暗示催眠语音",
  "工作サポ": "自慰辅助", 
  "オナサポ": "自慰辅助", 

  // 音声特性 (音声の技術的特徴)
  "立体音響": "立体音效", "高音質": "高音质", "BGMなし": "无BGM",
  "テキスト付き": "附文本", "日本語": "日语", "中国語": "中文"
};

function t(jp) {
  return TAG_JP2CN[jp] || jp;
}

init();
</script>
</body>
</html>
"""

# ── API ───────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/works")
def api_works():
    conn = get_conn()
    rows = conn.execute("SELECT rj_id, title, circle, cover_path, age_rating, release_date FROM works ORDER BY added_at DESC").fetchall()
    result = []
    for w in rows:
        cvs = [r["name_jp"] for r in conn.execute(
            "SELECT c.name_jp FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id WHERE wc.rj_id=?",
            (w["rj_id"],)
        ).fetchall()]
        tags = [r["name_jp"] for r in conn.execute(
            "SELECT t.name_jp FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id WHERE wt.rj_id=?",
            (w["rj_id"],)
        ).fetchall()]
        result.append(dict(w) | {"cvs": cvs, "tags": tags})
    conn.close()
    return jsonify(result)

@app.route("/api/work/<rj_id>")
def api_work(rj_id):
    conn = get_conn()
    w = conn.execute("SELECT * FROM works WHERE rj_id=?", (rj_id,)).fetchone()
    if not w:
        return jsonify({"error": "not found"}), 404
    cvs = [r["name_jp"] for r in conn.execute(
        "SELECT c.name_jp FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id WHERE wc.rj_id=?",
        (rj_id,)
    ).fetchall()]
    tags = [r["name_jp"] for r in conn.execute(
        "SELECT t.name_jp FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id WHERE wt.rj_id=?",
        (rj_id,)
    ).fetchall()]
    conn.close()
    return jsonify(dict(w) | {"cvs": cvs, "tags": tags})

@app.route("/api/cvs")
def api_cvs():
    conn = get_conn()
    rows = conn.execute(
        "SELECT c.cv_id, c.name_jp, COUNT(wc.rj_id) as cnt "
        "FROM cvs c JOIN work_cvs wc ON c.cv_id=wc.cv_id "
        "GROUP BY c.cv_id ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/tags")
def api_tags():
    conn = get_conn()
    rows = conn.execute(
        "SELECT t.tag_id, t.name_jp, COUNT(wt.rj_id) as cnt "
        "FROM tags t JOIN work_tags wt ON t.tag_id=wt.tag_id "
        "GROUP BY t.tag_id ORDER BY cnt DESC LIMIT 60"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/cover/<rj_id>")
def serve_cover(rj_id):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = _HERE / "covers" / f"{rj_id}.{ext}"
        if p.exists():
            return send_from_directory(p.parent, p.name)
    return "", 404

if __name__ == "__main__":
    import os
    # Render 会自动注入 PORT 环境变量，本地没有时默认 5000 方便你调试
    port = int(os.environ.get("PORT", 5000))
    # 必须指定 host="0.0.0.0" 才能让外网（你的手机/浏览器）访问
    # 在云端建议关闭 debug=True
    app.run(host="0.0.0.0", port=port, debug=False)